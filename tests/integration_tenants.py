
import asyncio
import sys

import httpx

# Base URL for the backend
BASE_URL = "http://localhost:8000/api/v1"

async def test_integration_tenants():
    print("🚀 Starting Integration Test: Tenants Flow")
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("\n1. Logging in...")
        login_data = {
            "username": "admin@vipmemory.com",
            "password": "admin123"
        }
        
        response = await client.post(f"{BASE_URL}/auth/token", data=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")

        # 2. Create Tenant
        print("\n2. Creating Tenant...")
        tenant_data = {
            "name": "Test Tenant",
            "description": "Integration Test Tenant",
            "plan": "free"
        }
        
        response = await client.post(f"{BASE_URL}/tenants/", json=tenant_data, headers=headers)
        if response.status_code == 201:
            tenant = response.json()
            print(f"✅ Tenant created: {tenant['id']} - {tenant['name']}")
        elif response.status_code == 400 and "already owns a tenant" in response.text:
             print("ℹ️ User already owns a tenant (expected if run multiple times)")
             # Try to list to get the ID
             list_resp = await client.get(f"{BASE_URL}/tenants/", headers=headers)
             tenant = list_resp.json()['tenants'][0]
        else:
            print(f"❌ Create Tenant failed: {response.status_code} - {response.text}")
            return False

        # 3. List Tenants
        print("\n3. Listing Tenants...")
        response = await client.get(f"{BASE_URL}/tenants/", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ List Tenants failed: {response.status_code} - {response.text}")
            return False
            
        data = response.json()
        print(f"✅ List Tenants successful! Found {data['total']} tenants")
        
        if data['total'] == 0:
            print("❌ Expected at least 1 tenant")
            return False

    print("\n✅ All Tenant Integration Tests Passed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_integration_tenants())
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        sys.exit(1)
