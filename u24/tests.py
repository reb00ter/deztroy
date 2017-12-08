import json

from django.test import TestCase

# Create your tests here.
from django.urls import reverse

from u24.models import Phone, Category, SubCategory


def init_categories():
    services = Category(u24id=7, title="Услуги")
    services.save()
    vacancies = Category(u24id=2, title="Вакансии")
    vacancies.save()
    fixing = SubCategory(category=services, title="Ремонт", u24id=55)
    fixing.save()
    building = SubCategory(category=services, title="Строительство", u24id=100)
    building.save()
    trade = SubCategory(category=vacancies, title="Торговля", u24id=67)
    trade.save()
    it = SubCategory(category=vacancies, title="ИТ", u24id=77)
    it.save()


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


class TestCategoriesJSON(TestCase):
    def test_get_categories(self):
        init_categories()
        response = self.client.get(reverse('categories_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(len(response.json()[0]['items'][0]), 2)
        self.assertEqual(len(response.json()[0]['items'][1]), 2)
