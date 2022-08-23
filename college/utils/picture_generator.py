from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
import os
import requests
from io import BytesIO
import random
import sys


if 'production' in os.environ.get('DJANGO_SETTINGS_MODULE'):
    FONT_URL = os.path.join(settings.STATIC_ROOT, 'fonts/impactregular.ttf')
    response = requests.get(FONT_URL)

DEFAULT_FONT_SIZE = 100
PICTURE_WIDTH = 200
PICTURE_HEIGHT = 200
LINE_SPACING = 5
PADDING = 10
BACKGROUND_COLORS = ['Brown', 'BlueViolet', 'Chocolate', 'Crimson',
                     'DarkOrange', 'DarkSeaGreen', 'DarkSalmon', 'PaleVioletRed']
TEXT_COLOR = 'white'


def get_font():
    if 'production' in os.environ.get('DJANGO_SETTINGS_MODULE'):
        return BytesIO(response.content)
    else:
        return 'static/fonts/impactregular.ttf'


def reduce_font_size_by_width(word, font_size):
    font = ImageFont.truetype(get_font(), size=font_size)

    while True:
        if font.getlength(word) > PICTURE_WIDTH - PADDING * 2:
            font_size -= 1
            font = ImageFont.truetype(get_font(), size=font_size)
            continue

        break

    return font_size


def reduce_font_size_by_height(words, font_size):
    font = ImageFont.truetype(get_font(), size=font_size)

    while True:
        word_height = font.getsize(words[0])[1]

        if PADDING * 2 \
                + (LINE_SPACING * (len(words) - 1) + word_height * len(words)) > PICTURE_HEIGHT:
            font_size -= 1
            font = ImageFont.truetype(get_font(), size=font_size)
            continue

        break

    return font_size


def calculate_font_size(text):
    font_size = DEFAULT_FONT_SIZE

    if '-' in text:
        words = text.split('-')

        for word in words:
            reduced_font_size = reduce_font_size_by_width(word, font_size)
            if reduced_font_size < font_size:
                font_size = reduced_font_size

        font_size = reduce_font_size_by_height(words, font_size)
    else:
        font_size = reduce_font_size_by_width(text, font_size)
        words = [text]
        font_size = reduce_font_size_by_height(words, font_size)

    return font_size


def generate_picture(text):
    im = Image.new('RGB', (PICTURE_WIDTH, PICTURE_HEIGHT), color=random.choice(BACKGROUND_COLORS))
    draw_text = ImageDraw.Draw(im)

    font_size = calculate_font_size(text)
    font = ImageFont.truetype(get_font(), size=font_size)

    words = text.split('-') if '-' in text else [text]

    start_height = (PICTURE_HEIGHT - (len(words) * font.size + (len(words) - 1) * LINE_SPACING)) / 2
    for i, word in enumerate(words):
        width, height = font.getsize(word)

        draw_text.text(
            ((PICTURE_WIDTH - width) / 2, start_height + LINE_SPACING * (i-1) + height * i),
            word,
            fill=TEXT_COLOR,
            font=font
        )
    picture = BytesIO()
    im.save(picture, format='JPEG')
    return picture
