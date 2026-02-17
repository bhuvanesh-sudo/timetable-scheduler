import requests
import json

base_url = "http://127.0.0.1:8000/api"

def test_login(username, password):
    url = f"{base_url}/auth/token/"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Testing login for {username} at {url}...")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

if __name__ == "__main__":
    test_login("admin", "admin123")
    print("-" * 20)
    test_login("superadmin", "password123")
