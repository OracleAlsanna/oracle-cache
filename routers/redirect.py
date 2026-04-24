from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

import db
from cache import get_cached_url, set_cached_url
from limiter import check_rate_limit

router = APIRouter(tags=["redirect"])

_TOO_MANY = JSONResponse(
    status_code=429,
    content={"detail": "Too many requests. Please slow down."},
)


@router.get("/{code}")
def redirect(code: str, request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(ip, "redirect", 60):
        return _TOO_MANY

    clicked_at = datetime.now(timezone.utc).isoformat()
    referrer: Optional[str] = request.headers.get("referer") or request.headers.get("referrer")
    user_agent: Optional[str] = request.headers.get("user-agent")

    cached_url = get_cached_url(code)
    if cached_url:
        background_tasks.add_task(db.insert_click, code, clicked_at, referrer, user_agent)
        return RedirectResponse(url=cached_url, status_code=307)

    row = db.get_by_code(code)
    if not row:
        raise HTTPException(status_code=404, detail=f"No link found for code '{code}'")

    set_cached_url(code, row["original_url"])
    background_tasks.add_task(db.insert_click, code, clicked_at, referrer, user_agent)
    return RedirectResponse(url=row["original_url"], status_code=307)
