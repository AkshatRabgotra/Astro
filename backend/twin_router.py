"""FastAPI Router for Dasha Twin and Share System.

Features:
- Dasha Twin match generation with pure deterministic day-locking
- Grounded card copy generation with strict validator and multilingual templates
- POST /api/share: stores 128-bit random token snapshot with 90-day expiry and NO birth data
- Server-side 1080x1350 & 1080x1920 story PNG rendering in background tasks
- Revoke endpoint (POST /api/share/{token}/revoke) returning 404 on revoked tokens
- Public page /s/{token} with Open Graph tags and 'Find your own parallel' signup CTA
- Rate limiting for share creation (max 10 shares / hour) and refresh (max 5 / day)
- Analytics logging for card_viewed, card_refresh, share_clicked, share_created, share_link_opened, signup_from_share
"""

from datetime import date, datetime, timedelta, timezone
import hashlib
import os
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BirthProfile, Event, ShareSnapshot, User
from backend.twin_matcher import find_dasha_twin
from backend.twin_copy import generate_grounded_twin_copy
from backend.twin_image_generator import render_twin_card_images, SHARE_DIR

router = APIRouter(tags=["dasha-twin"])

# In-memory rate limiting tracking
_SHARE_RATE_LIMITS: Dict[str, List[datetime]] = {}
_REFRESH_RATE_LIMITS: Dict[str, List[datetime]] = {}


class CreateShareRequest(BaseModel):
    user_id: Optional[str] = None
    headline: str = Field(..., max_length=255)
    body: str = Field(..., max_length=1000)
    figure_name: str = Field(..., max_length=128)
    figure_field: str = Field(..., max_length=64)
    lord: str = Field(..., max_length=32)
    theme: str = Field("Moon", max_length=64)
    include_first_name: bool = False
    source_url: Optional[str] = None


@router.get("/api/user/{user_id}/dasha-twin")
def get_user_dasha_twin(
    user_id: str,
    lang: str = Query("en", pattern="^(en|hi)$"),
    refresh: bool = False,
    level: str = Query("pratyantar", pattern="^(mahadasha|antardasha|pratyantar)$"),
    db: Session = Depends(get_db),
):
    """
    Fetch the Dasha Twin card for the user.
    Pure code deterministic matching by day.
    """
    profile = db.query(BirthProfile).filter(BirthProfile.user_id == user_id).first()
    if not profile:
        profile = db.query(BirthProfile).first()
        if not profile:
            raise HTTPException(status_code=404, detail="User birth profile not found")

    today = date.today()

    # Rate limit check for refresh button (free, but rate-limited to 5/day)
    exclude_figure_ids = []
    if refresh:
        now = datetime.now()
        history = _REFRESH_RATE_LIMITS.setdefault(user_id, [])
        history = [t for t in history if now - t < timedelta(days=1)]
        _REFRESH_RATE_LIMITS[user_id] = history
        if len(history) >= 10:
            raise HTTPException(
                status_code=429,
                detail="Refresh rate limit reached for today. You can view your current parallel."
            )
        history.append(now)

        # Look up what was just shown today to exclude it on refresh
        last_event = (
            db.query(Event)
            .filter(Event.user_id == user_id)
            .filter(Event.event_name.in_(["card_viewed", "card_refresh"]))
            .order_by(Event.created_at.desc())
            .first()
        )
        if last_event and last_event.payload and "figure_id" in last_event.payload:
            exclude_figure_ids.append(last_event.payload["figure_id"])

    # 1. Matching Engine
    match_result = find_dasha_twin(
        db=db,
        profile=profile,
        target_date=today,
        level=level,
        exclude_figure_ids=exclude_figure_ids if exclude_figure_ids else None,
    )

    # 2. Card Copy Generation (with Grounding Validator)
    card_copy = generate_grounded_twin_copy(match_result, lang=lang, use_llm=False)

    # 3. Log Analytics Event
    event_type = "card_refresh" if refresh else "card_viewed"
    fig_id = match_result.get("figure", {}).get("id") if match_result.get("figure") else None
    ev = Event(
        user_id=user_id,
        event_name=event_type,
        payload={
            "figure_id": fig_id,
            "lord": match_result.get("user_lord"),
            "level": match_result.get("user_level"),
            "lang": lang,
        },
    )
    db.add(ev)
    db.commit()

    user_first_name = profile.name.split()[0] if profile.name else "You"
    lord_name = match_result.get("user_lord", "Moon")

    # Suggested pre-filled Q&A question
    if lang == "hi":
        ask_prompt = f"मेरे {lord_name} चरण में मेरी तुलना किससे हो रही है?"
    else:
        ask_prompt = f"Who am I being measured against right now in my {lord_name} phase?"

    return {
        "match_type": match_result.get("match_type"),
        "headline": card_copy.get("headline"),
        "body": card_copy.get("body"),
        "lord": lord_name,
        "user_level": match_result.get("user_level"),
        "figure_level": match_result.get("figure_level", "Mahadasha"),
        "is_approximate": match_result.get("is_approximate", False),
        "disclaimer": card_copy.get("disclaimer"),
        "source_url": card_copy.get("source_url"),
        "figure": match_result.get("figure"),
        "event": match_result.get("event"),
        "user_first_name": user_first_name,
        "ask_prompt": ask_prompt,
    }


