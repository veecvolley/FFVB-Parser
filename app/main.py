from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
import pathlib

app = FastAPI()
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.include_router(router)
