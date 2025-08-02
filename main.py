import csv
import requests
import re
import textwrap
import io
import pdfplumber
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime

#== Configuration ======================================================

jours = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
mois = {"January": "janvier", "February": "février", "March": "mars", "April": "avril", "May": "mai", "June": "juin", "July": "juillet", "August": "août", "September": "septembre", "October": "octobre", "November": "novembre", "December": "décembre"}
entities = {
    "LIIDF": "Championnat Régional",
    "ADPVA": "Championnat de France",
    "PTIDF77": "Championnat Départemental"
}
entities_str = ['LIIDF', 'ADPVA', 'PTIDF77']

categories = {
    "PVA": "Volley-Assis",
    "RMC": "Masculin",
    "RFD": "Féminin",
    "1MB": "Masculin",
    "2FC": "Féminin",
    "ARA": "Masculin",
    "ARF": "Féminin",
}

#== Functions ==========================================================

def get_gymnase_address(codmatch, codent):
    """
    Recupere l'adresse complète du Gymnase à partir du PDF du match
    
    codmatch : code du match
    codent : code de la ligue
    """
    url = "https://www.ffvbbeach.org/ffvbapp/adressier/fiche_match_ffvb.php"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'codmatch': codmatch, 'codent': codent}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200 or response.headers.get('Content-Type') != 'application/pdf':
        print("Erreur lors du téléchargement du PDF.")
        return None

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ''
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + '\n'

        # Extraction du bloc "Salle"
        match = re.search(r'Salle\s*\n(.*?)(Sol\s*:|Arbitre\.s|$)', text, re.DOTALL)
        if match:
            salle_block = match.group(1)
            lines = [line.strip() for line in salle_block.split('\n') if line.strip()]
            if lines:
                nom = lines[0]
                adresse = ' '.join(lines[1:])  # ou '\n'.join(lines[1:]) si tu préfères multi-lignes

                match_adr = re.search(r"(.+)\s(\d{5})\s(.+)", adresse)
                if match_adr:
                    rue = match_adr.group(1).strip().lower()
                    code_postal = match_adr.group(2)
                    ville = match_adr.group(3).strip()

                return {'nom': nom, 'rue': rue, 'code_postal': code_postal, 'ville': ville}
    return None

