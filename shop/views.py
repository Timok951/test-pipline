from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, transaction
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import QueryDict
from .models import Good, Type, Tag, Company, Rate
from users.models import User, UserFavorites
from users.decorators import role_required
from .forms import *
from django.http import HttpResponse
from shop.filters import GoodFilter


def _humanize_filter_label(key):
    return key.replace("_", " ").capitalize()


def _resolve_filter_value(key, value):
    if not value:
        return "Any"
    model_map = {
        "type": Type,
        "company": Company,
        "tag": Tag,
    }
    model = model_map.get(key)
    if model:
        try:
            return model.objects.get(id=value).name
        except model.DoesNotExist:
            return value
    return value

def home(request):
    users = User.objects.all()
    types = Type.objects.all()
    preference = getattr(request.user, "preference", None)
    saved_filters = preference.saved_filters if preference and preference.saved_filters else {}

    saved_filter_summary = [
        {"label": _humanize_filter_label(key), "value": _resolve_filter_value(key, value)}
        for key, value in saved_filters.items()
        if key != "csrfmiddlewaretoken" and value not in (None, "")
    ]

    filter_source = request.GET if request.GET else QueryDict(mutable=True)
    if not request.GET and saved_filters:
        query = QueryDict(mutable=True)
        for key, value in saved_filters.items():
            query[key] = value
        filter_source = query

    goodFilter = GoodFilter(filter_source, queryset=Good.objects.all().order_by("id"))
    page_size = preference.page_size if preference else 12
    paginator = Paginator(goodFilter.qs, page_size)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    if request.GET and preference:
        preference.saved_filters = request.GET.dict()
        preference.save(update_fields=["saved_filters"])

    context = {
        "GoodsPage": page_obj,
        "Users": users,
        "Types": types,
        "Form": goodFilter.form,
        "page_obj": page_obj,
        "saved_filter_summary": saved_filter_summary,
    }
    
    if request.GET.get("clear"):
        preference = getattr(request.user, "preference", None)
        if preference:
            preference.saved_filters = {}
            preference.save(update_fields=["saved_filters"])
        return redirect("home")
    
    return render(request, "main/home_page.html", context)
    


def good_page(request, pk):
    good = get_object_or_404(Good, id=pk)
    reviews = Rate.objects.filter(good=good, isdeleted=True).select_related("user")
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = UserFavorites.objects.filter(user=request.user, good=good).exists()
    context = {
        "Good": good,
        "reviews": reviews,
        "is_favorite": is_favorite,
        "review_form": ReviewForm(),
    }
    return render(request, 'good/good_page.html', context)


@require_POST
@role_required("customer", "admin", "warehouse")
def toggle_favorite(request, pk):
    good = get_object_or_404(Good, id=pk)
    favorite, created = UserFavorites.objects.get_or_create(user=request.user, good=good)
    if not created:
        favorite.delete()
    return redirect("good_page", pk=pk)


@require_POST
@role_required("customer", "admin", "warehouse")
def add_review(request, pk):
    good = get_object_or_404(Good, id=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.good = good
        review.user = request.user
        review.isdeleted = True
        review.save()
    return redirect("good_page", pk=pk)


def _execute_sql(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])


def _add_good_cost_sql(good_id):
    if connection.vendor == "postgresql":
        try:
            _execute_sql("CALL add_good_cost(%s)", [good_id])
            return
        except Exception:
            pass
    _execute_sql(
        "UPDATE shop_good SET cost = cost + cost * 0.10 WHERE id = %s",
        [good_id],
    )


def _add_good_stock_sql(good_id, good_add):
    if connection.vendor == "postgresql":
        try:
            _execute_sql("CALL add_good_stock(%s, %s)", [good_id, good_add])
            return
        except Exception:
            pass
    _execute_sql(
        "UPDATE shop_good SET amount = amount + %s WHERE id = %s",
        [good_add, good_id],
    )


def _delete_bad_goods_sql(rate):
    if connection.vendor == "postgresql":
        try:
            _execute_sql("CALL delete_bad_goods(%s)", [rate])
            return
        except Exception:
            pass
    _execute_sql(
        "DELETE FROM shop_good WHERE id IN (SELECT good_id FROM shop_rate WHERE rating = %s)",
        [rate],
    )


@role_required("warehouse", "admin")
def warehouse_dashboard(request):
    goods = Good.objects.all()
    context = {
        "Goods": goods,
    }
    return render(request, "warehouse/warehouse.html", context)


@role_required("warehouse", "admin")
@require_POST
def warehouse_add_cost(request):
    good_id = request.POST.get("good_id")
    if good_id:
        with transaction.atomic():
            _add_good_cost_sql(good_id)
    return redirect("warehouse_dashboard")


@role_required("warehouse", "admin")
@require_POST
def warehouse_add_stock(request):
    good_id = request.POST.get("good_id")
    try:
        good_add = int(request.POST.get("good_add", 0))
    except (TypeError, ValueError):
        good_add = 0
    if good_id and good_add != 0:
        with transaction.atomic():
            _add_good_stock_sql(good_id, good_add)
    return redirect("warehouse_dashboard")


@role_required("warehouse", "admin")
@require_POST
def warehouse_delete_bad_goods(request):
    try:
        rate = float(request.POST.get("rate", ""))
    except (TypeError, ValueError):
        rate = None
    if rate is not None:
        with transaction.atomic():
            _delete_bad_goods_sql(rate)
    return redirect("warehouse_dashboard")


@role_required("warehouse", "admin")
def warehouse_good_create(request):
    if request.method == "POST":
        form = GoodForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            form.save_m2m()
            return redirect("warehouse_dashboard")
    else:
        form = GoodForm()
    return render(request, "warehouse/good_form.html", {"form": form, "mode": "create"})


@role_required("warehouse", "admin")
def warehouse_good_edit(request, pk):
    good = get_object_or_404(Good, id=pk)
    if request.method == "POST":
        form = GoodForm(request.POST, request.FILES, instance=good)
        if form.is_valid():
            form.save()
            form.save_m2m()
            return redirect("warehouse_dashboard")
    else:
        form = GoodForm(instance=good)
    return render(request, "warehouse/good_form.html", {"form": form, "mode": "edit"})


@role_required("warehouse", "admin")
@require_POST
def warehouse_good_delete(request, pk):
    good = get_object_or_404(Good, id=pk)
    good.delete()
    return redirect("warehouse_dashboard")

