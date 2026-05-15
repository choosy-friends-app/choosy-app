from behave import given, then, when
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Group, GroupMember, Plan, PlanProposal


def user_from_name(name):
    return get_user_model().objects.get(username=name.lower())


def proposal_for(username):
    return PlanProposal.objects.get(created_by=user_from_name(username))


def group_for(username):
    return Group.objects.filter(owner=user_from_name(username)).order_by("-id").first()


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


@given('Bob has a group named "{name}"')
def step_bob_has_group(context, name):
    bob = user_from_name("bob")
    context.bob_group = Group.objects.create(name=name, owner=bob)
    context.bob_group.add_member(user=bob, role=GroupMember.Role.OWNER)


@given('Alice owns an extra group named "{name}" without proposals')
def step_alice_extra_group(context, name):
    alice = user_from_name("alice")
    group = Group.objects.create(name=name, owner=alice)
    group.add_member(user=alice, role=GroupMember.Role.OWNER)
    context.alice_extra_group = group


@given('Bob has a proposal titled "{title}"')
def step_bob_has_proposal(context, title):
    bob = user_from_name("bob")
    group = Group.objects.create(name=f"{title} Group", owner=bob)
    group.add_member(user=bob, role=GroupMember.Role.OWNER)
    context.bob_proposal = PlanProposal.objects.create(
        group=group,
        created_by=bob,
        title=title,
        status=PlanProposal.Status.VOTING,
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


@when('I create a group named "{name}"')
def step_create_group(context, name):
    context.browser.visit(reverse("crear_grupo"))
    context.browser.fill("name", name)
    context.browser.fill("description", "Group created by Behave")
    context.browser.fill("mission_statement", "Keep plans simple")
    context.browser.fill("hero_image_url", "https://example.test/hero.jpg")
    context.browser.fill("interests", '["cinema", "food"]')
    context.browser.find_by_css("button[type='submit']").first.click()
    context.created_group_name = name


@when("I submit the group form without a name")
def step_submit_group_without_name(context):
    context.group_count_before_invalid_submit = Group.objects.count()
    context.browser.visit(reverse("crear_grupo"))
    context.browser.fill("description", "Missing required name")
    context.browser.find_by_css("button[type='submit']").first.click()


@when('I update the group "{old_name}" to "{new_name}"')
def step_update_group(context, old_name, new_name):
    group = Group.objects.get(name=old_name)
    context.browser.visit(reverse("editar_grupo", args=[group.id]))
    context.browser.fill("name", new_name)
    context.browser.find_by_css("button[type='submit']").first.click()


@when('I delete the group "{name}"')
def step_delete_group(context, name):
    group = Group.objects.get(name=name)
    context.browser.visit(reverse("eliminar_grupo", args=[group.id]))
    context.browser.find_by_css("button[type='submit']").first.click()


@when("I try to edit Bob's group")
def step_try_edit_bob_group(context):
    context.browser.visit(reverse("editar_grupo", args=[context.bob_group.id]))
    context.response_status = current_status(context)


@when("I try to delete Bob's group")
def step_try_delete_bob_group(context):
    context.browser.visit(reverse("eliminar_grupo", args=[context.bob_group.id]))
    context.response_status = current_status(context)


@when('I create a proposal titled "{title}" for group "{group_name}"')
def step_create_proposal(context, title, group_name):
    group = Group.objects.get(name=group_name, owner=user_from_name("alice"))
    context.browser.visit(reverse("crear_propuesta"))
    context.browser.find_by_name("group").select(str(group.id))
    context.browser.fill("title", title)
    context.browser.fill("description", "Proposal created by Behave")
    context.browser.find_by_css("button[type='submit']").first.click()
    context.created_proposal_title = title


@when('I submit the proposal form without a title for group "{group_name}"')
def step_submit_proposal_without_title(context, group_name):
    group = Group.objects.get(name=group_name, owner=user_from_name("alice"))
    context.proposal_count_before_invalid_submit = PlanProposal.objects.count()
    context.browser.visit(reverse("crear_propuesta"))
    context.browser.find_by_name("group").select(str(group.id))
    context.browser.fill("description", "Missing required title")
    context.browser.find_by_css("button[type='submit']").first.click()


@when('I update the proposal "{old_title}" to "{new_title}"')
def step_update_proposal(context, old_title, new_title):
    proposal = PlanProposal.objects.get(title=old_title)
    context.browser.visit(reverse("editar_propuesta", args=[proposal.id]))
    context.browser.fill("title", new_title)
    context.browser.find_by_css("button[type='submit']").first.click()


@when('I delete the proposal "{title}"')
def step_delete_proposal(context, title):
    proposal = PlanProposal.objects.get(title=title)
    context.browser.visit(reverse("eliminar_propuesta", args=[proposal.id]))
    context.browser.find_by_css("button[type='submit']").first.click()


@when("I try to edit Bob's proposal")
def step_try_edit_bob_proposal(context):
    context.browser.visit(reverse("editar_propuesta", args=[context.bob_proposal.id]))
    context.response_status = current_status(context)


@when("I try to delete Bob's proposal")
def step_try_delete_bob_proposal(context):
    context.browser.visit(reverse("eliminar_propuesta", args=[context.bob_proposal.id]))
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


@then('I should see that the group "{name}" exists')
def step_group_exists(context, name):
    assert Group.objects.filter(name=name).exists(), f'Expected group "{name}" to exist'


@then('I should see that the group "{name}" no longer exists')
def step_group_not_exists(context, name):
    assert not Group.objects.filter(name=name).exists(), f'Expected group "{name}" to be deleted'


@then("the group should not be created")
def step_group_not_created(context):
    assert (
        Group.objects.count() == context.group_count_before_invalid_submit
    ), "Expected invalid group creation to fail"


@then('Bob\'s group name should still be "{name}"')
def step_bob_group_name_unchanged(context, name):
    context.bob_group.refresh_from_db()
    assert context.bob_group.name == name


@then('I should see that the proposal "{title}" exists')
def step_proposal_exists(context, title):
    assert PlanProposal.objects.filter(title=title).exists(), f'Expected proposal "{title}" to exist'


@then('I should see that the proposal "{title}" no longer exists')
def step_proposal_not_exists(context, title):
    assert not PlanProposal.objects.filter(title=title).exists(), f'Expected proposal "{title}" to be deleted'


@then("the proposal should not be created")
def step_proposal_not_created(context):
    assert (
        PlanProposal.objects.count() == context.proposal_count_before_invalid_submit
    ), "Expected invalid proposal creation to fail"


@then('Bob\'s proposal title should still be "{title}"')
def step_bob_proposal_title_unchanged(context, title):
    context.bob_proposal.refresh_from_db()
    assert context.bob_proposal.title == title


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
