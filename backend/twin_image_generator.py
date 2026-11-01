"""Server-side image generator for Dasha Twin cards.

Generates 1080x1350 (portrait card) and 1080x1920 (story) PNG images.
Idempotent, retryable, safe to run twice, and cached by hash.
"""

from datetime import datetime
import hashlib
import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


SHARE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "shares")
os.makedirs(SHARE_DIR, exist_ok=True)


def get_font(size: int, bold: bool = False):
    """Load standard system font or default bitmap font."""
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "seguiemj.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def render_twin_card_images(
    token: str,
    headline: str,
    body: str,
    figure_name: str,
    figure_field: str,
    lord: str,
    theme: str = "Moon",
    first_name: Optional[str] = None,
    disclaimer: str = "For reflection and fun, not prediction.",
) -> Tuple[str, str]:
    """
    Render both 1080x1350 card and 1080x1920 story versions.
    Returns (card_filepath, story_filepath).
    Idempotent: skips if file already exists.
    """
    card_path = os.path.join(SHARE_DIR, f"{token}.png")
    story_path = os.path.join(SHARE_DIR, f"{token}_story.png")

    if os.path.exists(card_path) and os.path.exists(story_path) and os.path.getsize(card_path) > 1000:
        return card_path, story_path

    # Colors
    bg_top = (13, 7, 27)         # #0D071B
    bg_bottom = (27, 11, 46)     # #1B0B2E
    card_bg = (24, 14, 48)       # #180E30
    gold_border = (229, 169, 60) # #E5A93C
    plum_accent = (178, 30, 104) # #B21E68
    white = (255, 255, 255)
    cream = (253, 230, 138)
    subtext_color = (162, 153, 188)

    # 1. Render 1080x1350 Card
    base_grad = Image.new("RGB", (1, 1350))
    for y in range(1350):
        ratio = y / 1350.0
        r = int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio)
        base_grad.putpixel((0, y), (r, g, b))
    card_img = base_grad.resize((1080, 1350), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(card_img)

    # Inner Glass Card Box
    margin_x = 80
    top_y = 100
    bottom_y = 1250
    draw.rounded_rectangle([margin_x, top_y, 1080 - margin_x, bottom_y], radius=36, fill=card_bg, outline=gold_border, width=3)

    # Fonts
    font_brand = get_font(32, bold=True)
    font_chip = get_font(28, bold=True)
    font_hl = get_font(46, bold=True)
    font_name = get_font(52, bold=True)
    font_field = get_font(30, bold=False)
    font_body = get_font(36, bold=False)
    font_disclaimer = get_font(24, bold=False)
    font_cta = get_font(28, bold=True)

    # Brand Title
    draw.text((1080 // 2, top_y + 60), "✦  MELOOHA · DASHA TWIN  ✦", fill=gold_border, font=font_brand, anchor="mt")

    # Lord Chip
    chip_text = f"  {lord.upper()} PHASE  "
    chip_y = top_y + 130
    draw.rounded_rectangle([1080 // 2 - 140, chip_y, 1080 // 2 + 140, chip_y + 46], radius=23, fill=plum_accent)
    draw.text((1080 // 2, chip_y + 23), chip_text, fill=white, font=font_chip, anchor="mm")

    # Headline
    hl_text = headline if not first_name else f"{first_name}'s {headline}"
    draw.text((1080 // 2, top_y + 220), hl_text, fill=cream, font=font_hl, anchor="mt")

    # Monogram Avatar
    monogram = "".join([w[0].upper() for w in figure_name.split()[:2]])
    avatar_cx = 1080 // 2
    avatar_cy = top_y + 360
    avatar_r = 60
    draw.ellipse([avatar_cx - avatar_r, avatar_cy - avatar_r, avatar_cx + avatar_r, avatar_cy + avatar_r], fill=plum_accent, outline=gold_border, width=3)
    draw.text((avatar_cx, avatar_cy), monogram, fill=white, font=font_hl, anchor="mm")

    # Figure Name & Field
    draw.text((1080 // 2, avatar_cy + 85), figure_name, fill=white, font=font_name, anchor="mt")
    draw.text((1080 // 2, avatar_cy + 155), figure_field, fill=subtext_color, font=font_field, anchor="mt")

    # Divider
    draw.line([margin_x + 60, avatar_cy + 215, 1080 - margin_x - 60, avatar_cy + 215], fill=(60, 40, 95), width=2)

    # Wrapped Body
    body_lines = wrap_text(body, font_body, 1080 - 2 * (margin_x + 60), draw)
    body_y = avatar_cy + 245
    for line in body_lines:
        draw.text((1080 // 2, body_y), line, fill=(230, 225, 245), font=font_body, anchor="mt")
        body_y += 54

    # Disclaimer
    draw.text((1080 // 2, bottom_y - 120), disclaimer, fill=subtext_color, font=font_disclaimer, anchor="mt")

    # CTA Footer
    draw.text((1080 // 2, bottom_y - 70), "Discover your cosmic parallel at melooha.com", fill=gold_border, font=font_cta, anchor="mt")

    card_img.save(card_path, "PNG", optimize=True)

    # 2. Render 1080x1920 Story Version
    story_base_grad = Image.new("RGB", (1, 1920))
    for y in range(1920):
        ratio = y / 1920.0
        r = int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio)
        story_base_grad.putpixel((0, y), (r, g, b))
    story_img = story_base_grad.resize((1080, 1920), Image.Resampling.BILINEAR)
    story_draw = ImageDraw.Draw(story_img)

    # Inner Box for Story
    story_top = 260
    story_bottom = 1680
    story_draw.rounded_rectangle([margin_x, story_top, 1080 - margin_x, story_bottom], radius=40, fill=card_bg, outline=gold_border, width=3)

    story_draw.text((1080 // 2, story_top + 80), "✦  MELOOHA · DASHA TWIN  ✦", fill=gold_border, font=font_brand, anchor="mt")

    story_chip_y = story_top + 170
    story_draw.rounded_rectangle([1080 // 2 - 150, story_chip_y, 1080 // 2 + 150, story_chip_y + 50], radius=25, fill=plum_accent)
    story_draw.text((1080 // 2, story_chip_y + 25), chip_text, fill=white, font=font_chip, anchor="mm")

    story_draw.text((1080 // 2, story_top + 280), hl_text, fill=cream, font=font_hl, anchor="mt")

    story_avatar_cy = story_top + 450
    story_draw.ellipse([avatar_cx - avatar_r - 10, story_avatar_cy - avatar_r - 10, avatar_cx + avatar_r + 10, story_avatar_cy + avatar_r + 10], fill=plum_accent, outline=gold_border, width=4)
    story_draw.text((avatar_cx, story_avatar_cy), monogram, fill=white, font=font_name, anchor="mm")

    story_draw.text((1080 // 2, story_avatar_cy + 95), figure_name, fill=white, font=font_name, anchor="mt")
    story_draw.text((1080 // 2, story_avatar_cy + 175), figure_field, fill=subtext_color, font=font_field, anchor="mt")

    story_draw.line([margin_x + 60, story_avatar_cy + 245, 1080 - margin_x - 60, story_avatar_cy + 245], fill=(60, 40, 95), width=2)

    story_body_lines = wrap_text(body, font_body, 1080 - 2 * (margin_x + 60), story_draw)
    story_body_y = story_avatar_cy + 285
    for line in story_body_lines:
        story_draw.text((1080 // 2, story_body_y), line, fill=(230, 225, 245), font=font_body, anchor="mt")
        story_body_y += 56

    story_draw.text((1080 // 2, story_bottom - 130), disclaimer, fill=subtext_color, font=font_disclaimer, anchor="mt")
    story_draw.text((1080 // 2, story_bottom - 70), "Swipe up / Tap to discover your Dasha Twin", fill=gold_border, font=font_cta, anchor="mt")

    story_img.save(story_path, "PNG", optimize=True)

    return card_path, story_path
