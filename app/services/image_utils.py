
from PIL import Image, ImageDraw, ImageFont

def paste_image_fit_box(background, overlay_path, box_x, box_y, box_width, box_height):
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size
    ratio = min(box_width / original_width, box_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    overlay = overlay.resize((new_width, new_height), Image.LANCZOS)
    decal_x = box_x + (box_width - new_width) // 2
    decal_y = box_y + (box_height - new_height) // 2
    background.paste(overlay, (decal_x, decal_y), overlay)
    return background

def paste_image_with_fixed_width(background, overlay_path, dest_x, dest_y, fixed_width):
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size
    new_height = int(original_height * fixed_width / original_width)
    overlay = overlay.resize((fixed_width, new_height), Image.LANCZOS)
    background.paste(overlay, (dest_x, dest_y), overlay)
    return background

def paste_image_with_fixed_height(background, overlay_path, dest_x, dest_y, fixed_height):
    overlay = Image.open(overlay_path).convert("RGBA")
    original_width, original_height = overlay.size
    new_width = int(original_width * fixed_height / original_height)
    overlay = overlay.resize((new_width, fixed_height), Image.LANCZOS)
    background.paste(overlay, (dest_x, dest_y), overlay)
    return background

def draw_centered_text_overlay(background_img, text, width, center_x, center_y, fnt, fill=(255,255,255,255), stroke_width=0, stroke_fill=(0,0,0,255)):
    draw = ImageDraw.Draw(background_img)

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

    temp_img = Image.new("RGBA", (width, 1000))
    temp_draw = ImageDraw.Draw(temp_img)
    lines = wrap_text_px(text, fnt, width, temp_draw)
    line_height = fnt.getbbox("Hg")[3] - fnt.getbbox("Hg")[1] + 5
    total_height = len(lines) * line_height
    y_start = int(center_y - total_height / 2)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=fnt)
        w = bbox[2] - bbox[0]
        x = int(center_x - w/2)
        y = y_start + i * line_height
        draw.text((x, y), line, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

    return background_img
