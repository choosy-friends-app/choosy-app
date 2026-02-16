from django.shortcuts import render


NAV_ITEMS = [
    {"id": "home", "label": "Home", "icon": "🏠", "url_name": "home"},
    {"id": "groups", "label": "Groups", "icon": "👥", "url_name": "groups"},
    {"id": "discover", "label": "Discover", "icon": "🧭", "url_name": "discover"},
    {"id": "profile", "label": "Profile", "icon": "👤", "url_name": "profile"},
]


def base_context(active_tab: str):
    return {"nav_items": NAV_ITEMS, "active_tab": active_tab}


def home(request):
    context = base_context("home")
    context.update(
        {
            "plans": [
                {
                    "id": 1,
                    "title": "Beach Day",
                    "description": "Surf, swim and chill at the coast",
                    "price": 25,
                    "duration": "4h",
                    "tag": "Outdoor",
                    "votes": 5,
                    "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=300&fit=crop",
                    "tag_class": "tag-outdoor",
                },
                {
                    "id": 2,
                    "title": "Rooftop Party",
                    "description": "Sunset vibes with great music",
                    "price": 40,
                    "duration": "6h",
                    "tag": "Party",
                    "votes": 8,
                    "image": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=400&h=300&fit=crop",
                    "tag_class": "tag-party",
                },
                {
                    "id": 3,
                    "title": "Movie Marathon",
                    "description": "Cozy night in with snacks",
                    "price": 15,
                    "duration": "5h",
                    "tag": "Chill",
                    "votes": 3,
                    "image": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=300&fit=crop",
                    "tag_class": "tag-chill",
                },
                {
                    "id": 4,
                    "title": "Street Food Tour",
                    "description": "Explore the best local bites",
                    "price": 30,
                    "duration": "3h",
                    "tag": "Food",
                    "votes": 6,
                    "image": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=300&fit=crop",
                    "tag_class": "tag-food",
                },
            ],
            "group_members": [
                {"name": "Alex", "avatar": "https://i.pravatar.cc/80?img=1"},
                {"name": "Jamie", "avatar": "https://i.pravatar.cc/80?img=2"},
                {"name": "Sam", "avatar": "https://i.pravatar.cc/80?img=3"},
                {"name": "Taylor", "avatar": "https://i.pravatar.cc/80?img=4"},
            ],
        }
    )
    return render(request, "core/home.html", context)


def groups(request):
    context = base_context("groups")
    groups_data = [
        {
            "id": 1,
            "name": "Weekend Crew",
            "members": [
                {"name": "Alex", "avatar": "https://i.pravatar.cc/80?img=1"},
                {"name": "Jamie", "avatar": "https://i.pravatar.cc/80?img=2"},
                {"name": "Sam", "avatar": "https://i.pravatar.cc/80?img=3"},
                {"name": "Taylor", "avatar": "https://i.pravatar.cc/80?img=4"},
            ],
            "active_plans": 3,
            "status": "Voting",
            "status_class": "badge-voting",
        },
        {
            "id": 2,
            "name": "College Besties",
            "members": [
                {"name": "Morgan", "avatar": "https://i.pravatar.cc/80?img=5"},
                {"name": "Casey", "avatar": "https://i.pravatar.cc/80?img=6"},
                {"name": "Riley", "avatar": "https://i.pravatar.cc/80?img=7"},
            ],
            "active_plans": 1,
            "status": "Planning",
            "status_class": "badge-planning",
        },
        {
            "id": 3,
            "name": "Work Friends",
            "members": [
                {"name": "Jordan", "avatar": "https://i.pravatar.cc/80?img=8"},
                {"name": "Drew", "avatar": "https://i.pravatar.cc/80?img=9"},
                {"name": "Parker", "avatar": "https://i.pravatar.cc/80?img=10"},
                {"name": "Avery", "avatar": "https://i.pravatar.cc/80?img=11"},
                {"name": "Quinn", "avatar": "https://i.pravatar.cc/80?img=12"},
            ],
            "active_plans": 2,
            "status": "Active",
            "status_class": "badge-active",
        },
        {
            "id": 4,
            "name": "Road Trip Gang",
            "members": [
                {"name": "Blake", "avatar": "https://i.pravatar.cc/80?img=13"},
                {"name": "Kai", "avatar": "https://i.pravatar.cc/80?img=14"},
            ],
            "active_plans": 0,
            "status": "Idle",
            "status_class": "badge-idle",
        },
        {
            "id": 5,
            "name": "Summer Squad",
            "members": [
                {"name": "Reese", "avatar": "https://i.pravatar.cc/80?img=15"},
                {"name": "Finley", "avatar": "https://i.pravatar.cc/80?img=16"},
                {"name": "Sky", "avatar": "https://i.pravatar.cc/80?img=17"},
                {"name": "Sage", "avatar": "https://i.pravatar.cc/80?img=18"},
            ],
            "active_plans": 4,
            "status": "Voting",
            "status_class": "badge-voting",
        },
    ]

    context.update(
        {
            "groups": groups_data,
            "total_active_plans": sum(group["active_plans"] for group in groups_data),
        }
    )
    return render(request, "core/groups.html", context)


