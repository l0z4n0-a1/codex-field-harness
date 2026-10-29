import unittest
from decimal import Decimal
from discount import discounted

class DiscountTests(unittest.TestCase):
    def test_boundary(self):
        self.assertEqual(discounted(Decimal('99.99')), Decimal('99.99'))
        self.assertEqual(discounted(Decimal('100')), Decimal('90.00'))
        self.assertEqual(discounted(Decimal('100.01')), Decimal('90.009'))
    def test_decimal_contract(self):
        with self.assertRaises(TypeError): discounted(100.0)

if __name__ == '__main__': unittest.main()
