import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Group, Plan, Vote

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

def active_plans(request):
    return render(
        request,
        "pages/active_plans.html",
        {
            "meta_title": "Active Plans",
            "active_page": "active_plans",
            "topbar_context": "Active Plans",
        },
    )

def archive(request):
    return render(
        request,
        "pages/archive.html",
        {
            "meta_title": "Archive",
            "active_page": "archive",
            "topbar_context": "Archive",
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
    if request.method == "POST":
        group_id = request.POST.get("group_id")
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        price = request.POST.get("price", 0)
        
        if not group_id:
            user_groups = Group.objects.all()
            return render(
                request,
                "pages/start_new_plan.html",
                {
                    "meta_title": "Start New Plan",
                    "active_page": "start_new_plan",
                    "topbar_context": "Start New Plan",
                    "groups": user_groups,
                    "error": "Per favor, selecciona un grup per proposar el pla.",
                },
            )
            
        group = get_object_or_404(Group, id=group_id)
        
        Plan.objects.create(
            group=group,
            title=title,
            description=description,
            price=price or 0,
            status=Plan.Status.VOTING,
        )
        return redirect("active_plans")
        
    user_groups = Group.objects.all()
    
    # Auto-seed if empty for the user to test
    if not user_groups.exists():
        Group.objects.create(name="The Foodies Collective", description="Culinary adventures")
        Group.objects.create(name="Adventure Seekers", description="Outdoor stuff")
        user_groups = Group.objects.all()
    
    return render(
        request,
        "pages/start_new_plan.html",
        {
            "meta_title": "Start New Plan",
            "active_page": "start_new_plan",
            "topbar_context": "Start New Plan",
            "groups": user_groups,
        },
    )

def vote(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Plans currently in voting stage
    active_plans = Plan.objects.filter(group=group, status=Plan.Status.VOTING)
    
    return render(
        request,
        "pages/vote.html",
        {
            "meta_title": "Vote",
            "active_page": "active_plans",
            "topbar_context": f"Voting - {group.name}",
            "group": group,
            "plans": active_plans,
        }
    )

@csrf_exempt
def api_submit_vote(request, plan_id):
    if request.method == "POST":
        plan = get_object_or_404(Plan, id=plan_id)
        try:
            data = json.loads(request.body)
            value = data.get("value", 1)
            
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
                
            Vote.objects.create(
                plan=plan,
                value=value,
                session_key=session_key
            )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "method_not_allowed"}, status=405)
