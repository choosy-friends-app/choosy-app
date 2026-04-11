from django.shortcuts import render


def dashboard(request):
    return render(
        request,
        "pages/dashboard.html",
        {
            "meta_title": "Dashboard",
            "active_page": "dashboard",
        },
    )


def groups(request):
    return render(
        request,
        "pages/groups.html",
        {
            "meta_title": "Groups",
            "active_page": "groups",
        },
    )
