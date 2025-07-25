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

def fetch_csv_utf8():
    url = "https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php"
    payload = {
        "cnclub": "0775819",
        "cal_saison": "2025/2026",
        "typ_edition": "E",
        "type": "RES"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()
    csv_latin1_bytes = r.content  # type: bytes
    csv_utf8_str = csv_latin1_bytes.decode('latin1').encode('utf-8').decode('utf-8')
    return io.StringIO(csv_utf8_str)

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
    fill=(255,255,255,255)
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
        draw.text((x, y), line, font=fnt, fill=fill)

    return background_img

#== Main ===============================================================
def generate_filtered_image(categories_filter=None, date_start=None, date_end=None):
    """
    categories_filter: liste de codes catégorie (ex ["RMC", "PVA", ...]) ou None (toutes)
    date_start/date_end: string format "YYYY-MM-DD" ou None (pas de borne)
    """

    # multiplicateur
    m = 2

    # get a font
    fnt = ImageFont.truetype("_font/DejaVuSans.ttf", size=50*m)
    fnt_bold_10 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=10*m)
    fnt_bold_12 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=12*m)
    fnt_bold_13 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=13*m)
    fnt_bold_14 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=14*m)
    fnt_bold_15 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=15*m)
  

    background = Image.open("_img/objects/background_0"+ str(m) +".png").convert("RGBA")


    v = 200 * m
    v_entity = 225*m
    v_category = 255*m
    v_delta = 80*m
    v_logo = 205*m
    v_team = 235*m
    v_date = 235*m
    v_place = 213*m
    v_place_type = 215*m

    # -- Parsing dates limites --
    date_start_dt = datetime.strptime(date_start, "%Y-%m-%d") if date_start else None
    date_end_dt = datetime.strptime(date_end, "%Y-%m-%d") if date_end else None

    # with open('export20252026_utf8.csv', newline='') as csvfile:
    #     reader = csv.reader(csvfile, delimiter=";", quotechar='"')
    csvfile = fetch_csv_utf8()
    reader = csv.reader(csvfile, delimiter=";", quotechar='"')

    for row in reader:

        entity = row[0]
        match = row[2]
        hour = "" if row[4] == "00:00" else row[4]
        logo_a = row[5]
        team_a = row[6]
        logo_b = row[7]
        team_b = row[8]
        place = row[12]
        date = row[3]

        # Si la date n'est pas précisé on passe à la ligne suivante
        if date == 'Date':
            continue
        
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_full = f"{jours[dt.strftime('%A')]} {dt.day} {mois[dt.strftime('%B')]} {hour}"

        # ==== FILTRAGE PAR CATÉGORIE ====
        cat_code = match[:3]
        # print("CAT_FIL:" + str(categories_filter))
        # print("CAT_CDE:" + str(cat_code))
        # On prend la catégorie du match, sinon None
        if categories_filter is not None:
            # Si la catégorie n'est pas dans la liste, on skip
            if cat_code not in categories_filter:
                continue

        # ==== FILTRAGE PAR DATE ====
        if date_start_dt and dt < date_start_dt:
            continue
        if date_end_dt and dt > date_end_dt:
            continue

        # Si l'entité n'estpas géré on passe à la ligne suivante
        if entity not in entities_str:
            continue

        title_entity = entities.get(entity, "null")
        category = categories.get(match[:3], "null")
        #category = match

        print(str(v) + "|" + date_full + " - " + entity + " - " + match + " - " + category + " - " + team_a + " - " + team_b + " - " + place)

        overlay = Image.open("_img/objects/bande_0"+ str(m) +".png").convert("RGBA")
        background.paste(overlay, (20*m, v), overlay)

        # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
        # draw = ImageDraw.Draw(img)
        # draw.multiline_text((10, 10), title_entity, font=fnt_bold_15, fill=(255, 255, 255, 255))
        # background.paste(img, (30, v_entity), img)

        draw_centered_text_overlay(background, title_entity, 115*m, 95*m, v_entity, fnt_bold_15, fill=(255, 255, 255, 255))

        # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
        # draw = ImageDraw.Draw(img)
        # draw.multiline_text((10, 10), category, font=fnt_bold_15, fill=(255, 255, 255, 255))
        # background.paste(img, (38, v_category), img)

        draw_centered_text_overlay(background, category, 115*m, 95*m, v_category, fnt_bold_15, fill=(255, 255, 255, 255))

        # overlay = Image.open("_img/clubs/" + logo_a + ".png").convert("RGBA")
        # overlay = overlay.resize((65, 65))
        # background.paste(overlay, (170, v_logo), overlay)

        #background = paste_image_with_fixed_width(background, "_img/clubs/" + logo_a + ".png", 170, v_logo, 65)
        background = paste_image_fit_box(background, "_img/clubs/" + logo_a + ".png", 170*m, v_logo, 65*m, 65*m)

        # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
        # draw = ImageDraw.Draw(img)
        # draw.multiline_text((10, 10), team_a, font=fnt_bold_10, fill=(0, 0, 0, 255))
        # background.paste(img, (240, v_team), img)

        draw_centered_text_overlay(background, team_a, 120*m, 310*m, v_team, fnt_bold_13, fill=(0, 0, 0, 255))

        # overlay = Image.open("_img/clubs/" + logo_b + ".png").convert("RGBA")
        # overlay = overlay.resize((65, 65))
        # background.paste(overlay, (425, v_logo), overlay)

        #background = paste_image_with_fixed_width(background, "_img/clubs/" + logo_b + ".png", 425, v_logo, 65)
        background = paste_image_fit_box(background, "_img/clubs/" + logo_b + ".png", 425*m, v_logo, 65*m, 65*m)

        # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
        # draw = ImageDraw.Draw(img)
        # draw.multiline_text((10, 10), team_b, font=fnt_bold_10, fill=(0, 0, 0, 255))
        # background.paste(img, (495, v_team), img)

        draw_centered_text_overlay(background, team_b, 120*m, 560*m, v_team, fnt_bold_13, fill=(0, 0, 0, 255))

        draw_centered_text_overlay(background, date_full, 100*m, 705*m, v_date, fnt_bold_15, fill=(255, 255, 255, 255))

        result = get_gymnase_address(match, entity)
        if result:
            place_nom = result["nom"]
            place_adr = result["rue"]
            place_ville= result["ville"]
        else:
            place_adr = "Adresse non trouvée"

        draw_centered_text_overlay(background, place_nom, 210*m, 882*m, v_place, fnt_bold_14, fill=(255, 255, 255, 255))
        draw_centered_text_overlay(background, place_adr, 210*m, 882*m, v_place + 40, fnt_bold_12, fill=(255, 255, 255, 255))
        draw_centered_text_overlay(background, place_ville, 210*m, 882*m, v_place + 80, fnt_bold_15, fill=(255, 255, 255, 255))

        if place == 'GYMNASE DAVID DOUILLET' or place == 'DAVID DOUILLET' or place == 'PARC DES SPORTS' or place == 'ESPACE JEAN JACQUES LITZLER':
            place_type = "dom"
        else:
            place_type = "ext"

        overlay = Image.open("_img/objects/" + place_type + ".png").convert("RGBA")
        overlay = overlay.resize((40*m, 40*m))
        background.paste(overlay, (995*m, v_place_type), overlay)

        v += v_delta
        v_entity += v_delta
        v_category += v_delta
        v_logo += v_delta
        v_team += v_delta
        v_date += v_delta
        v_place += v_delta
        v_place_type += v_delta
    return background
    #background.save("output.png")
    #background.show()


# img = generate_filtered_image("2FC","2025-10-13","2025-10-20")
# img.save("output.png")