def paste_image_fit_box(
    background: Image.Image,
    overlay_path: str,
    box_x: int,
    box_y: int,
    box_width: int,
    box_height: int
):
    """
    Colle overlay_path sur background, la redimensionne pour la faire tenir dans un cadre (box_width x box_height)
    et centre l'image dans ce cadre.
    - background: PIL.Image (déjà ouverte)
    - overlay_path: chemin de l'image PNG à coller
    - box_x, box_y: coordonnées du coin haut-gauche du cadre dans background
    - box_width, box_height: dimensions maximales du cadre
    Retourne l'image modifiée (background)
    """
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size

    # Calcul du ratio d'ajustement pour tenir dans le cadre
    ratio = min(box_width / original_width, box_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    # Redimensionnement
    overlay = overlay.resize((new_width, new_height), Image.LANCZOS)

    # Calcul du décalage pour centrer dans le cadre
    decal_x = box_x + (box_width - new_width) // 2
    decal_y = box_y + (box_height - new_height) // 2

    # Collage avec la transparence
    background.paste(overlay, (decal_x, decal_y), overlay)
    return background

def paste_image_with_fixed_width(
    background: Image.Image,
    overlay_path: str,
    dest_x: int,
    dest_y: int,
    fixed_width: int
):
    """
    Colle overlay_path sur background en imposant la largeur (hauteur ajustée au ratio d'origine)
    - background: PIL.Image (déjà ouverte)
    - overlay_path: chemin de l'image PNG à coller
    - dest_x, dest_y: coordonnées où coller (coin haut-gauche du logo)
    - fixed_width: largeur en pixels à imposer pour l'overlay
    Retourne l'image modifiée (background)
    """
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size
    new_height = int(original_height * fixed_width / original_width)
    overlay = overlay.resize((fixed_width, new_height), Image.LANCZOS)
    background.paste(overlay, (dest_x, dest_y), overlay)
    return background

def paste_image_with_fixed_height(
    background: Image.Image,
    overlay_path: str,
    dest_x: int,
    dest_y: int,
    fixed_height: int
):
    """
    Colle overlay_path sur background en imposant la hauteur (largeur ajustée au ratio d'origine)
    - background: PIL.Image (déjà ouverte)
    - overlay_path: chemin de l'image PNG à coller
    - dest_x, dest_y: coordonnées où coller (coin haut-gauche du logo)
    - fixed_height: hauteur en pixels à imposer pour l'overlay
    Retourne l'image modifiée (background)
    """
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size
    new_width = int(original_width * fixed_height / original_height)
    overlay = overlay.resize((new_width, fixed_height), Image.LANCZOS)
    background.paste(overlay, (dest_x, dest_y), overlay)
    return background

def draw_centered_text_overlay(
    background_img,
    text,
    width,
    center_x,
    center_y,
    fnt,
    fill=(255,255,255,255),
    stroke_width=0,
    stroke_fill=(0,0,0,255)
):
    """
    Affiche un texte centré (avec wordwrap) sur une image, en overlay transparent.
    
    background_img : image PIL.Image (mode RGBA)
    text : le texte à afficher
    width : largeur max du texte en px
    center_x, center_y : centre de l'overlay sur le fond
    fnt : police
    fill : couleur du texte
    """

    draw = ImageDraw.Draw(background_img)
    
    # Word-wrap sur la largeur max en pixels
    def wrap_text_px(text, fnt, max_width, draw):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            bbox = draw.textbbox((0, 0), test, font=fnt)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # On utilise une image temporaire pour mesurer
    temp_img = Image.new("RGBA", (width, 1000))
    temp_draw = ImageDraw.Draw(temp_img)
    lines = wrap_text_px(text, fnt, width, temp_draw)
    
    # Mesure la hauteur totale
    line_height = fnt.getbbox("Hg")[3] - fnt.getbbox("Hg")[1] + 5
    total_height = len(lines) * line_height

    # Calcul de la position de départ pour centrer
    y_start = int(center_y - total_height / 2)

    # Affichage de chaque ligne centrée
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=fnt)
        w = bbox[2] - bbox[0]
        x = int(center_x - w/2)
        y = y_start + i * line_height
        draw.text((x, y), line, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

    return background_img

def format_sets(sets):
    """
    Transforme une chaîne de score 'A/B' en 'A - B'.

    Arguments :
    - sets : str, au format 'A/B'

    Retourne :
    - str formaté : 'A - B' ou sets d'origine si invalide
    """
    if not sets or '/' not in sets:
        return sets

    parts = sets.strip().split('/')
    if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
        a, b = int(parts[0]), int(parts[1])
        return f"{a} - {b}"
    return sets

def did_team_a_win(sets):
    """
    Détermine si l'équipe A a gagné à partir d'un score 'A/B'.

    Arguments :
    - sets : str, au format 'A/B'

    Retourne :
    - True si A > B, False si A < B, None si égalité ou invalide
    """
    if not sets or '/' not in sets:
        return None

    parts = sets.strip().split('/')
    if len(parts) == 2 and all(part.strip().isdigit() for part in parts):
        a, b = int(parts[0]), int(parts[1])
        if a == b:
            return None
        return a > b
    return None

def create_score_image(score):
    """
    Génère une image représentant un score de match de volley :
    - chaque set affiché verticalement (équipe A en haut, B en bas)
    - fond jaune + texte noir pour le score gagnant du set
    - fond noir + texte blanc pour le score perdant

    Argument :
    - score : str, format '26-24,19-25,...'

    Retourne :
    - image PIL.Image
    """
    sets = []
    for s in score.split(','):
        try:
            a, b = map(int, s.strip().split('-'))
            sets.append([a, b])
        except ValueError:
            continue

    # Paramètres
    set_count = len(sets)
    box_width, box_height = 80, 50
    padding, spacing = 20, 10
    width = set_count * (box_width + spacing) + padding * 2 - spacing
    height = box_height * 2 + padding * 3

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except:
        font = ImageFont.load_default()

    for i, (a, b) in enumerate(sets):
        x = padding + i * (box_width + spacing)
        y_top = padding
        y_bottom = y_top + box_height + padding

        # Définir couleurs
        box_a = ("yellow", "black") if a > b else ("black", "white")
        box_b = ("yellow", "black") if b > a else ("black", "white")

        # Boîte équipe A
        draw.rectangle([x, y_top, x + box_width, y_top + box_height], fill=box_a[0])
        a_text = str(a)
        a_size = draw.textbbox((0, 0), a_text, font=font)
        draw.text(
            (x + (box_width - (a_size[2] - a_size[0])) / 2,
             y_top + (box_height - (a_size[3] - a_size[1])) / 2),
            a_text, fill=box_a[1], font=font
        )

        # Boîte équipe B
        draw.rectangle([x, y_bottom, x + box_width, y_bottom + box_height], fill=box_b[0])
        b_text = str(b)
        b_size = draw.textbbox((0, 0), b_text, font=font)
        draw.text(
            (x + (box_width - (b_size[2] - b_size[0])) / 2,
             y_bottom + (box_height - (b_size[3] - b_size[1])) / 2),
            b_text, fill=box_b[1], font=font
        )

    return image

#== Main ===============================================================
#== FACTORISATION COMMUNE ==================================================

def setup_graphics(format="pub", multiplier=2):
    """
    Initialise les polices et le fond en fonction du format (story/publication).

    Arguments :
    - format : str, "pub" ou "story"
    - multiplier : facteur d'échelle pour les tailles (par défaut 2)

    Retourne :
    - m : facteur utilisé pour la mise à l'échelle
    - fonts : dictionnaire de polices chargées
    - background : image PIL ouverte et convertie
    """
    m = multiplier
    fonts = {
        "main": ImageFont.truetype("_font/DejaVuSans.ttf", size=50*m),
        "bold_10": ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=10*m),
        "bold_12": ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=12*m),
        "bold_13": ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=13*m),
        "bold_14": ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=14*m),
        "bold_15": ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=15*m),
        "title": ImageFont.truetype("_font/Gagalin-Regular.ttf", size=40*m),
        "sets": ImageFont.truetype("_font/Coiny-Regular.ttf", size=30*m),
        "victory": ImageFont.truetype("_font/Coiny-Regular.ttf", size=25*m),
    }
    background = Image.open(f"_img/objects/background_{format}.png").convert("RGBA")
    return m, fonts, background

