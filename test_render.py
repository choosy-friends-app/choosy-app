import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "choosy.settings")
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

client = Client()
client.force_login(user)

response = client.get('/invitation/1/')
print("STATUS:", response.status_code)
# print the first 2000 chars to see what happened to the <style> tag
print("CONTENT TYPE:", response['Content-Type'])
content = response.content.decode('utf-8')
print("LENGTH:", len(content))
print("--- START HTML ---")
print(content[:1500])
print("--- END HTML ---")
