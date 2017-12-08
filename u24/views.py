from django.shortcuts import render

# Create your views here.
from django.views.generic import ListView, TemplateView

from deztroy.mixins import JSONResponseMixin
from u24.models import Category, SubCategory


class CategoriesJSON(JSONResponseMixin, TemplateView):
    def get_context_data(self, **kwargs):
        categories = Category.objects.all()
        categories_list = list()
        for category in categories:
            category_item = dict(id=category.id, title=category.title)
            category_item['items'] = list(category.subcategory_set.values('id', 'title'))
            categories_list.append(category_item)
        self.extra_context = dict(categories=categories_list)
        return super().get_context_data(**kwargs)

    def get_data(self, context):
        return context['categories']

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, safe=False)

