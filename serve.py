from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from datetime import datetime
import io
from PIL import Image, ImageDraw

from main import generate_filtered_image

CATEGORIES = {
    "1MB": "SM1 - Masculin",
    "2FC": "SF1 - Féminin"
}

VERSION = open("VERSION.md", encoding="utf-8").readline().strip()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=StreamingResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": VERSION})

@app.get("/categories")
def categories():
    return CATEGORIES

@app.get("/image")
def image(
    title: Optional[str] = None,
    format: Optional[str] = "pub",
    categories: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
):
    img = generate_filtered_image(categories, date_start, date_end, title, format)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
