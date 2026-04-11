from django.shortcuts import render


def dashboard(request):
    return render(
        request,
        "pages/dashboard.html",
        {
            "meta_title": "Dashboard",
            "active_page": "dashboard",
            "topbar_context": "Dashboard",
        },
    )


def groups(request):
    return render(
        request,
        "pages/groups.html",
        {
            "meta_title": "Groups",
            "active_page": "groups",
            "topbar_context": "Groups",
        },
    )


def start_new_plan(request):
    return render(
        request,
        "pages/start_new_plan.html",
        {
            "meta_title": "Start New Plan",
            "active_page": "start_new_plan",
            "topbar_context": "Start New Plan",
        },
    )
