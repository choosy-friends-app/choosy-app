import os

os.environ.setdefault("SECRET_KEY", "behave-test-secret-key")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "choosy.settings")

import django
from django.core.management import call_command
from django.test.utils import setup_test_environment, teardown_test_environment
from splinter import Browser

django.setup()


def before_all(context):
    setup_test_environment()
    call_command("migrate", verbosity=0, interactive=False)
    context.browser = Browser("django")


def before_scenario(context, scenario):
    call_command("flush", verbosity=0, interactive=False)
    context.created_plan = None
    context.response_status = None


def after_all(context):
    if hasattr(context, "browser"):
        context.browser.quit()
    teardown_test_environment()
