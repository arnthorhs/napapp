import os
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

client = MongoClient(
    os.environ["MONGO_URL"], tz_aware=True, serverSelectionTimeoutMS=3000
)
naps = client["napapp"]["naps"]

app = FastAPI(title="nap-service")


@app.exception_handler(ConnectionFailure)
def database_unavailable(request: Request, exc: ConnectionFailure):
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


class NapCreate(BaseModel):
    child_id: str
    start: AwareDatetime
    end: AwareDatetime | None = None


class NapUpdate(BaseModel):
    end: AwareDatetime


class Nap(BaseModel):
    id: str
    child_id: str
    start: datetime
    end: datetime | None


def document_to_nap_obj(doc) -> Nap:
    return Nap(
        id=str(doc["_id"]), child_id=doc["child_id"], start=doc["start"], end=doc["end"]
    )


@app.post("/naps", status_code=201)
def create_nap(nap: NapCreate) -> Nap:
    if nap.child_id == "":
        raise HTTPException(status_code=422, detail="child_id must not be empty")
    if nap.end is not None and nap.end <= nap.start:
        raise HTTPException(status_code=422, detail="end must be after start")

    doc = {"child_id": nap.child_id, "start": nap.start, "end": nap.end}
    result = naps.insert_one(doc)

    saved = naps.find_one({"_id": result.inserted_id})
    return document_to_nap_obj(saved)


@app.get("/naps")
def list_naps(child_id: str, since: AwareDatetime | None = None) -> list[Nap]:
    query = {"child_id": child_id}
    if since is not None:
        query["start"] = {"$gte": since}

    result = []
    for doc in naps.find(query).sort("start", -1):
        result.append(document_to_nap_obj(doc))
    return result


@app.post("/naps/{nap_id}")
def end_nap(nap_id: str, update: NapUpdate) -> Nap:
    try:
        doc = naps.find_one({"_id": ObjectId(nap_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Nap not found")
    if doc is None:
        raise HTTPException(status_code=404, detail="Nap not found")
    if update.end <= doc["start"]:
        raise HTTPException(status_code=422, detail="end must be after start")

    naps.update_one({"_id": doc["_id"]}, {"$set": {"end": update.end}})

    saved = naps.find_one({"_id": doc["_id"]})
    return document_to_nap_obj(saved)


@app.delete("/naps/{nap_id}", status_code=204)
def delete_nap(nap_id: str):
    try:
        result = naps.delete_one({"_id": ObjectId(nap_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Nap not found")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nap not found")
    return Response(status_code=204)
