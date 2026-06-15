from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

import db
from limiter import check_rate_limit
from models import ClickCountResponse, ClickEventResponse, LinkAnalyticsResponse, RecentClickResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

_TOO_MANY = JSONResponse(
    status_code=429,
    content={"detail": "Too many requests. Please slow down."},
)


@router.get("/recent", response_model=list[RecentClickResponse])
def recent_clicks():
    rows = db.get_recent_clicks(limit=50)
    return [
        RecentClickResponse(code=r["code"], clicked_at=r["clicked_at"], referrer=r["referrer"])
        for r in rows
    ]


@router.get("", response_model=list[ClickCountResponse])
def all_click_counts(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(ip, "analytics", 30):
        return _TOO_MANY

    rows = db.get_all_click_counts()
    return [
        ClickCountResponse(code=r["code"], url=r["url"], click_count=r["click_count"])
        for r in rows
    ]


@router.get("/{code}", response_model=LinkAnalyticsResponse)
def link_analytics(code: str):
    link = db.get_by_code(code)
    if not link:
        raise HTTPException(status_code=404, detail=f"No link found for code '{code}'")

    click_count = db.get_click_count_by_code(code)
    clicks = db.get_clicks_by_code(code)

    return LinkAnalyticsResponse(
        code=code,
        url=link["original_url"],
        click_count=click_count,
        recent_clicks=[
            ClickEventResponse(
                clicked_at=c["clicked_at"],
                referrer=c["referrer"],
                user_agent=c["user_agent"],
            )
            for c in clicks
        ],
    )
