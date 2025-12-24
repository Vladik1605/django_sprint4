from django.urls import path
from django.views.generic import TemplateView

app_name = 'pages'

urlpatterns = [
    path(
        'about/',
        TemplateView.as_view(
            template_name='pages/about.html',
            extra_context={'title': 'О проекте'},
        ),
        name='about',
    ),
    path(
        'rules/',
        TemplateView.as_view(
            template_name='pages/rules.html',
            extra_context={'title': 'Наши правила'},
        ),
        name='rules',
    ),
]
