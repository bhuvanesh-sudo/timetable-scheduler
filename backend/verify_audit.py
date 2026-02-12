"""
Script to verify audit logs and API functionality.
"""
import requests
import json
import sys

BASE_URL = 'http://localhost:8000'

def test_audit_logs():
    print("1. Logging in as admin...")
    try:
        resp = requests.post(f'{BASE_URL}/api/auth/token/', json={'username': 'admin', 'password': 'admin123'})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token = resp.json().get('access')
        headers = {'Authorization': f'Bearer {token}'}
        print("   Login successful.")

        print("\n2. Fetching Audit Logs...")
        resp = requests.get(f'{BASE_URL}/api/audit-logs/', headers=headers)
        if resp.status_code == 200:
            logs = resp.json()
            print(f"   Success! Retrieved {len(logs)} logs.")
            print("   Latest 3 logs:")
            for l in logs[:3]:
                user = l.get('user_name', 'N/A')
                action = l.get('action', 'N/A')
                model = l.get('model_name', 'N/A')
                timestamp = l.get('timestamp', '')[:19]
                print(f"   - [{timestamp}] {user} | {action} | {model}")
        else:
            print(f"   Failed to fetch logs: {resp.status_code} {resp.text}")

        print("\n3. Testing Backup Creation (should create audit log)...")
        backup_data = {'label': 'Final Verification Test'}
        resp = requests.post(f'{BASE_URL}/api/system/backups/create/', json=backup_data, headers=headers)
        if resp.status_code == 201:
            print("   Backup created successfully.")
            filename = resp.json().get('filename')
            print(f"   Filename: {filename}")
            
            # Verify the BACKUP log exists
            print("\n4. Verifying BACKUP log entry...")
            resp = requests.get(f'{BASE_URL}/api/audit-logs/', headers=headers)
            logs = resp.json()
            found = False
            for l in logs[:5]:
                if l['action'] == 'BACKUP' and l['object_id'] == filename:
                    print(f"   FOUND: {l['action']} log for {l['object_id']}")
                    found = True
                    break
            if not found:
                print("   WARNING: BACKUP log not found in recent entries!")
        else:
            print(f"   Backup creation failed: {resp.status_code} {resp.text}")

        print("\n5. Testing User Lifecycle Logging (Create & Delete)...")
        # UserViewSet uses UserSerializer.
        # Let's try creating a user.
        new_user = {
            "username": "audit_test_user",
            "email": "audit@test.com",
            "password": "testpassword123",
            "role": "STUDENT"
        }
        
        # Admin creates user
        print(f"   Creating user {new_user['username']}...")
        resp = requests.post(f'{BASE_URL}/api/auth/users/', json=new_user, headers=headers)
        
        if resp.status_code == 201:
            user_data = resp.json()
            user_id = user_data.get('id')
            print(f"   User created (ID: {user_id}).")
            
            # Now delete the user
            print(f"   Deleting user {user_id}...")
            resp = requests.delete(f'{BASE_URL}/api/auth/users/{user_id}/', headers=headers)
            
            if resp.status_code == 204:
                print("   User deleted successfully.")
                
                # Check logs again
                print("\n6. Verifying User Lifecycle Logs...")
                resp = requests.get(f'{BASE_URL}/api/audit-logs/', headers=headers)
                logs = resp.json()
                
                created_found = False
                deleted_found = False
                
                # Search recent logs for our test user
                for l in logs[:20]:
                    if l['model_name'] == 'User':
                        details_str = str(l.get('details', ''))
                        obj_id = str(l.get('object_id', ''))
                        
                        if l['action'] == 'CREATE' and (str(user_id) == obj_id or 'audit_test_user' in details_str):
                            created_found = True
                            print(f"   ✅ FOUND: User CREATE log for ID {obj_id}")
                        
                        if l['action'] == 'DELETE' and (str(user_id) == obj_id or 'audit_test_user' in details_str):
                            deleted_found = True
                            print(f"   ✅ FOUND: User DELETE log for ID {obj_id}")

                if created_found and deleted_found:
                    print("   ✅ SUCCESS: User creation and deletion were logged correctly!")
                else:
                    print(f"   ❌ FAILURE: Missing logs. Created: {created_found}, Deleted: {deleted_found}")
            else:
                 print(f"   Failed to delete user: {resp.status_code} {resp.text}")
        else:
            # If user already exists, try to delete it first? Or just ignore
            if "already exists" in resp.text:
                print("   User already exists, skipping creation test but checking deletion...")
                # Try to find ID? Hard without list.
                # Just skip for now.
                print(f"   Skipping user lifecycle test: {resp.text}")
            else:
                print(f"   Failed to create user: {resp.status_code} {resp.text}")


    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    test_audit_logs()
