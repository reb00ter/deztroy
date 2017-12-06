from django.test import TestCase

# Create your tests here.
from u24.models import Phone


class TestPhone(TestCase):
    def test_variants(self):
        phone = Phone(num="9129468128")
        phone.save()
        self.assertEqual(phone.get_variant(0), "+79129468128")
        self.assertEqual(phone.get_variant(1), "89129468128")
        self.assertEqual(phone.get_variant(2), "+791294-68-128")
        self.assertEqual(phone.get_variant(3), "891294-68-128")
        self.assertEqual(phone.get_variant(4), "+7(912)94-68-128")
        self.assertEqual(phone.get_variant(5), "8(912)94-68-128")
