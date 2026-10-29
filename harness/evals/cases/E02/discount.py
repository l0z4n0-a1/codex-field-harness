from decimal import Decimal

def discounted(amount: Decimal) -> Decimal:
    if not isinstance(amount, Decimal):
        raise TypeError('Decimal required')
    return amount * (Decimal('0.90') if amount > Decimal('100') else Decimal('1'))
