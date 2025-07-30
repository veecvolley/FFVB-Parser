from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from datetime import datetime
import io
from PIL import Image, ImageDraw

from main import generate_filtered_image

# ---- CONFIG ----
CATEGORIES = {
    #"PVA": "Volley-Assis",
    "1MB": "SM1 - Masculin",
    "2FC": "SF1 - Féminin"
}

VERSION = open("VERSION.md", encoding="utf-8").readline().strip()

# ---- FastAPI APP ----
app = FastAPI()

app.mount("/static", StaticFiles(directory="_img"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>VEEC - Comm' Generator</title>
    <link rel="icon" type="image/png" href="/static/favicon.png">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        html, body {{
            height: 100%;
        }}
        body {{
            font-family: Arial, sans-serif;
            background: #f9f9fa;
            padding: 22px;
            min-height: 100vh;
        }}
        .container-flex {{
            display: flex;
            justify-content: center;
            gap: 2em;
            align-items: flex-start;
            max-width: 1100px;
            margin: auto;
        }}
        .form-card {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 2px 14px #ddd;
            padding: 2em;
            min-width: 300px;
            max-width: 500px;
            flex: 1 1 320px;
        }}
        .image-holder {{
            text-align: center;
            margin-top: 0.5em;
            background: white;
            border-radius: 20px;
            box-shadow: 0 2px 14px #ddd;
            padding: 1em 1em 1.5em 1em;
            min-width: 250px;
            max-width: 600px;
            flex: 1 1 350px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            min-height: 220px;
        }}
        #resultImg {{
            max-width: 100%;
            max-height: 55vw;
            box-shadow: 0 2px 16px #ccc;
            border-radius: 16px;
            display: none;
            cursor: zoom-in;
        }}
        h1 {{
            color: #0083d1;
            display: inline-block;
            vertical-align: middle;
            margin-left: 0.5em;
            font-size: 2em;
        }}
        .main-logo {{
            height: 48px;
            vertical-align: middle;
            margin-right: 0.7em;
            margin-bottom: 8px;
            display: inline-block;
        }}
        label {{
            font-weight: bold;
        }}
        .row {{
            margin-bottom: 1.2em;
        }}
        select, input[type=date] {{
            padding: 0.4em;
            font-size: 1em;
        }}
        button {{
            padding: 0.6em 1.3em;
            font-size: 1em;
            background: #0083d1;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        button:hover {{
            background: #005fa3;
        }}
        #loading {{
            display: none;
        }}
        .dates-row {{
            display: flex;
            gap: 1em;
            align-items: flex-end;
        }}
        .date-col {{
            display: flex;
            flex-direction: column;
            flex: 1 1 0;
        }}
        #versionInfo {{
            color: #999;
            font-size: 0.7em;
            text-align: center;
            margin: 0 0 12px 0;
            position: fixed;
            left: 0;
            right: 0;
            bottom: 8px;
            z-index: 99;
            pointer-events: none;
            user-select: none;
            letter-spacing: 0.03em;
        }}
        /* Lightbox Modal styles */
        #imgModal {{
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0; top: 0; width: 100vw; height: 100vh;
            background: rgba(10,16,25,0.88);
            align-items: center; justify-content: center;
            transition: background 0.2s;
        }}
        #imgModal img {{
            max-width: 96vw;
            max-height: 88vh;
            border-radius: 15px;
            box-shadow: 0 2px 28px #000a;
            background: #fff;
        }}
        #imgModalClose {{
            position: absolute;
            top: 28px;
            right: 44px;
            font-size: 2.2em;
            font-weight: bold;
            color: #fff;
            cursor: pointer;
            user-select: none;
            z-index: 2;
            text-shadow: 0 2px 12px #000c;
        }}
        #imgModal:hover #imgModalClose {{ color: #fff; }}

        @media (max-width: 900px) {{
            .container-flex {{
                flex-direction: column;
                gap: 1.2em;
                align-items: stretch;
            }}
            .image-holder, .form-card {{
                min-width: 0;
                max-width: 100%;
                margin-left: 0; margin-right: 0;
                padding-left: 0.5em; padding-right: 0.5em;
            }}
            h1 {{ font-size: 1.25em; }}
            .main-logo {{ height: 32px; margin-bottom: 4px; }}
        }}
        @media (max-width: 600px) {{
            body {{ padding: 6px; }}
            .form-card {{ padding: 1em 0.7em; }}
            .image-holder {{ padding: 0.5em 0.3em 1em 0.3em; }}
            .row {{ margin-bottom: 0.7em; }}
            #resultImg {{ max-height: 38vw; }}
            #imgModal img {{ max-width: 99vw; max-height: 76vh; }}
            #imgModalClose {{ top:10px; right:16px; font-size:1.4em;}}
        }}
        @media (max-width: 440px) {{
            .dates-row {{ flex-direction: column; gap: 0.3em; }}
            .date-col {{ width: 100%; }}
            .form-card {{ min-width: 0; }}
            .image-holder {{ min-width: 0; }}
        }}
    </style>