def discover(request):
    context = base_context("discover")
    context.update(
        {
            "featured": [
                {
                    "title": "Sunset Kayaking",
                    "location": "Lake Tahoe",
                    "rating": 4.8,
                    "price": 45,
                    "duration": "3h",
                    "image": "https://images.unsplash.com/photo-1472745433479-4556f22e32c2?w=600&h=400&fit=crop",
                },
                {
                    "title": "Wine & Paint Night",
                    "location": "Downtown Studio",
                    "rating": 4.9,
                    "price": 35,
                    "duration": "2.5h",
                    "image": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=600&h=400&fit=crop",
                },
            ],
            "activities": [
                {
                    "title": "Bowling Night",
                    "location": "Lucky Strike",
                    "rating": 4.5,
                    "price": 20,
                    "image": "https://images.unsplash.com/photo-1545232979-8bf68ee9b1af?w=400&h=300&fit=crop",
                    "tag": "Indoor",
                    "tag_class": "tag-indoor",
                },
                {
                    "title": "Hiking Trail",
                    "location": "Mount Wilson",
                    "rating": 4.7,
                    "price": 0,
                    "image": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=400&h=300&fit=crop",
                    "tag": "Outdoor",
                    "tag_class": "tag-outdoor",
                },
                {
                    "title": "Escape Room",
                    "location": "Puzzle Masters",
                    "rating": 4.6,
                    "price": 30,
                    "image": "https://images.unsplash.com/photo-1590698933947-a202b069a861?w=400&h=300&fit=crop",
                    "tag": "Adventure",
                    "tag_class": "tag-adventure",
                },
                {
                    "title": "Jazz Night",
                    "location": "Blue Note Lounge",
                    "rating": 4.8,
                    "price": 25,
                    "image": "https://images.unsplash.com/photo-1511192336575-5a79af67a629?w=400&h=300&fit=crop",
                    "tag": "Culture",
                    "tag_class": "tag-culture",
                },
                {
                    "title": "Cooking Class",
                    "location": "Chef Studio",
                    "rating": 4.9,
                    "price": 50,
                    "image": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=400&h=300&fit=crop",
                    "tag": "Food",
                    "tag_class": "tag-food",
                },
                {
                    "title": "Go Karting",
                    "location": "Speedway Arena",
                    "rating": 4.4,
                    "price": 35,
                    "image": "https://images.unsplash.com/photo-1504891616163-a1adbc697fe9?w=400&h=300&fit=crop",
                    "tag": "Adventure",
                    "tag_class": "tag-adventure",
                },
            ],
        }
    )
    return render(request, "core/discover.html", context)


def profile(request):
    context = base_context("profile")
    context.update(
        {
            "stats": [
                {"label": "Plans Created", "value": "24", "icon": "⚡", "color_class": "stat-primary"},
                {"label": "Plans Attended", "value": "18", "icon": "📅", "color_class": "stat-orange"},
                {"label": "Avg Budget", "value": "$32", "icon": "💲", "color_class": "stat-teal"},
            ],
            "achievements": [
                {"title": "Plan Master", "description": "Created 20+ plans", "icon": "🏆", "unlocked": True},
                {"title": "Social Butterfly", "description": "In 5+ groups", "icon": "👥", "unlocked": True},
                {"title": "Explorer", "description": "Tried 10 activity types", "icon": "📍", "unlocked": False},
            ],
            "recent_activity": [
                {"action": "Voted on", "plan": "Beach Day", "group": "Weekend Crew", "time": "2h ago"},
                {"action": "Created", "plan": "Game Night", "group": "College Besties", "time": "1d ago"},
                {"action": "Joined", "plan": "Hiking Trail", "group": "Work Friends", "time": "3d ago"},
            ],
        }
    )
    return render(request, "core/profile.html", context)
