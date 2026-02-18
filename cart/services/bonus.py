from decimal import Decimal, InvalidOperation

BONUS_EARN_RATE = Decimal("0.05")
BONUS_QUANT = Decimal("0.01")


def parse_bonus(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")
    if amount < 0:
        return Decimal("0.00")
    return amount.quantize(BONUS_QUANT)


def apply_bonus(available, total, requested):
    available_value = Decimal(available or 0).quantize(BONUS_QUANT)
    total_value = Decimal(total or 0).quantize(BONUS_QUANT)
    requested_value = parse_bonus(requested)
    bonus_used = min(available_value, requested_value, total_value)
    total_after = (total_value - bonus_used).quantize(BONUS_QUANT)
    bonus_earned = (total_after * BONUS_EARN_RATE).quantize(BONUS_QUANT)
    return bonus_used, bonus_earned, total_after