</head>
<body>
    <div class="container-flex">
        <div class="form-card">
            <!-- Logo juste avant le titre -->
            <div style="display: flex; align-items: center; margin-bottom: 0.7em;">
                <img src="/static/logo.png"
                     id="mainLogo" class="main-logo"
                     alt="Logo"
                     >
                <h1>Comm' Generator</h1>
            </div>
            <form id="filterForm">
                <div class="row">
                    <label for="custom_title">Titre :</label><br>
                    <input type="text" id="custom_title" name="custom_title" style="width:100%;" placeholder="Ex: Week-end de Matchs !!">
                </div>
                <div class="row">
                    <label>Format :</label><br>
                    <label><input type="radio" name="format" value="pub" checked> Publication</label>
                    <label style="margin-left:1.2em;"><input type="radio" name="format" value="story"> Story</label>
                </div>
                <div class="row">
                    <label for="categories">Catégories :</label><br>
                    <select id="categories" name="categories" multiple size="3" style="width:100%;"></select>
                </div>
                <div class="row dates-row">
                    <div class="date-col">
                        <label for="date_start">Date début :</label>
                        <input type="date" id="date_start" name="date_start">
                    </div>
                    <div class="date-col">
                        <label for="date_end">Date fin :</label>
                        <input type="date" id="date_end" name="date_end">
                    </div>
                </div>
                <div class="row">
                    <button type="submit">Générer l'image</button>
                    <span id="loading">⏳ Génération...</span>
                </div>
            </form>
        </div>
        <div class="image-holder">
            <img id="resultImg" src="" alt="Image générée">
        </div>
        <div id="versionInfo"></div>
    </div>

    <!-- Lightbox modal -->
    <div id="imgModal" style="display:none;">
        <span id="imgModalClose">&times;</span>
        <img id="imgModalContent" src="" alt="Agrandissement" />
    </div>

<script>
const APP_VERSION = "{VERSION}";

document.addEventListener("DOMContentLoaded", async function(){{
    // --- Calcul automatique samedi/dimanche de la semaine courante ---
    function getWeekendDates() {{
        const now = new Date();
        const day = now.getDay();
        const monday = new Date(now);
        monday.setDate(now.getDate() - ((day + 6) % 7));
        const saturday = new Date(monday);
        saturday.setDate(monday.getDate() + 5);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        function fmt(d) {{ return d.toISOString().slice(0,10); }}
        return {{ saturday: fmt(saturday), sunday: fmt(sunday) }};
    }}
    const weekend = getWeekendDates();
    document.getElementById("date_start").value = weekend.saturday;
    document.getElementById("date_end").value = weekend.sunday;

    fetch("/categories").then(r=>r.json()).then(cats=>{{
        const sel = document.getElementById("categories");
        Object.entries(cats).forEach(([val, label]) => {{
            let opt = document.createElement("option");
            opt.value = val; opt.text = label;
            sel.add(opt);
        }});
    }});

    document.getElementById("filterForm").onsubmit = async function(e){{
        e.preventDefault();
        document.getElementById("loading").style.display = "inline";
        document.getElementById("resultImg").style.display = "none";
        let title = document.getElementById("custom_title").value;
        let format = document.querySelector('input[name="format"]:checked').value;
        let cats = Array.from(document.getElementById("categories").selectedOptions).map(opt=>opt.value);
        let date_start = document.getElementById("date_start").value;
        let date_end   = document.getElementById("date_end").value;
        let url = "/image?"+cats.map(c=>"categories="+encodeURIComponent(c)).join("&");
        if (title) url += "&title=" + encodeURIComponent(title);
        if (format) url += "&format=" + encodeURIComponent(format);
        if(date_start) url += "&date_start=" + encodeURIComponent(date_start);
        if(date_end) url += "&date_end=" + encodeURIComponent(date_end);

        fetch(url).then(r => r.blob()).then(blob => {{
            let imgUrl = URL.createObjectURL(blob);
            let img = document.getElementById("resultImg");
            img.src = imgUrl;
            img.style.display = "block";
            document.getElementById("loading").style.display = "none";
        }});
    }};
    document.getElementById("versionInfo").textContent = "Version : " + APP_VERSION;

    // --- Modal/lightbox pour agrandir l'image ---
    document.getElementById("resultImg").onclick = function() {{
        if(this.src && this.style.display !== "none") {{
            document.getElementById("imgModalContent").src = this.src;
            document.getElementById("imgModal").style.display = "flex";
        }}
    }};
    document.getElementById("imgModalClose").onclick = function() {{
        document.getElementById("imgModal").style.display = "none";
    }};
    document.getElementById("imgModal").onclick = function(e) {{
        if(e.target === this) {{
            document.getElementById("imgModal").style.display = "none";
        }}
    }};
}});
</script>
</body>
</html>
"""

@app.get("/categories", response_class=JSONResponse)
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
