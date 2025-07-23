import csv
import textwrap
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime


#== Configuration ======================================================

jours = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
mois = {"January": "janvier", "February": "février", "March": "mars", "April": "avril", "May": "mai", "June": "juin", "July": "juillet", "August": "août", "September": "septembre", "October": "octobre", "November": "novembre", "December": "décembre"}
entities = {
    "LIIDF": "Championnat Régional",
    "ADPVA": "Championnat de France"
}
categories = {
    "PVA": "Volley-Assis",
    "RMC": "Masculin",
    "RFD": "Féminin",
    "1MB": "Masculin",
    "2FC": "Féminin"
}

places = {
    "DAVID DOUILLET": "Gymnase David Douillet, Coupvray",
    "PARC DES SPORTS": "Gymnase David Douillet, Coupvray",
    "BEGHIN": "Gymnase Pierre Beghin, Moirans"
}


#== Functions ==========================================================

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

# get a font
fnt = ImageFont.truetype("_font/DejaVuSans.ttf", size=50)
fnt_bold_10 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=10)
fnt_bold_15 = ImageFont.truetype("_font/OpenSans-ExtraBold.ttf", size=15)

background = Image.open("_img/objects/background_01.png").convert("RGBA")

v = 200
v_entity = 225
v_category = 255
v_delta = 80
v_logo = 205
v_team = 235
v_date = 235
v_place = 235
v_place_type = 215

with open('export20252026_utf8.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=";", quotechar='"')
    i = 0
   
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

        if date != 'Date':
            dt = datetime.strptime(date, "%Y-%m-%d")
            date_full = f"{jours[dt.strftime('%A')]} {dt.day} {mois[dt.strftime('%B')]} {hour}"

           # if dt.isocalendar()[1] == 7:

            if entity == 'LIIDF' or entity == 'ADPVA':

                title_entity = entities.get(entity, "null")
                category = categories.get(match[:3], "null")
                #category = match

                if category == 'Masculin':

                    print(str(v) + "|" + date_full + " - " + entity + " - " + match + " - " + category + " - " + team_a + " - " + team_b + " - " + place)

                    overlay = Image.open("_img/objects/bande_01.png").convert("RGBA")
                    background.paste(overlay, (20, v), overlay)

                    # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                    # draw = ImageDraw.Draw(img)
                    # draw.multiline_text((10, 10), title_entity, font=fnt_bold_15, fill=(255, 255, 255, 255))
                    # background.paste(img, (30, v_entity), img)

                    draw_centered_text_overlay(background, title_entity, 115, 95, v_entity, fnt_bold_15, fill=(255, 255, 255, 255))

                    # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                    # draw = ImageDraw.Draw(img)
                    # draw.multiline_text((10, 10), category, font=fnt_bold_15, fill=(255, 255, 255, 255))
                    # background.paste(img, (38, v_category), img)

                    draw_centered_text_overlay(background, category, 115, 95, v_category, fnt_bold_15, fill=(255, 255, 255, 255))

                    # overlay = Image.open("_img/clubs/" + logo_a + ".png").convert("RGBA")
                    # overlay = overlay.resize((65, 65))
                    # background.paste(overlay, (170, v_logo), overlay)

                    #background = paste_image_with_fixed_width(background, "_img/clubs/" + logo_a + ".png", 170, v_logo, 65)
                    background = paste_image_fit_box(background, "_img/clubs/" + logo_a + ".png", 170, v_logo, 65, 65)

                    # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                    # draw = ImageDraw.Draw(img)
                    # draw.multiline_text((10, 10), team_a, font=fnt_bold_10, fill=(0, 0, 0, 255))
                    # background.paste(img, (240, v_team), img)

                    draw_centered_text_overlay(background, team_a, 120, 310, v_team, fnt_bold_10, fill=(0, 0, 0, 255))

                    # overlay = Image.open("_img/clubs/" + logo_b + ".png").convert("RGBA")
                    # overlay = overlay.resize((65, 65))
                    # background.paste(overlay, (425, v_logo), overlay)

                    #background = paste_image_with_fixed_width(background, "_img/clubs/" + logo_b + ".png", 425, v_logo, 65)
                    background = paste_image_fit_box(background, "_img/clubs/" + logo_b + ".png", 425, v_logo, 65, 65)

                    # img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                    # draw = ImageDraw.Draw(img)
                    # draw.multiline_text((10, 10), team_b, font=fnt_bold_10, fill=(0, 0, 0, 255))
                    # background.paste(img, (495, v_team), img)

                    draw_centered_text_overlay(background, team_b, 120, 560, v_team, fnt_bold_10, fill=(0, 0, 0, 255))

                    draw_centered_text_overlay(background, date_full, 100, 705, v_date, fnt_bold_15, fill=(255, 255, 255, 255))

                    draw_centered_text_overlay(background, place, 200, 880, v_place, fnt_bold_15, fill=(255, 255, 255, 255))

                    if place == 'GYMNASE DAVID DOUILLET' or place == 'DAVID DOUILLET' or place == 'PARC DES SPORTS' or place == 'ESPACE JEAN JACQUES LITZLER':
                        place_type = "dom"
                    else:
                        place_type = "ext"

                    overlay = Image.open("_img/objects/" + place_type + ".png").convert("RGBA")
                    overlay = overlay.resize((40, 40))
                    background.paste(overlay, (995, v_place_type), overlay)

                    v += v_delta
                    v_entity += v_delta
                    v_category += v_delta
                    v_logo += v_delta
                    v_team += v_delta
                    v_date += v_delta
                    v_place += v_delta
                    v_place_type += v_delta

background.save("output.png")
#background.show()