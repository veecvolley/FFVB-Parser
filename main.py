import csv

gymnases = set()
with open('export20242025_utf8.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=";", quotechar='"')
    i = 0
    for row in reader:
        if i == 0:
            i += 1
            continue
        if (row[12] != ''):
            gymnases.add(row[12])

print(gymnases)
from PIL import Image, ImageFont, ImageDraw

im = Image.open("veec_fond.png")

print(im.format, im.size, im.mode)

# create an image
out = Image.new("RGB", (1000, 1200), (255, 255, 255))

# get a font
fnt = ImageFont.truetype("Geneva.ttf", 20)
# get a drawing context
d = ImageDraw.Draw(out)

# draw multiline text
text = ""
for gymnase in gymnases:
    text += f"{gymnase}\n"


d.multiline_text((10, 10), text, font=fnt, fill=(0, 0, 0))

im.paste(out, (1000, 1000))
im.show()
