import csv
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime

jours = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
mois = {"January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril", "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août", "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"}

# get a font
fnt = ImageFont.truetype("_font/DejaVuSans.ttf", size=50)

background = Image.open("_img/objects/background_01.png").convert("RGBA")

v_bande = 200
with open('export20242025_utf8.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=";", quotechar='"')
    i = 0
   
    for row in reader:

        category = row[0]
        code = row[2]
        hour = row[4]
        logo1 = row[5]
        team1 = row[6]
        logo2 = row[7]
        team2 = row[8]
        gymnase = row[12]
        date = row[3]

        if date != 'Date':
            dt = datetime.strptime(date, "%Y-%m-%d")
            date_full = f"{jours[dt.strftime('%A')]} {dt.strftime('%d')} {mois[dt.strftime('%B')]}"

            if dt.isocalendar()[1] == 5:

                if category == 'LIIDF' or category == 'ADPVA':
                    # print(str(v_bande) + "|" + date_full + " - " + category + " - " + code + " - " + team1 + " - " + team2)

                    overlay = Image.open("_img/objects/bande_01.png").convert("RGBA")
                    background.paste(overlay, (20, v_bande), overlay)

                    # shape = Image.new("RGBA", (400, 200), (0, 0, 0, 0))
                    # d = ImageDraw.Draw(shape)
                    # d.rounded_rectangle((50, 50, 350, 150), radius=40, fill=(255, 200, 50, 255), outline=(0, 0, 0, 255), width=5)
                    # background.paste(shape, (1000, v), shape)

                    # # Créer une image transparente pour la date
                    # date_img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                    # d = ImageDraw.Draw(date_img)
                    # d.multiline_text((10, 10), date_full, font=fnt, fill=(255, 255, 255, 255))
                    # background.paste(date_img, (200, v), date_img)

                    # overlay = Image.open("_img/clubs/0775819.png").convert("RGBA")
                    # overlay = overlay.resize((100, 100))
                    # background.paste(overlay, (100, v), overlay)

                    # # Créer une image transparente pour team1
                    # team1_img = Image.new("RGBA", (700, 100), (255, 255, 255, 0))
                    # d = ImageDraw.Draw(team1_img)
                    # d.multiline_text((10, 10), team1, font=fnt, fill=(0, 0, 0, 255))
                    # background.paste(team1_img, (100, 700), team1_img)

                    v_bande = v_bande + 80

# #im.show()
background.save("output.png")