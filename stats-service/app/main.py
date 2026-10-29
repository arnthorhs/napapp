import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

nap_service = httpx.Client(base_url=os.environ["NAP_SERVICE_URL"], timeout=3)

app = FastAPI(title="stats-service")


class Stats(BaseModel):
    child_id: str
    days: int
    nap_count: int
    average_minutes: float | None
    daily_minutes: float


@app.get("/stats/{child_id}")
def get_stats(child_id: str, days: Annotated[int, Query(ge=1, le=365)] = 7) -> Stats:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_text = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        response = nap_service.get(
            "/naps", params={"child_id": child_id, "since": since_text}
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="nap-service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="nap-service unavailable")

    naps = response.json()

    nap_count = 0
    total_minutes = 0
    for nap in naps:
        if nap["end"] is None:
            continue
        start = datetime.fromisoformat(nap["start"])
        end = datetime.fromisoformat(nap["end"])
        length = end - start
        total_minutes = total_minutes + length.total_seconds() / 60
        nap_count = nap_count + 1

    if nap_count == 0:
        average = None
    else:
        average = round(total_minutes / nap_count, 1)

    daily = round(total_minutes / days, 1)

    return Stats(
        child_id=child_id,
        days=days,
        nap_count=nap_count,
        average_minutes=average,
        daily_minutes=daily,
    )
