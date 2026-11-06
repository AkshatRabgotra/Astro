"""Google Authentication and User Session router for Melooha."""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import httpx

from backend.config import settings
from backend.database import get_db
from backend.models import User, BirthProfile, Chart, BalanceLedger, Question, Answer
from backend.ledger import get_balance, topup_credits
from chart.models import ChartFacts

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/config")
def get_auth_config():
    """Return public auth configuration for frontend clients."""
    client_id = settings.GOOGLE_CLIENT_ID or os.getenv("GOOGLE_CLIENT_ID", "")
    return {
        "google_client_id": client_id,
    }


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None  # Google JWT ID token
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None


class GuestAuthRequest(BaseModel):
    name: Optional[str] = "Akshat"


async def verify_google_token(id_token: str) -> dict:
    """Verify Google ID token via Google TokenInfo API."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": data.get("email"),
                    "name": data.get("name") or data.get("email", "").split("@")[0],
                    "avatar_url": data.get("picture"),
                    "google_id": data.get("sub"),
                }
    except Exception as e:
        print(f"Warning: Google token validation failed: {e}")
    return {}


@router.post("/google")
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth credentials."""
    email = payload.email
    name = payload.name
    avatar_url = payload.avatar_url
    google_id = payload.google_id

    # If raw credential (JWT ID token) is provided, verify with Google API
    if payload.credential:
        verified = await verify_google_token(payload.credential)
        if verified.get("email"):
            email = verified["email"]
            name = verified.get("name") or name
            avatar_url = verified.get("avatar_url") or avatar_url
            google_id = verified.get("google_id") or google_id

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address is required for authentication."
        )

    # Check if user already exists by email or google_id
    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    is_new_user = False
    if not user:
        # Create new User record in PostgreSQL / SQLite
        is_new_user = True
        user = User(
            name=name or email.split("@")[0].title(),
            email=email,
            google_id=google_id,
            avatar_url=avatar_url,
            auth_provider="google"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Grant 5 free welcome question credits
        topup_credits(
            db=db,
            user_id=user.id,
            count=5,
            idempotency_key=f"welcome_{user.id}",
            description="Google Welcome Bonus",
        )
    else:
        # Update existing user profile with latest details
        updated = False
        if name and not user.name:
            user.name = name
            updated = True
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if google_id and not user.google_id:
            user.google_id = google_id
            updated = True
        if updated:
            db.commit()
            db.refresh(user)

    # Fetch user's active birth profiles and chart facts if already created
    all_profiles = (
        db.query(BirthProfile)
        .filter(BirthProfile.user_id == user.id)
        .order_by(BirthProfile.created_at.asc())
        .all()
    )

    birth_profile = all_profiles[-1] if all_profiles else None

    chart_facts = None
    if birth_profile:
        chart_record = db.query(Chart).filter(Chart.birth_profile_id == birth_profile.id).first()
        if chart_record and chart_record.facts_json:
            chart_facts = chart_record.facts_json

    balance = get_balance(db, user.id)

    profiles_data = [
        {
            "id": p.id,
            "user_id": p.user_id,
            "name": p.name,
            "place_name": p.place_name,
            "birth_date": str(p.birth_date),
            "birth_time": p.birth_time,
            "time_known": p.time_known,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "timezone_str": p.timezone_str,
        }
        for p in all_profiles
    ]

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "auth_provider": user.auth_provider,
        },
        "profile": {
            "id": birth_profile.id,
            "user_id": user.id,
            "name": birth_profile.name,
            "place_name": birth_profile.place_name,
            "birth_date": str(birth_profile.birth_date),
            "birth_time": birth_profile.birth_time,
            "time_known": birth_profile.time_known,
            "latitude": birth_profile.latitude,
            "longitude": birth_profile.longitude,
            "timezone_str": birth_profile.timezone_str,
        } if birth_profile else None,
        "profiles": profiles_data,
        "chart_facts": chart_facts,
        "balance": balance,
        "is_new_user": is_new_user,
    }


@router.post("/guest")
async def guest_auth(payload: GuestAuthRequest, db: Session = Depends(get_db)):
    """Authenticate as Guest for instant evaluator testing without Google config."""
    guest_email = "guest@melooha.ai"
    user = db.query(User).filter(User.email == guest_email).first()

    if not user:
        user = User(
            name=payload.name or "Akshat",
            email=guest_email,
            auth_provider="guest"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        topup_credits(
            db=db,
            user_id=user.id,
            count=5,
            idempotency_key=f"guest_{user.id}",
            description="Guest Welcome Bonus",
        )

    all_profiles = (
        db.query(BirthProfile)
        .filter(BirthProfile.user_id == user.id)
        .order_by(BirthProfile.created_at.asc())
        .all()
    )

    birth_profile = all_profiles[-1] if all_profiles else None

    chart_facts = None
    if birth_profile:
        chart_record = db.query(Chart).filter(Chart.birth_profile_id == birth_profile.id).first()
        if chart_record and chart_record.facts_json:
            chart_facts = chart_record.facts_json

    balance = get_balance(db, user.id)

    profiles_data = [
        {
            "id": p.id,
            "user_id": p.user_id,
            "name": p.name,
            "place_name": p.place_name,
            "birth_date": str(p.birth_date),
            "birth_time": p.birth_time,
            "time_known": p.time_known,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "timezone_str": p.timezone_str,
        }
        for p in all_profiles
    ]

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": None,
            "auth_provider": "guest",
        },
        "profile": {
            "id": birth_profile.id,
            "user_id": user.id,
            "name": birth_profile.name,
            "place_name": birth_profile.place_name,
            "birth_date": str(birth_profile.birth_date),
            "birth_time": birth_profile.birth_time,
            "time_known": birth_profile.time_known,
            "latitude": birth_profile.latitude,
            "longitude": birth_profile.longitude,
            "timezone_str": birth_profile.timezone_str,
        } if birth_profile else None,
        "profiles": profiles_data,
        "chart_facts": chart_facts,
        "balance": balance,
        "is_new_user": False,
    }
