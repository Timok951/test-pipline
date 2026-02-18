import csv
import io
import zipfile

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.models import F, FloatField, Sum
from django.http import HttpResponse
from django.shortcuts import render
from cart.models import OrderItem
from shop.models import Good
from .models import UserOrders, GoodIncome, DangerousGoods, OrderReport
from users.decorators import role_required
from chartjs.views.base import JSONView
from django.db import connection


MATERIALIZED_VIEWS = [
    "good_icome",
    "user_orders",
    "dangerous_goods",
    "orders_report",
]


def refresh_materialized_views():
    with connection.cursor() as cursor:
        for view in MATERIALIZED_VIEWS:
            cursor.execute(f"REFRESH MATERIALIZED VIEW {view};")
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    letter = None
    canvas = None
    REPORTLAB_AVAILABLE = False

APP_LABELS = {"shop", "cart", "users", "analytics", "articles"}
MAX_ROWS_PER_TABLE = 20


@role_required("admin")
def admin_report_pdf(request):
    if not REPORTLAB_AVAILABLE:
        return HttpResponse(
            "reportlab is missing; install via `pip install reportlab` to generate PDF.",
            content_type="text/plain",
        )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=report.pdf"

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 40

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Database Report")
    y -= 30

    pdf.setFont("Helvetica", 10)

    models = [
        model for model in apps.get_models()
        if model._meta.app_label in APP_LABELS
    ]

    for model in models:
        table_name = model._meta.db_table
        fields = [field.name for field in model._meta.fields]
        rows = model.objects.all()[:MAX_ROWS_PER_TABLE]

        if y < 80:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, f"Table: {table_name}")
        y -= 16

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, "Fields: " + ", ".join(fields))
        y -= 14

        for row in rows:
            if y < 60:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 9)
            values = [str(getattr(row, f, "")) for f in fields]
            line = " | ".join(values)
            pdf.drawString(40, y, line[:120])
            y -= 12

        y -= 10

    pdf.showPage()
    pdf.save()
    return response


def _fetch_view_data(model):
    fields = list(model._meta.fields)
    columns = [field.db_column or field.name for field in fields]
    rows = []
    for obj in model.objects.all()[:MAX_ROWS_PER_TABLE]:
        row = [getattr(obj, field.name) for field in fields]
        rows.append(row)
    return columns, rows


@role_required("admin")
def analytics_reports(request):
    refresh_materialized_views()  
    view_names = [
        (UserOrders, "User orders"),
        (GoodIncome, "Goods income"),
        (DangerousGoods, "Dangerous goods"),
        (OrderReport, "Orders report"),
    ]
    
    data = []
    for model, label in view_names:
        try:
            columns, rows = _fetch_view_data(model)
        except Exception as exc:
            columns, rows = [], []
            data.append({"name": model._meta.db_table, "label": label, "columns": [], "rows": [], "error": str(exc)})
            continue
        data.append({"name": model._meta.db_table, "label": label, "columns": columns, "rows": rows, "error": ""})

    context = {"views": data}
    return render(request, "analytics/reports.html", context)


def _goods_summary():
    return list(
        Good.objects.values("type__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def _orders_summary():
    return list(
        OrderItem.objects.values("order__date")
        .annotate(
            revenue=Sum(
                F("amount") * F("price_at_purchase"),
                output_field=FloatField()
            )
        )
        .order_by("order__date")
    )


class GoodsChartData(JSONView):
    def get_labels(self):
        summary = _goods_summary()
        return [entry["type__name"] or "Uncategorized" for entry in summary]

    def get_context_data(self, **kwargs):
        summary = _goods_summary()
        labels = [entry["type__name"] or "Uncategorized" for entry in summary]
        data = [entry["total"] or 0 for entry in summary]
        colors = ["#00296b", "#00509d", "#fdc500", "#fdda5c", "#0b1b2b"]
        background = [colors[i % len(colors)] for i in range(len(data))]
        return {
            "labels": labels,
            "datasets": [{
                "label": "Stock",
                "data": data,
                "backgroundColor": background,
            }],
        }


class OrdersChartData(JSONView):
    def get_context_data(self, **kwargs):
        summary = _orders_summary()
        labels = [entry["order__date"].strftime("%Y-%m-%d") for entry in summary]
        data = [entry["revenue"] or 0 for entry in summary]
        return {
            "labels": labels,
            "datasets": [{
                "label": "Revenue",
                "data": data,
                "borderColor": "#fdc500",
                "backgroundColor": "rgba(253,197,0,0.2)",
                "fill": True,
            }],
        }


@role_required("admin")
def requirements_status(request):
    from users.models import Role

    role_labels = ["ADMIN", "WAREHOUSE", "CUSTOMER"]
    roles_ok = all(Role.objects.filter(rolename=name).exists() for name in role_labels)
    cart_setting = settings.CART_SESSION_ID if hasattr(settings, "CART_SESSION_ID") else "missing"
    pdf_ready = REPORTLAB_AVAILABLE
    requirements = [
        {"label": "Roles seeded", "status": roles_ok},
        {"label": "Session cart configured", "status": cart_setting != "missing"},
        {"label": "At least one product", "status": Good.objects.exists()},
        {"label": "PDF lib ready", "status": pdf_ready},
    ]
    return render(request, "analytics/requirements.html", {"requirements": requirements})


@role_required("admin")
def admin_backup(request):
    buffer = io.BytesIO()
    json_buffer = io.StringIO()
    call_command("dumpdata", stdout=json_buffer, exclude=["analytics"])
    payload = json_buffer.getvalue().encode("utf-8")
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("backup.json", payload)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=backup.zip"
    return response
