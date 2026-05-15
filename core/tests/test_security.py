import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Group, GroupMember, Plan, PlanProposal


class SecurityAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="owner", password="testpass123")
        self.member = user_model.objects.create_user(username="member", password="testpass123")
        self.outsider = user_model.objects.create_user(username="outsider", password="testpass123")

        self.group = Group.objects.create(name="Private Group", owner=self.owner)
        self.group.add_member(user=self.owner, role=GroupMember.Role.OWNER)
        self.group.add_member(user=self.member, role=GroupMember.Role.MEMBER)

        self.proposal = PlanProposal.objects.create(
            group=self.group,
            created_by=self.owner,
            title="Friday Plan",
            status=PlanProposal.Status.VOTING,
        )
        self.plan = Plan.objects.create(
            proposal=self.proposal,
            group=self.group,
            created_by=self.owner,
            title="Dinner",
            option_order=1,
        )

    def test_groups_page_requires_login(self):
        response = self.client.get(reverse("groups"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_vote_api_requires_authenticated_member(self):
        response = self.client.post(
            reverse("api_submit_vote", args=[self.plan.id]),
            data=json.dumps({"value": 1}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "Authentication required")

    def test_invitation_detail_rejects_uninvited_users(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("invitation_detail", args=[self.group.id]))

        self.assertEqual(response.status_code, 403)

    def test_plan_update_rejects_non_creator_with_403(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("editar_plan", args=[self.plan.id]))

        self.assertEqual(response.status_code, 403)

    def test_plan_delete_rejects_non_creator_with_403(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("eliminar_plan", args=[self.plan.id]))

        self.assertEqual(response.status_code, 403)

    def test_plan_create_cannot_use_another_users_proposal(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("crear_plan"),
            data={
                "proposal": self.proposal.id,
                "title": "Unauthorized plan",
                "description": "Should not be accepted",
                "price": "10.00",
                "duration_minutes": "45",
                "tag": "food",
                "image_url": "",
                "place_name": "Barcelona",
                "address": "Barcelona, Spain",
                "scheduled_for": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Plan.objects.filter(title="Unauthorized plan").exists())
