from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from shop.models import Good
from users.models import UserCredenetials, User
from cart.services import Cart
from cart.services.bonus import apply_bonus, parse_bonus
from .models import Order, OrderItem

def _build_cart_context(
    cart,
    error=None,
    address="",
    bonus_available=None,
    bonus_to_use=None,
    bonus_used=None,
    bonus_earned=None,
    total_after=None,
):
    context = {
        "cart": cart,
        "cart_total": cart.get_total_price(),
        "error": error,
        "address": address,
    }
    if bonus_available is not None:
        context["bonus_available"] = bonus_available
    if bonus_to_use is not None:
        context["bonus_to_use"] = bonus_to_use
    if bonus_used is not None:
        context["bonus_used"] = bonus_used
    if bonus_earned is not None:
        context["bonus_earned"] = bonus_earned
    if total_after is not None:
        context["total_after"] = total_after
    return context


def _missing_profile_fields(user):
    missing = []
    if not user.email:
        missing.append("email")
    phone = None
    try:
        phone = user.usercredenetials.phonenumber
    except UserCredenetials.DoesNotExist:
        phone = None
    if not phone:
        missing.append("phone number")
    return missing


def cart_summarry(request):
    cart = Cart(request)
    bonus_available = Decimal("0.00")
    if request.user.is_authenticated:
        bonus_available = request.user.bonus or Decimal("0.00")
    bonus_used, bonus_earned, total_after = apply_bonus(
        bonus_available,
        cart.get_total_price(),
        Decimal("0.00"),
    )
    context = _build_cart_context(
        cart,
        bonus_available=bonus_available,
        bonus_to_use=Decimal("0.00"),
        bonus_used=bonus_used,
        bonus_earned=bonus_earned,
        total_after=total_after,
    )
    return render(request, "cart/cart_summary.html", context)

@transaction.atomic
@require_POST
def cart_add(request, pk):
    cart = Cart(request)
    good = get_object_or_404(Good, id=pk)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(quantity, 1)
    if good.amount > 0:
        quantity = min(quantity, good.amount)
    cart.add(
        good=good,
        amount=quantity,
        override_quantity=False,
    )
    return redirect("cart_summarry")

@transaction.atomic
@require_POST
def cart_delete(request, pk):
    cart = Cart(request)
    good = get_object_or_404(Good, id=pk)
    cart.remove(good)
    return redirect("cart_summarry")

@transaction.atomic
@require_POST
def cart_update(request, pk):
    cart = Cart(request)
    good = get_object_or_404(Good, id=pk)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(quantity, 1)
    if good.amount > 0:
        quantity = min(quantity, good.amount)
    cart.add(
        good=good,
        amount=quantity,
        override_quantity=True,
    )
    return redirect("cart_summarry")

@transaction.atomic
@login_required
@require_POST
def cart_checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        context = _build_cart_context(cart, error="Cart is empty.")
        return render(request, "cart/cart_summary.html", context)

    address = (request.POST.get("address") or "").strip()
    bonus_request = parse_bonus(request.POST.get("bonus_to_use", "0"))
    if not address:
        bonus_available = request.user.bonus or Decimal("0.00")
        bonus_used, bonus_earned, total_after = apply_bonus(
            bonus_available,
            cart.get_total_price(),
            bonus_request,
        )
        context = _build_cart_context(
            cart,
            error="Please enter an address.",
            address=address,
            bonus_available=bonus_available,
            bonus_to_use=bonus_request,
            bonus_used=bonus_used,
            bonus_earned=bonus_earned,
            total_after=total_after,
        )
        return render(request, "cart/cart_summary.html", context)

    missing_fields = _missing_profile_fields(request.user)
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        bonus_available = request.user.bonus or Decimal("0.00")
        bonus_used, bonus_earned, total_after = apply_bonus(
            bonus_available,
            cart.get_total_price(),
            bonus_request,
        )
        context = _build_cart_context(
            cart,
            error=f"Please complete your profile with: {missing_text}.",
            address=address,
            bonus_available=bonus_available,
            bonus_to_use=bonus_request,
            bonus_used=bonus_used,
            bonus_earned=bonus_earned,
            total_after=total_after,
        )
        return render(request, "cart/cart_summary.html", context)

    items = list(cart)
    total_value = cart.get_total_price()
    good_ids = [item["good"].id for item in items]
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)
        bonus_used, bonus_earned, total_after = apply_bonus(
            user.bonus or Decimal("0.00"),
            total_value,
            bonus_request,
        )
        goods = {g.id: g for g in Good.objects.select_for_update().filter(id__in=good_ids)}
        for item in items:
            good = goods.get(item["good"].id)
            if not good or good.amount < item["amount"]:
                context = _build_cart_context(
                    cart,
                    error="Not enough stock for one or more items.",
                    address=address,
                    bonus_available=user.bonus or Decimal("0.00"),
                    bonus_to_use=bonus_request,
                    bonus_used=bonus_used,
                    bonus_earned=bonus_earned,
                    total_after=total_after,
                )
                return render(request, "cart/cart_summary.html", context)

        order = Order.objects.create(user=request.user, address=address)
        for item in items:
            good = goods[item["good"].id]
            OrderItem.objects.create(
                order=order,
                good=good,
                user=request.user,
                amount=item["amount"],
                price_at_purchase=float(item["price_at_purchase"]),
            )
            good.amount = good.amount - item["amount"]
            good.save(update_fields=["amount"])
        user.bonus = (user.bonus or Decimal("0.00")) - bonus_used + bonus_earned
        user.save(update_fields=["bonus"])

    cart.clear()
    _send_order_confirmation(
        request.user,
        order,
        items,
        total_after,
        address,
        bonus_used=bonus_used,
        bonus_earned=bonus_earned,
    )
    return redirect("cart_summarry")



@transaction.atomic
def _send_order_confirmation(
    user,
    order,
    items,
    total,
    address,
    bonus_used=Decimal("0.00"),
    bonus_earned=Decimal("0.00"),
):
    if not user.email:
        return
    lines = [
        f"Thank you for your purchase, {user.username}!",
        f"Order #{order.id} summary:",
        "",
    ]
    for item in items:
        lines.append(
            f"- {item['good'].name} x{item['amount']} - ${item['total_price']:.2f}"
        )
    lines.extend(
        [
            "",
            f"Bonus used: ${bonus_used:.2f}",
            f"Bonus earned: ${bonus_earned:.2f}",
            f"Total charged: ${total:.2f}",
            f"Shipping address: {address}",
            "",
            "If you have questions, reply to this message.",
        ]
    )
    send_mail(
        f"ShopBoom order #{order.id}",
        "\n".join(lines),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
