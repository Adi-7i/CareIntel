import asyncio
import httpx
from careintel.main import app

async def main():
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            print("[*] Testing GET /api/v1/health/live...")
            live_resp = await client.get("/api/v1/health/live")
            print(f"[OK] Live response: {live_resp.status_code} - {live_resp.json()}")

            print("[*] Testing GET /api/v1/health/ready...")
            ready_resp = await client.get("/api/v1/health/ready")
            print(f"[OK] Ready response: {ready_resp.status_code} - {ready_resp.json()}")

            print("[*] Testing POST /api/v1/auth/login...")
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "doctor@careintel.local", "password": "demo123"}
            )
            login_data = login_resp.json()
            token = login_data.get("access_token") or login_data.get("data", {}).get("access_token")
            print(f"[OK] Access token received: {token[:25]}...")

            print("[*] Testing GET /api/v1/auth/me...")
            me_resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"[OK] /me response status: {me_resp.status_code}")
            print(f"[OK] /me data: {me_resp.json()}")

            print("\n[SUCCESS] Full ASGI HTTP & Auth Pipeline verified successfully!")

if __name__ == "__main__":
    asyncio.run(main())