def parse_csv_rows():
    """
    Récupère et parse le fichier CSV depuis la FFVB.

    Retourne :
    - itérateur CSV
    """
    url = "https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php"
    payload = {
        "cnclub": "0775819",
        "cal_saison": "2024/2025",
        "typ_edition": "E",
        "type": "RES"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()
    csv_latin1_bytes = r.content  # type: bytes
    csv_utf8_str = csv_latin1_bytes.decode('latin1').encode('utf-8').decode('utf-8')

    csvfile = io.StringIO(csv_utf8_str)
    return csv.reader(csvfile, delimiter=";", quotechar='"')

def parse_local_csv_rows():
    """
    Charge et parse un fichier CSV local (UTF-8) pour le traitement des matchs.

    Ce remplacement évite l'appel réseau à la FFVB en mode hors-ligne.
    Le chemin est fixé à 'data/export.csv', mais peut être modifié.

    Retourne :
    - itérateur CSV
    """
    with open("export20242025_utf8.csv", newline="", encoding="utf-8") as csvfile:
        return csv.reader(csvfile, delimiter=";", quotechar='"')

#== IMAGE - PLANNING =======================================================

def generate_filtered_image(categories_filter=None, date_start=None, date_end=None, title=None, format="pub", mode="planning"):
    """
    Génère une image affichant le planning des matchs à venir selon les filtres donnés.

    Arguments :
    - categories_filter : liste de codes de catégories à inclure (ex: ["RMC", "PVA"])
    - date_start / date_end : bornes de dates (format YYYY-MM-DD)
    - title : titre personnalisé affiché en haut de l'image
    - format : "pub" ou "story" (détermine le fond et les dimensions)

    Retourne : image PIL
    """
    m, fonts, background = setup_graphics(format)
    fnt_gagalin_40 = fonts["title"]

    # Constantes de placement vertical
    v = 200*m
    v_title = 50*m
    v_entity = 225*m
    v_category = 255*m
    v_delta = 80*m
    v_logo = 205*m
    v_team = 235*m
    v_date = 235*m
    v_place = 213*m
    v_place_type = 215*m
    v_sets = 238*m
    v_victory = 238*m

    draw_centered_text_overlay(background, title, 430*m, 660*m, v_title, fnt_gagalin_40, fill=(192,192,192,255), stroke_width=2, stroke_fill=(84,84,84,255))

    # Parsing des dates limites
    date_start_dt = datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
    date_end_dt = datetime.strptime(date_end, "%Y-%m-%d") if date_end else None

    reader = parse_csv_rows()

    for row in reader:
        entity = row[0]
        match = row[2]
        date = row[3]
        hour = "" if row[4] == "00:00" else row[4]
        logo_a = row[5]
        team_a = row[6]
        logo_b = row[7]
        team_b = row[8]
        sets = row[9]
        score = row[10]
        place = row[12]
        

        if date == 'Date':
            continue

        dt = datetime.strptime(date, "%Y-%m-%d")
        if date_start_dt and dt < date_start_dt:
            continue
        if date_end_dt and dt > date_end_dt:
            continue

        cat_code = match[:3]
        if categories_filter and cat_code not in categories_filter:
            continue

        if entity not in entities_str:
            continue

        title_entity = entities.get(entity, "null")
        category = categories.get(cat_code, "null")
        date_full = f"{jours[dt.strftime('%A')]} {dt.day} {mois[dt.strftime('%B')]} {hour}"

        match mode:
            case "results":
                
                result = did_team_a_win(sets)
                victory_color = "green" if result else "red" if result is False else "yellow"
                victory_text = "VICTOIRE" if result else "DÉFAITE" if result is False else "INCONNU"

                overlay = Image.open(f"_img/objects/banner_result_{victory_color}.png").convert("RGBA")
                background.paste(overlay, (20*m, v), overlay)
            case _: # Default "planning"
                overlay = Image.open(f"_img/objects/banner_planning.png").convert("RGBA")
                background.paste(overlay, (20*m, v), overlay)

        # Debug console
        print(f"{format} | {date_full} - {entity} - {match} - {category} - {team_a} - {team_b} - {sets} - {score} - {place} | {victory_color}")


        draw_centered_text_overlay(background, title_entity, 115*m, 95*m, v_entity, fonts["bold_15"], fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,255))
        draw_centered_text_overlay(background, category, 115*m, 95*m, v_category, fonts["bold_15"], fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,255))

        background = paste_image_fit_box(background, f"_img/clubs/{logo_a}.png", 170*m, v_logo, 65*m, 65*m)
        draw_centered_text_overlay(background, team_a, 120*m, 310*m, v_team, fonts["bold_13"], fill=(0,0,0,255))

        background = paste_image_fit_box(background, f"_img/clubs/{logo_b}.png", 425*m, v_logo, 65*m, 65*m)
        draw_centered_text_overlay(background, team_b, 120*m, 560*m, v_team, fonts["bold_13"], fill=(0,0,0,255))


        match mode:
            case "results":
                if result:
                    draw_centered_text_overlay(background, victory_text, 200*m, 705*m, v_victory, fonts["victory"], fill=(0,109,57,255))
                else:
                    draw_centered_text_overlay(background, victory_text, 200*m, 705*m, v_victory, fonts["victory"], fill=(167,46,59,255))

                sets_formatted = format_sets(sets)
                draw_centered_text_overlay(background, sets_formatted, 100*m, 828*m, v_sets, fonts["sets"], fill=(10,58,128,255))


            case _: # Default "planning"
                draw_centered_text_overlay(background, date_full, 100*m, 705*m, v_date, fonts["bold_15"], fill=(255,255,255,255))

                result = get_gymnase_address(match, entity)
                if result:
                    place_nom = result["nom"]
                    place_adr = result["rue"]
                    place_ville = result["ville"]
                else:
                    place_adr = "Adresse non trouvée"
                    place_nom = ""
                    place_ville = ""

                draw_centered_text_overlay(background, place_nom, 210*m, 882*m, v_place, fonts["bold_14"], fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,255))
                draw_centered_text_overlay(background, place_adr, 210*m, 882*m, v_place + 40, fonts["bold_12"], fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,255))
                draw_centered_text_overlay(background, place_ville, 210*m, 882*m, v_place + 80, fonts["bold_15"], fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,255))

                place_type = "dom" if place in ['GYMNASE DAVID DOUILLET', 'DAVID DOUILLET', 'PARC DES SPORTS', 'ESPACE JEAN JACQUES LITZLER'] else "ext"
                overlay = Image.open(f"_img/objects/{place_type}.png").convert("RGBA").resize((40*m, 40*m))
                background.paste(overlay, (995*m, v_place_type), overlay)

        v += v_delta
        v_entity += v_delta
        v_category += v_delta
        v_logo += v_delta
        v_team += v_delta
        v_date += v_delta
        v_place += v_delta
        v_place_type += v_delta
        v_sets += v_delta
        v_victory += v_delta

    return background

