#!/usr/bin/env python3
"""
Smoke-test all HTTP routes (run against a migrated DB).

From repo root:
  DATABASE_URL=... .venv/bin/python -m scripts.verify_api
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

# Configure before any app imports
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://airfreeze:airfreeze@localhost:5433/airfreeze",
)
_admin_tag = uuid.uuid4().hex[:10]
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = f"admin_{_admin_tag}@example.com"

from starlette.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def main() -> None:
    with TestClient(app, raise_server_exceptions=True) as client:
        # --- Auth: admin (bootstrap) ---
        admin_email = os.environ["BOOTSTRAP_ADMIN_EMAIL"]
        r = client.post(
            "/auth/register",
            json={"email": admin_email, "password": "password12"},
        )
        if r.status_code != 201:
            fail(f"admin register: {r.status_code} {r.text}")
        admin_access = r.json()["access_token"]
        admin_refresh = r.json()["refresh_token"]
        admin_h = {"Authorization": f"Bearer {admin_access}"}

        r = client.post(
            "/auth/register",
            json={"email": admin_email, "password": "password12"},
        )
        if r.status_code != 200:
            fail(f"admin register idempotent: {r.status_code} {r.text}")

        # --- Auth: normal user ---
        u_email = f"user_{_admin_tag}@example.com"
        r = client.post("/auth/register", json={"email": u_email, "password": "password12"})
        if r.status_code != 201:
            fail(f"user register: {r.status_code} {r.text}")
        user_access = r.json()["access_token"]
        user_refresh = r.json()["refresh_token"]
        user_h = {"Authorization": f"Bearer {user_access}"}

        r = client.post("/auth/register", json={"email": u_email, "password": "wrongpass"})
        if r.status_code != 409:
            fail(f"duplicate wrong password: expected 409, got {r.status_code}")

        r = client.post("/auth/login", json={"email": u_email, "password": "password12"})
        if r.status_code != 200:
            fail(f"login: {r.status_code} {r.text}")

        r = client.post("/auth/refresh", json={"refresh_token": user_refresh})
        if r.status_code != 200:
            fail(f"refresh: {r.status_code} {r.text}")
        user_access = r.json()["access_token"]
        user_h = {"Authorization": f"Bearer {user_access}"}

        r = client.post("/auth/login", json={"email": u_email, "password": "bad"})
        if r.status_code != 401:
            fail(f"bad login: expected 401, got {r.status_code}")

        # --- Users ---
        r = client.get("/users/me", headers=user_h)
        if r.status_code != 200 or r.json()["email"] != u_email:
            fail(f"users/me: {r.status_code} {r.text}")

        r = client.get("/users/me")
        if r.status_code != 401:
            fail(f"users/me without auth: expected 401, got {r.status_code}")

        r = client.patch(
            "/users/me/password",
            headers=user_h,
            json={"current_password": "password12", "new_password": "password34"},
        )
        if r.status_code != 200:
            fail(f"password change: {r.status_code} {r.text}")

        user_h = {"Authorization": f"Bearer {user_access}"}  # old token still valid until expiry
        r = client.patch(
            "/users/me/password",
            headers=user_h,
            json={"current_password": "password34", "new_password": "password12"},
        )
        if r.status_code != 200:
            fail(f"password change back: {r.status_code} {r.text}")

        r = client.post("/auth/login", json={"email": u_email, "password": "password12"})
        if r.status_code != 200:
            fail(f"login after password revert: {r.status_code} {r.text}")
        user_access = r.json()["access_token"]
        user_h = {"Authorization": f"Bearer {user_access}"}

        # --- Flights public ---
        r = client.get("/flights", params={"skip": 0, "limit": 5})
        if r.status_code != 200:
            fail(f"GET /flights: {r.status_code} {r.text}")
        catalog = r.json()
        if "items" not in catalog or not catalog["items"]:
            fail("GET /flights: empty catalog (need seed/migration)")
        now_utc = datetime.now(timezone.utc)
        target_item = None
        for item in catalog["items"]:
            dep_i = datetime.fromisoformat(item["departure_time"].replace("Z", "+00:00"))
            if dep_i > now_utc:
                target_item = item
                break
        if target_item is None:
            fail("GET /flights: no future flights found")

        flight_id = target_item["id"]
        dep = datetime.fromisoformat(target_item["departure_time"].replace("Z", "+00:00"))
        search_date = dep.date()

        r = client.get(
            "/flights/search",
            params={
                "from_city": target_item["from_city"],
                "to_city": target_item["to_city"],
                "date": search_date.isoformat(),
                "passengers": 1,
            },
        )
        if r.status_code != 200:
            fail(f"search: {r.status_code} {r.text}")

        r = client.get(
            "/flights/search",
            headers=user_h,
            params={
                "from_city": target_item["from_city"],
                "to_city": target_item["to_city"],
                "date": search_date.isoformat(),
                "passengers": 2,
                "sort_by": "price",
                "sort_order": "desc",
            },
        )
        if r.status_code != 200:
            fail(f"search (auth, sort): {r.status_code} {r.text}")
        sf = r.json()
        if sf:
            if "stops" not in sf[0] or "duration_minutes" not in sf[0]:
                fail("FlightOut missing stops or duration_minutes")
            if len(sf) >= 2 and sf[0]["price"] < sf[-1]["price"]:
                fail("price desc sort inconsistent")

        r = client.get("/searches/my", headers=user_h)
        if r.status_code != 200 or r.json()["total"] < 1:
            fail(f"searches/my: {r.status_code} {r.text}")
        entry_id = r.json()["items"][0]["id"]

        r = client.delete(f"/searches/{entry_id}", headers=user_h)
        if r.status_code != 204:
            fail(f"delete search: {r.status_code} {r.text}")

        r = client.get("/searches/my")
        if r.status_code != 401:
            fail(f"searches/my without auth: expected 401, got {r.status_code}")

        r = client.get(f"/flights/{flight_id}")
        if r.status_code != 200:
            fail(f"GET flight: {r.status_code} {r.text}")

        r = client.get("/flights/999999999")
        if r.status_code != 404:
            fail(f"missing flight: expected 404, got {r.status_code}")

        # --- Admin flights CRUD ---
        new_dep = datetime.now(timezone.utc) + timedelta(days=30)
        new_arr = new_dep + timedelta(hours=2)
        r = client.post(
            "/admin/flights",
            headers=admin_h,
            json={
                "from_city": "TestCityA",
                "to_city": "TestCityB",
                "departure_time": new_dep.isoformat(),
                "arrival_time": new_arr.isoformat(),
                "price": 99.5,
            },
        )
        if r.status_code != 201:
            fail(f"admin create flight: {r.status_code} {r.text}")
        new_fid = r.json()["id"]

        r = client.patch(
            f"/admin/flights/{new_fid}",
            headers=admin_h,
            json={"price": 88.0},
        )
        if r.status_code != 200 or r.json()["price"] != 88.0:
            fail(f"admin patch flight: {r.status_code} {r.text}")

        r = client.get("/admin/flights", headers=admin_h, params={"skip": 0, "limit": 3})
        if r.status_code != 200:
            fail(f"admin list flights: {r.status_code} {r.text}")

        r = client.get(f"/flights/{new_fid}")
        if r.status_code != 200:
            fail(f"GET created flight: {r.status_code} {r.text}")

        # --- Freeze + booking (user) ---
        r = client.post("/freeze", headers=user_h, json={"flight_id": flight_id})
        if r.status_code != 201:
            fail(f"freeze: {r.status_code} {r.text}")
        freeze_id = r.json()["id"]
        frozen_price = r.json()["frozen_price"]

        r = client.get("/freeze/my", headers=user_h)
        if r.status_code != 200 or not any(f["id"] == freeze_id for f in r.json()):
            fail(f"freeze/my: {r.status_code} {r.text}")

        r = client.get(f"/freeze/{freeze_id}", headers=user_h)
        if r.status_code != 200:
            fail(f"freeze get: {r.status_code} {r.text}")

        r = client.get(f"/admin/freezes/{freeze_id}", headers=admin_h)
        if r.status_code != 200:
            fail(f"admin get freeze: {r.status_code} {r.text}")

        r = client.get(f"/freeze/{freeze_id}", headers=admin_h)
        if r.status_code != 404:
            fail(f"freeze other user: expected 404, got {r.status_code}")

        r = client.post("/booking", headers=user_h, json={"flight_id": flight_id})
        if r.status_code != 201:
            fail(f"booking: {r.status_code} {r.text}")
        if abs(r.json()["price_paid"] - frozen_price) > 0.01:
            fail("booking should use frozen_price")

        booking_id = r.json()["id"]

        r = client.get("/booking/my", headers=user_h)
        if r.status_code != 200:
            fail(f"booking/my: {r.status_code} {r.text}")

        r = client.get(f"/booking/{booking_id}", headers=user_h)
        if r.status_code != 200:
            fail(f"booking get: {r.status_code} {r.text}")

        r = client.patch(
            f"/booking/{booking_id}",
            headers=user_h,
            json={"status": "cancelled"},
        )
        if r.status_code != 200 or r.json()["status"] != "cancelled":
            fail(f"booking cancel: {r.status_code} {r.text}")

        r = client.patch(
            f"/booking/{booking_id}",
            headers=user_h,
            json={"status": "cancelled"},
        )
        if r.status_code != 400:
            fail(f"double cancel: expected 400, got {r.status_code}")

        # Second booking without freeze (use admin-created flight)
        r = client.post("/booking", headers=user_h, json={"flight_id": new_fid})
        if r.status_code != 201:
            fail(f"booking no freeze: {r.status_code} {r.text}")
        if abs(r.json()["price_paid"] - 88.0) > 0.01:
            fail("booking without freeze should use flight price")

        booking2_id = r.json()["id"]

        r = client.post("/freeze", headers=user_h, json={"flight_id": new_fid})
        if r.status_code != 201:
            fail(f"second freeze: {r.status_code} {r.text}")
        freeze_extra_id = r.json()["id"]

        r = client.delete(f"/admin/freezes/{freeze_extra_id}", headers=admin_h)
        if r.status_code != 204:
            fail(f"admin delete freeze: {r.status_code} {r.text}")

        r = client.get(f"/freeze/{freeze_extra_id}", headers=user_h)
        if r.status_code != 404:
            fail(f"freeze after admin delete: expected 404, got {r.status_code}")

        r = client.post("/freeze", json={"flight_id": flight_id})
        if r.status_code != 401:
            fail(f"freeze without auth: expected 401, got {r.status_code}")

        r = client.delete(f"/freeze/{freeze_id}", headers=user_h)
        if r.status_code != 204:
            fail(f"freeze delete: {r.status_code} {r.text}")

        # --- Admin lists / patch / delete ---
        r = client.get("/admin/users", headers=admin_h)
        if r.status_code != 200:
            fail(f"admin users: {r.status_code} {r.text}")

        uid = r.json()["items"][0]["id"]
        r = client.get(f"/admin/users/{uid}", headers=admin_h)
        if r.status_code != 200:
            fail(f"admin user by id: {r.status_code} {r.text}")

        r = client.get("/admin/users", headers=user_h)
        if r.status_code != 403:
            fail(f"admin as user: expected 403, got {r.status_code}")

        r = client.get("/admin/freezes", headers=admin_h)
        if r.status_code != 200:
            fail(f"admin freezes: {r.status_code} {r.text}")

        r = client.get("/admin/bookings", headers=admin_h)
        if r.status_code != 200:
            fail(f"admin bookings: {r.status_code} {r.text}")

        r = client.patch(
            f"/admin/bookings/{booking2_id}",
            headers=admin_h,
            json={"status": "cancelled"},
        )
        if r.status_code != 200:
            fail(f"admin patch booking: {r.status_code} {r.text}")

        r = client.delete(f"/admin/bookings/{booking2_id}", headers=admin_h)
        if r.status_code != 204:
            fail(f"admin delete booking: {r.status_code} {r.text}")

        r = client.delete(f"/admin/flights/{new_fid}", headers=admin_h)
        if r.status_code != 204:
            fail(f"admin delete flight: {r.status_code} {r.text}")

        r = client.get("/docs")
        if r.status_code != 200:
            fail(f"/docs: {r.status_code}")

        r = client.get("/redoc")
        if r.status_code != 200:
            fail(f"/redoc: {r.status_code}")

    print("OK: all checked routes returned expected status codes.")


if __name__ == "__main__":
    main()
