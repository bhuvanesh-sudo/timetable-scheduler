import os
import django
import json
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

client = Client()

data = {
    "username": "admin",
    "password": "admin123"
}

print("Simulating POST /api/auth/token/")
response = client.post(
    '/api/auth/token/',
    data=json.dumps(data),
    content_type='application/json'
)

print(f"Status Code: {response.status_code}")
try:
    print(f"Response Body: {response.json()}")
except Exception:
    print(f"Response Text: {response.content}")

if response.status_code == 200:
    access_token = response.json().get('access')
    print("\nAttempting to fetch /api/auth/me/ with token")
    me_response = client.get(
        '/api/auth/me/',
        HTTP_AUTHORIZATION=f'Bearer {access_token}'
    )
    print(f"Status Code: {me_response.status_code}")
    try:
        print(f"Response Body: {me_response.json()}")
    except Exception:
        print(f"Response Text: {me_response.content}")
