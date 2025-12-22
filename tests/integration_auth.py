
import asyncio
import sys

import httpx

# Base URL for the backend
BASE_URL = "http://localhost:8000/api/v1"

async def test_integration_auth():
    print("🚀 Starting Integration Test: Auth Flow")
    
    async with httpx.AsyncClient() as client:
        # 1. Test Login (POST /auth/token)
        print("\n1. Testing Login (POST /auth/token)...")
        login_data = {
            "username": "admin@vipmemory.com",
            "password": "admin123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/token", data=login_data)
            
            if response.status_code != 200:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
            token_data = response.json()
            access_token = token_data.get("access_token")
            token_type = token_data.get("token_type")
            
            if not access_token:
                print("❌ Login successful but no access_token returned")
                return False
                
            print(f"✅ Login successful! Token type: {token_type}")
            print(f"🔑 Access Token: {access_token[:10]}...")
            
        except Exception as e:
            print(f"❌ Login request error: {e}")
            return False

        # 2. Test Get Current User (GET /auth/me)
        print("\n2. Testing Get User (GET /auth/me)...")
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Get User failed: {response.status_code} - {response.text}")
                return False
                
            user_data = response.json()
            print("✅ Get User successful!")
            print(f"👤 User: {user_data.get('email')} ({user_data.get('role')})")
            
            if user_data.get("email") != "admin@vipmemory.com":
                 print(f"❌ User email mismatch: Expected admin@vipmemory.com, got {user_data.get('email')}")
                 return False

        except Exception as e:
            print(f"❌ Get User request error: {e}")
            return False
            
    print("\n✅ All Integration Tests Passed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_integration_auth())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except ConnectionRefusedError:
         print(f"\n❌ Could not connect to {BASE_URL}. Is the server running?")
         sys.exit(1)