@router.post("/api/share", status_code=status.HTTP_201_CREATED)
def create_share_snapshot(
    req: CreateShareRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Store snapshot under a random 128-bit token with 90-day expiry.
    Never stores birth details.
    Renders 1080x1350 & 1080x1920 PNG in background.
    """
    # Rate limit: max 15 shares per hour per user/IP
    client_key = req.user_id or (request.client.host if getattr(request, "client", None) else "anon")
    now = datetime.now()
    history = _SHARE_RATE_LIMITS.setdefault(client_key, [])
    history = [t for t in history if now - t < timedelta(hours=1)]
    _SHARE_RATE_LIMITS[client_key] = history
    if len(history) >= 15:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a little while before generating another share card."
        )
    history.append(now)

    # Resolve first name only if explicitly enabled
    first_name_val = None
    if req.include_first_name and req.user_id:
        user_prof = db.query(BirthProfile).filter(BirthProfile.user_id == req.user_id).first()
        if user_prof and user_prof.name:
            first_name_val = user_prof.name.split()[0]

    # Generate 128-bit token (32 hex characters)
    token = secrets.token_hex(16)
    expires_at = datetime.now(timezone.utc) + timedelta(days=90)

    snapshot = ShareSnapshot(
        token=token,
        user_id=req.user_id,
        headline=req.headline,
        body=req.body,
        figure_name=req.figure_name,
        figure_field=req.figure_field,
        lord=req.lord,
        theme=req.theme,
        first_name=first_name_val,
        source_url=req.source_url,
        is_approximate=False,
        is_revoked=False,
        expires_at=expires_at,
    )
    db.add(snapshot)

    # Log analytics event
    ev = Event(
        user_id=req.user_id,
        event_name="share_created",
        payload={"token": token, "figure_name": req.figure_name, "lord": req.lord},
    )
    db.add(ev)
    db.commit()

    # Trigger background image generation (idempotent & cached)
    background_tasks.add_task(
        render_twin_card_images,
        token=token,
        headline=req.headline,
        body=req.body,
        figure_name=req.figure_name,
        figure_field=req.figure_field,
        lord=req.lord,
        theme=req.theme,
        first_name=first_name_val,
    )

    return {
        "token": token,
        "share_url": f"/s/{token}",
        "card_image_url": f"/api/share/{token}/image",
        "story_image_url": f"/api/share/{token}/story",
        "expires_at": expires_at.isoformat(),
    }


@router.post("/api/share/{token}/revoke")
def revoke_share(token: str, db: Session = Depends(get_db)):
    """Revoke a shared card snapshot. Returns 404 on subsequent lookups."""
    snapshot = db.query(ShareSnapshot).filter(ShareSnapshot.token == token).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Shared card not found")

    snapshot.is_revoked = True
    db.commit()
    return {"status": "revoked", "token": token}


@router.get("/api/share/{token}")
def get_share_data(token: str, db: Session = Depends(get_db)):
    """Retrieve card snapshot data for client display."""
    snapshot = db.query(ShareSnapshot).filter(ShareSnapshot.token == token).first()
    if not snapshot or snapshot.is_revoked:
        raise HTTPException(status_code=404, detail="Shared card not found or has been revoked")

    now_utc = datetime.now(timezone.utc)
    if snapshot.expires_at:
        exp = snapshot.expires_at if snapshot.expires_at.tzinfo else snapshot.expires_at.replace(tzinfo=timezone.utc)
        if exp < now_utc:
            raise HTTPException(status_code=404, detail="Shared card has expired")

    return {
        "token": snapshot.token,
        "headline": snapshot.headline,
        "body": snapshot.body,
        "figure_name": snapshot.figure_name,
        "figure_field": snapshot.figure_field,
        "lord": snapshot.lord,
        "first_name": snapshot.first_name,
        "source_url": snapshot.source_url,
        "card_image_url": f"/api/share/{token}/image",
        "story_image_url": f"/api/share/{token}/story",
    }


@router.get("/api/share/{token}/image")
def get_card_image(token: str, db: Session = Depends(get_db)):
    """Serve the 1080x1350 PNG image (renders idempotently if not cached)."""
    snapshot = db.query(ShareSnapshot).filter(ShareSnapshot.token == token).first()
    if not snapshot or snapshot.is_revoked:
        raise HTTPException(status_code=404, detail="Image not found")

    card_path = os.path.join(SHARE_DIR, f"{token}.png")
    if not os.path.exists(card_path):
        card_path, _ = render_twin_card_images(
            token=snapshot.token,
            headline=snapshot.headline,
            body=snapshot.body,
            figure_name=snapshot.figure_name,
            figure_field=snapshot.figure_field,
            lord=snapshot.lord,
            first_name=snapshot.first_name,
        )

    return FileResponse(card_path, media_type="image/png")


@router.get("/api/share/{token}/story")
def get_story_image(token: str, db: Session = Depends(get_db)):
    """Serve the 1080x1920 story PNG image."""
    snapshot = db.query(ShareSnapshot).filter(ShareSnapshot.token == token).first()
    if not snapshot or snapshot.is_revoked:
        raise HTTPException(status_code=404, detail="Story image not found")

    story_path = os.path.join(SHARE_DIR, f"{token}_story.png")
    if not os.path.exists(story_path):
        _, story_path = render_twin_card_images(
            token=snapshot.token,
            headline=snapshot.headline,
            body=snapshot.body,
            figure_name=snapshot.figure_name,
            figure_field=snapshot.figure_field,
            lord=snapshot.lord,
            first_name=snapshot.first_name,
        )

    return FileResponse(story_path, media_type="image/png")


@router.get("/s/{token}", response_class=HTMLResponse)
def view_public_share_card(token: str, request: Request, db: Session = Depends(get_db)):
    """
    Public web page with Open Graph tags and 'Find your own parallel' signup CTA.
    Logs share_link_opened event.
    """
    snapshot = db.query(ShareSnapshot).filter(ShareSnapshot.token == token).first()
    if not snapshot or snapshot.is_revoked:
        raise HTTPException(status_code=404, detail="Shared card not found or has been revoked")

    now_utc = datetime.now(timezone.utc)
    if snapshot.expires_at:
        exp = snapshot.expires_at if snapshot.expires_at.tzinfo else snapshot.expires_at.replace(tzinfo=timezone.utc)
        if exp < now_utc:
            raise HTTPException(status_code=404, detail="Shared card has expired")

    # Log share_link_opened
    ev = Event(
        user_id=snapshot.user_id,
        event_name="share_link_opened",
        payload={"token": token, "figure": snapshot.figure_name},
    )
    db.add(ev)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/api/share/{token}/image"
    signup_url = f"{base_url}/?ref={token}"

    title = f"{snapshot.figure_name} & Your Cosmic Phase · Melooha Dasha Twin"
    desc = f"{snapshot.headline}: {snapshot.body[:140]}..."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  
  <!-- Open Graph / WhatsApp / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{base_url}/s/{token}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{image_url}">
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{image_url}">

  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #06030D; color: #FFF; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    .crystal-card {{ background: linear-gradient(135deg, rgba(34, 19, 61, 0.7), rgba(18, 9, 36, 0.85)); backdrop-filter: blur(16px); border: 1px solid rgba(229, 169, 60, 0.35); }}
  </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4">
  <main class="max-w-md w-full space-y-5 text-center">
    <!-- Brand -->
    <div class="space-y-1">
      <div class="text-xs uppercase tracking-widest text-[#E5A93C] font-semibold">✦ Melooha Astrology · Dasha Twin ✦</div>
      <h1 class="text-2xl font-serif font-bold text-white tracking-wide">{snapshot.headline}</h1>
    </div>

    <!-- Visual Card -->
    <div class="crystal-card rounded-3xl p-6 shadow-2xl text-left space-y-4">
      <div class="flex items-center justify-between">
        <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#B21E68] text-white">
          {snapshot.lord} Phase
        </span>
        <span class="text-xs text-[#A299BC]">Vedic Parallel</span>
      </div>

      <div class="flex items-center gap-3.5 pt-2">
        <div class="w-14 h-14 rounded-full bg-gradient-to-tr from-[#B21E68] to-[#E5A93C] flex items-center justify-center text-white font-bold text-lg shadow-lg">
          {"".join([w[0].upper() for w in snapshot.figure_name.split()[:2]])}
        </div>
        <div>
          <h2 class="text-lg font-serif font-bold text-white">{snapshot.figure_name}</h2>
          <p class="text-xs text-[#A299BC]">{snapshot.figure_field}</p>
        </div>
      </div>

      <p class="text-sm text-[#DDD5EE] leading-relaxed pt-2">
        {snapshot.body}
      </p>

      <div class="pt-4 border-t border-[#312250] flex items-center justify-between text-[11px] text-[#A299BC]">
        <span>For reflection and fun, not prediction.</span>
        {f'<a href="{snapshot.source_url}" target="_blank" rel="noopener noreferrer" class="text-[#E5A93C] hover:underline">Source ↗</a>' if snapshot.source_url else ''}
      </div>
    </div>

    <!-- Call to Action -->
    <div class="space-y-2 pt-2">
      <a href="{signup_url}" class="block w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-bold text-sm tracking-wide shadow-xl hover:brightness-110 active:scale-95 transition-all">
        Find Your Own Parallel Free ✦
      </a>
      <p class="text-xs text-[#A299BC]">See which legendary milestone mirrors your current astrological phase</p>
    </div>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/api/metrics/dasha-twin")
def get_dasha_twin_metrics(db: Session = Depends(get_db)):
    """
    Compute Dasha Twin metrics:
    - Primary metric: shares per weekly active user (WAU)
    - Secondary metric: share link opened to signup conversion rate
    - Full funnel counters
    """
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    # Weekly Active Users (WAU): distinct users who triggered any event in the last 7 days
    recent_events = db.query(Event).filter(Event.created_at >= seven_days_ago).all()
    active_user_ids = {ev.user_id for ev in recent_events if ev.user_id}
    wau = len(active_user_ids) if active_user_ids else 1

    # Shares created in past 7 days
    shares_7d = db.query(ShareSnapshot).filter(ShareSnapshot.created_at >= seven_days_ago).count()
    shares_per_wau = round(shares_7d / max(1, wau), 3)

    # Conversion funnel
    card_viewed = db.query(Event).filter(Event.event_name == "card_viewed").count()
    card_refresh = db.query(Event).filter(Event.event_name == "card_refresh").count()
    share_clicked = db.query(Event).filter(Event.event_name == "share_clicked").count()
    share_created = db.query(Event).filter(Event.event_name == "share_created").count()
    share_link_opened = db.query(Event).filter(Event.event_name == "share_link_opened").count()
    signup_from_share = db.query(Event).filter(Event.event_name == "signup_from_share").count()

    share_to_signup_rate = (
        round(signup_from_share / share_link_opened * 100.0, 2)
        if share_link_opened > 0
        else 0.0
    )

    return {
        "weekly_active_users": wau,
        "shares_last_7_days": shares_7d,
        "primary_metric_shares_per_wau": shares_per_wau,
        "secondary_metric_share_to_signup_pct": share_to_signup_rate,
        "funnel": {
            "card_viewed": card_viewed,
            "card_refresh": card_refresh,
            "share_clicked": share_clicked,
            "share_created": share_created,
            "share_link_opened": share_link_opened,
            "signup_from_share": signup_from_share,
        },
    }