# #== IMAGE - RESULTATS ======================================================

# def generate_results_image(categories_filter=None, date_start=None, date_end=None, title=None, format="pub"):
#     """
#     Génère une image affichant un résumé des résultats passés.

#     Arguments : mêmes que generate_filtered_image
#     Retourne : image PIL
#     """
#     m, fonts, background = setup_graphics(format)
#     fnt_gagalin_40 = fonts["title"]

#     # Constantes de placement vertical
#     v = 200*m
#     v_title = 50*m
#     v_entity = 225*m
#     v_category = 255*m
#     v_delta = 80*m
#     v_logo = 205*m
#     v_team = 235*m
#     v_date = 235*m
#     v_place = 213*m
#     v_place_type = 215*m

#     draw = ImageDraw.Draw(background)

#     draw_centered_text_overlay(background, title, 430*m, 660*m, v_title, fnt_gagalin_40, fill=(192,192,192,255), stroke_width=2, stroke_fill=(84,84,84,255))
    
#     # Parsing des dates limites
#     date_start_dt = datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
#     date_end_dt = datetime.strptime(date_end, "%Y-%m-%d") if date_end else None

#     reader = parse_csv_rows()

#     for i, row in enumerate(reader):
#         if i < 10: 
#             print(row)
#     # for row in reader:
#     #     entity = row[0]
#     #     match = row[2]
#     #     hour = "" if row[4] == "00:00" else row[4]
#     #     logo_a = row[5]
#     #     team_a = row[6]
#     #     logo_b = row[7]
#     #     team_b = row[8]
#     #     place = row[12]
#     #     date = row[3]

#     #     print(format + " | " + date_full + " - " + entity + " - " + match + " - " + category + " - " + team_a + " - " + team_b + " - " + place)
    
#     draw.text((20, 50), f"Résultats du {date_start} au {date_end}", fill="white")
#     draw.text((20, 100), "Catégories : " + ", ".join(categories_filter or []), fill="white")

#     return background
