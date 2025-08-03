
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from app.services.image_gen import generate_filtered_image
#from app.core.constants import CATEGORIES
import io
import pathlib
from app.core.templates import templates
from app.core.config import settings

VERSION = open(pathlib.Path(__file__).parents[2] / "VERSION.md", encoding="utf-8").readline().strip()

router = APIRouter()

@router.get("/", response_class=StreamingResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": VERSION})

@router.get("/categories")
def categories():
    return settings.labels

@router.get("/image")
def image(
    mode: Optional[str] = "planning",
    title: Optional[str] = None,
    format: Optional[str] = "pub",
    categories: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
):
    img = generate_filtered_image(categories, date_start, date_end, title, format, mode)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
