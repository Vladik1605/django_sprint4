from django.shortcuts import render


def about(request):
    template = 'pages/about.html'
    context = {'title': 'О проекте'}
    return render(request, template, context=context)


def rules(request):
    template = 'pages/rules.html'
    context = {'title': 'Наши правила'}
    return render(request, template, context=context)


def page_not_found(request, exception=None):
    template = 'pages/404.html'
    context = {}
    return render(request, template, context=context, status=404)


def csrf_failure(request, reason=''):
    template = 'pages/403csrf.html'
    context = {}
    return render(request, template, context=context, status=403)


def server_error(request):
    template = 'pages/500.html'
    context = {}
    return render(request, template, context=context, status=500)
