import os
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

NAP_SERVICE_URL = os.environ["NAP_SERVICE_URL"]
STATS_SERVICE_URL = os.environ["STATS_SERVICE_URL"]

http = httpx.AsyncClient(timeout=5)

app = FastAPI(title="web")


async def forward(request: Request, url: str) -> Response:
    body = await request.body()

    try:
        response = await http.request(
            request.method,
            url,
            params=dict(request.query_params),
            content=body,
            headers={"Content-Type": "application/json"},
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="service unavailable")

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("Content-Type"),
    )


@app.get("/api/naps")
async def list_naps(request: Request):
    return await forward(request, NAP_SERVICE_URL + "/naps")


@app.post("/api/naps")
async def create_nap(request: Request):
    return await forward(request, NAP_SERVICE_URL + "/naps")


@app.post("/api/naps/{nap_id}")
async def end_nap(nap_id: str, request: Request):
    return await forward(request, NAP_SERVICE_URL + "/naps/" + quote(nap_id, safe=""))


@app.delete("/api/naps/{nap_id}")
async def delete_nap(nap_id: str, request: Request):
    return await forward(request, NAP_SERVICE_URL + "/naps/" + quote(nap_id, safe=""))


@app.get("/api/stats/{child_id}")
async def get_stats(child_id: str, request: Request):
    return await forward(
        request, STATS_SERVICE_URL + "/stats/" + quote(child_id, safe="")
    )


app.mount("/", StaticFiles(directory="static", html=True), name="static")
