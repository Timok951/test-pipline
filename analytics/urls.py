from django.urls import path
from .views import (
    admin_report_pdf,
    analytics_reports,
    requirements_status,
    admin_backup,
    GoodsChartData,
    OrdersChartData,
)

urlpatterns = [
    path("report/pdf/", admin_report_pdf, name="admin_report_pdf"),
    path("reports/", analytics_reports, name="analytics_reports"),
    path("requirements/", requirements_status, name="analytics_requirements"),
    path("backup/", admin_backup, name="admin_backup"),
    path("charts/goods/", GoodsChartData.as_view(), name="analytics_goods_chart"),
    path("charts/orders/", OrdersChartData.as_view(), name="analytics_orders_chart"),
]
