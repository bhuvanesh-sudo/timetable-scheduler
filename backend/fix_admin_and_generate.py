import os
import django
import requests

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def run():
    print("🔧 Fixing Admin Role...")
    try:
        admin = User.objects.get(username='admin')
        if admin.role != 'ADMIN':
            admin.role = 'ADMIN'
            admin.save()
            print("✅ Admin role updated to 'ADMIN'")
        else:
            print("ℹ️  Admin role is already 'ADMIN'")
            
    except User.DoesNotExist:
        print("❌ Admin user not found!")
        return

    print("\n🚀 Triggering Schedule Generation via API...")
    
    # 1. Login as Admin to get Token
    login_url = 'http://127.0.0.1:8000/api/auth/token/'
    login_data = {'username': 'admin', 'password': 'admin'}
    
    try:
        auth_response = requests.post(login_url, data=login_data)
        if auth_response.status_code != 200:
            print(f"❌ Login Failed: {auth_response.status_code}")
            print(auth_response.text)
            return
            
        tokens = auth_response.json()
        access_token = tokens['access']
        print("✅ Admin Logged In")
        
        # 2. Generate Schedule
        generate_url = 'http://127.0.0.1:8000/api/scheduler/generate'
        headers = {'Authorization': f'Bearer {access_token}'}
        payload = {
            'name': 'Verification Schedule',
            'year': 1,
            'semester': 'odd'
        }
        
        print("⏳ Sending Generation Request...")
        gen_response = requests.post(generate_url, headers=headers, json=payload)
        
        if gen_response.status_code == 200:
            data = gen_response.json()
            print(f"✅ Schedule Generated! ID: {data.get('schedule_id')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('data', {}).get('quality_score'):
                print(f"   Quality Score: {data['data']['quality_score']}")
        else:
            print(f"❌ Generation Failed: {gen_response.status_code}")
            print(gen_response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    run()
