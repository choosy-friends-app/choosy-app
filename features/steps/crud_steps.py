from behave import given, then, when
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Group, GroupMember, Plan, PlanProposal


def user_from_name(name):
    return get_user_model().objects.get(username=name.lower())


def proposal_for(username):
    return PlanProposal.objects.get(created_by=user_from_name(username))


def current_status(context):
    response = getattr(context.browser, "_response", None)
    status = getattr(response, "status_code", None)
    if hasattr(status, "code"):
        return status.code
    return status


def submit_plan_form(context, *, title, price="25.00"):
    proposal = proposal_for("alice")
    context.browser.visit(reverse("crear_plan"))
    context.browser.find_by_name("proposal").select(str(proposal.id))
    context.browser.fill("title", title)
    context.browser.fill("description", "A collaborative plan created by Behave.")
    context.browser.fill("price", price)
    context.browser.fill("duration_minutes", "90")
    context.browser.fill("tag", "food")
    context.browser.fill("place_name", "Barcelona")
    context.browser.fill("address", "Barcelona, Spain")
    context.browser.fill("scheduled_for", "2026-06-20T19:00")
    context.browser.find_by_css("button[type='submit']").first.click()


@given("the following users exist:")
def step_users_exist(context):
    user_model = get_user_model()
    for row in context.table:
        user_model.objects.create_user(
            username=row["username"],
            password=row["password"],
            email=f"{row['username']}@example.test",
        )


@given("Alice owns a group with an open proposal")
def step_alice_group_exists(context):
    alice = user_from_name("alice")
    group = Group.objects.create(name="Alice Group", owner=alice)
    group.add_member(user=alice, role=GroupMember.Role.OWNER)
    PlanProposal.objects.create(
        group=group,
        created_by=alice,
        title="Alice Proposal",
        status=PlanProposal.Status.VOTING,
    )


@given("Bob owns a group with an open proposal")
def step_bob_group_exists(context):
    bob = user_from_name("bob")
    group = Group.objects.create(name="Bob Group", owner=bob)
    group.add_member(user=bob, role=GroupMember.Role.OWNER)
    PlanProposal.objects.create(
        group=group,
        created_by=bob,
        title="Bob Proposal",
        status=PlanProposal.Status.VOTING,
    )


@given('I am logged in as "{username}"')
def step_login(context, username):
    context.browser.visit(reverse("login"))
    context.browser.fill("username", username)
    context.browser.fill("password", "testpass123")
    context.browser.find_by_css("button[type='submit']").first.click()


@given('Bob has a plan titled "{title}"')
def step_bob_has_plan(context, title):
    proposal = proposal_for("bob")
    context.bob_plan = Plan.objects.create(
        proposal=proposal,
        group=proposal.group,
        created_by=user_from_name("bob"),
        title=title,
        description="Bob's private plan",
        price="18.00",
        option_order=0,
    )


@when('I create a plan titled "{title}"')
def step_create_plan(context, title):
    submit_plan_form(context, title=title)
    context.created_plan = Plan.objects.get(title=title)


@when('I update the plan "{old_title}" to "{new_title}"')
def step_update_plan(context, old_title, new_title):
    plan = Plan.objects.get(title=old_title)
    context.browser.visit(reverse("editar_plan", args=[plan.id]))
    context.browser.fill("title", new_title)
    context.browser.find_by_css("button[type='submit']").first.click()


@when('I delete the plan "{title}"')
def step_delete_plan(context, title):
    plan = Plan.objects.get(title=title)
    context.browser.visit(reverse("eliminar_plan", args=[plan.id]))
    context.browser.find_by_css("button[type='submit']").first.click()


@when("I submit the plan form without a title")
def step_submit_without_title(context):
    submit_plan_form(context, title="")


@when("I submit the plan form with an invalid price")
def step_submit_invalid_price(context):
    submit_plan_form(context, title="Invalid price plan", price="not-a-number")


@when("I try to edit Bob's plan")
def step_try_edit_bob_plan(context):
    context.browser.visit(reverse("editar_plan", args=[context.bob_plan.id]))
    context.response_status = current_status(context)


@when("I try to delete Bob's plan")
def step_try_delete_bob_plan(context):
    context.browser.visit(reverse("eliminar_plan", args=[context.bob_plan.id]))
    context.response_status = current_status(context)


@then('I should see that the plan "{title}" exists')
def step_plan_exists(context, title):
    assert Plan.objects.filter(title=title).exists(), f'Expected plan "{title}" to exist'


@then('I should see that the plan "{title}" no longer exists')
def step_plan_not_exists(context, title):
    assert not Plan.objects.filter(title=title).exists(), f'Expected plan "{title}" to be deleted'


@then("the plan should not be created")
def step_plan_not_created(context):
    assert Plan.objects.count() == 0, "Expected no plan to be persisted"


@then("the plan form should show a validation error")
def step_form_validation_error(context):
    body = context.browser.html
    assert "error" in body.lower() or "obligatorio" in body.lower() or "required" in body.lower()


@then("the request should be forbidden")
def step_request_forbidden(context):
    assert context.response_status == 403 or "403" in context.browser.html or "Forbidden" in context.browser.html


@then('Bob\'s plan title should still be "{title}"')
def step_bob_title_unchanged(context, title):
    context.bob_plan.refresh_from_db()
    assert context.bob_plan.title == title
