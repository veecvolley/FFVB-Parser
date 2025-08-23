from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List
from app.services.image_gen import generate_filtered_image
from app.services.seasons import generate_config_seasons
# from app.core.constants import CATEGORIES
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
def categories(saison: str = Query(..., description="Saison au format YYYY-YYYY (ou YYYY/YYYY)")):
    # Normalisation pour supporter les deux séparateurs
    s = saison.strip()
    seasons = getattr(settings, "saisons", {}) or {}
    cats = (
        seasons.get(s) or
        seasons.get(s.replace("/", "-")) or
        seasons.get(s.replace("-", "/"))
    )

    if not cats:
        return JSONResponse(
            status_code=404,
            content={"error": f"Saison '{saison}' non trouvée"}
        )
    return cats

@router.get("/image")
def image(
    saison: Optional[str] = "2025/2026",
    mode: Optional[str] = "planning",
    title: Optional[str] = "Matchs",
    format: Optional[str] = "pub",
    categories: Optional[List[str]] = Query(None),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
):
    print(f"{mode}")
    print(f"{saison}")
    print(f"{categories}")
    img = generate_filtered_image(categories, date_start, date_end, title, format, mode, saison)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@router.post("/update-config")
def update_config():
    try:
        generate_config_seasons(club_id, club_saisons, "saisons.yaml")
        return {"message": "Configuration mise à jour avec succès."}
    except Exception as e:
        return {"message": f"Erreur : {e}"}