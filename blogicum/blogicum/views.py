from django.shortcuts import render


def csrf_failure(request, exception=None):
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    return render(request, 'pages/500.html', status=500)
