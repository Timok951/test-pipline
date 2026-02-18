import json
from decimal import Decimal
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import F
from cart.models import Order, OrderItem
from cart.services.bonus import apply_bonus, parse_bonus
from users.models import UserCredenetials, User
from shop.models import Good

ROLE_ALLOW_LIST = {"warehouse", "admin"}


def _manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        has_role = (
            user.is_authenticated
            and (
                user.is_staff
                or user.is_superuser
                or (user.role and user.role.rolename.lower() in ROLE_ALLOW_LIST)
            )
        )
        if not has_role:
            return JsonResponse({"error": "Requires warehouse or admin role"}, status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped


def _serialize_good(good):
    return {
        "id": good.id,
        "name": good.name,
        "amount": good.amount,
        "cost": str(good.cost),
        "type": good.type.name if good.type else None,
        "company": good.company.name if good.company else None,
    }


@require_http_methods(["GET", "POST"])
@csrf_exempt
def goods_api(request):
    if request.method == "GET":
        goods = [ _serialize_good(g) for g in Good.objects.all() ]
        return JsonResponse({"goods": goods})

    payload = {}
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    user = request.user
    has_role = (
        user.is_staff
        or user.is_superuser
        or (user.role and user.role.rolename.lower() in ROLE_ALLOW_LIST)
    )
    if not has_role:
        return JsonResponse({"error": "Requires warehouse or admin role"}, status=403)

    name = payload.get("name")
    amount = payload.get("amount", 0)
    cost = payload.get("cost", 0)
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    good = Good.objects.create(
        name=name,
        amount=int(amount),
        cost=float(cost),
    )
    return JsonResponse({"good": _serialize_good(good)}, status=201)


@require_http_methods(["GET", "PUT", "DELETE"])
@csrf_exempt
def good_detail_api(request, pk):
    good = get_object_or_404(Good, id=pk)
    if request.method == "GET":
        return JsonResponse(_serialize_good(good))

    if request.method == "DELETE":
        return _delete_good(request, good)
    if request.method == "PUT":
        return _update_good(request, good)


def _update_good(request, good):
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    if not (request.user.is_staff or request.user.is_superuser or (request.user.role and request.user.role.rolename.lower() in ROLE_ALLOW_LIST)):
        return JsonResponse({"error": "Requires warehouse or admin role"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    for field in ("name", "amount", "cost"):
        if field in payload:
            setattr(
                good,
                field,
                payload[field] if field != "amount" else int(payload[field]),
            )
    good.save()
    return JsonResponse({"good": _serialize_good(good)})


def _delete_good(request, good):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    if not (request.user.is_staff or request.user.is_superuser or (request.user.role and request.user.role.rolename.lower() in ROLE_ALLOW_LIST)):
        return JsonResponse({"error": "Requires warehouse or admin role"}, status=403)
    good.delete()
    return JsonResponse({"status": "deleted"})


@login_required
@require_http_methods(["GET"])
def orders_api(request):
    orders = Order.objects.filter(user=request.user)
    payload = []
    for order in orders:
        items = [
            {
                "good": item.good.name,
                "amount": item.amount,
                "price": item.price_at_purchase,
            }
            for item in order.fk_order.all()
        ]
        payload.append({"order_id": order.id, "date": str(order.date), "items": items})
    return JsonResponse({"orders": payload})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def orders_checkout_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    items = payload.get("items", [])
    address = payload.get("address", "").strip()
    if not items or not address:
        return JsonResponse({"error": "Items and address are required"}, status=400)

    missing_fields = []
    if not request.user.email:
        missing_fields.append("email")
    phone = None
    try:
        phone = request.user.usercredenetials.phonenumber
    except UserCredenetials.DoesNotExist:
        phone = None
    if not phone:
        missing_fields.append("phone number")
    if missing_fields:
        return JsonResponse(
            {"error": f"Complete your profile with: {', '.join(missing_fields)}"},
            status=400,
        )

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)
        goods_map = {
            good.id: good
            for good in Good.objects.select_for_update().filter(
                id__in=[item["good_id"] for item in items]
            )
        }
        total_value = Decimal("0.00")
        prepared_items = []
        for item in items:
            good = goods_map.get(item["good_id"])
            if not good:
                transaction.set_rollback(True)
                return JsonResponse({"error": f"Product {item['good_id']} not found"}, status=404)
            requested = int(item.get("amount", 1))
            if requested < 1 or requested > good.amount:
                transaction.set_rollback(True)
                return JsonResponse({"error": f"Invalid quantity for {good.name}"}, status=400)
            total_value += Decimal(str(good.cost)) * requested
            prepared_items.append((good, requested))
        bonus_request = parse_bonus(payload.get("bonus_to_use", "0"))
        bonus_used, bonus_earned, total_after = apply_bonus(
            user.bonus or Decimal("0.00"),
            total_value,
            bonus_request,
        )
        order = Order.objects.create(user=request.user, address=address)
        for good, requested in prepared_items:
            OrderItem.objects.create(
                order=order,
                good=good,
                user=request.user,
                amount=requested,
                price_at_purchase=float(good.cost),
            )
            good.amount -= requested
            good.save(update_fields=["amount"])
        user.bonus = (user.bonus or Decimal("0.00")) - bonus_used + bonus_earned
        user.save(update_fields=["bonus"])
        return JsonResponse(
            {
                "order_id": order.id,
                "status": "created",
                "bonus_used": float(bonus_used),
                "bonus_earned": float(bonus_earned),
                "total_charged": float(total_after),
            },
            status=201,
        )
