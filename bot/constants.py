#!/usr/bin/env python3
"""Constants for the bot."""
from configparser import ConfigParser
from pathlib import Path

from PIL import Image, ImageFont
from hyphen import Hyphenator

config = ConfigParser()
config.read("bot.ini")

# A little trick to get the corrects paths both at runtime and when building the docs
PATH_PREFIX = '../' if Path('../headers').is_dir() else ''

ADMIN_KEY: str = 'ADMIN_KEY'
""":obj:`str`: The admins chat id is stored under this key in ``bot_data``."""
STICKER_CHAT_ID_KEY: str = 'STICKER_CHAT_ID_KEY'
""":obj:`srt`: The name of the chat where stickers can be sent to get their file IDs is stored
under this key in ``bot_data``."""
HOMEPAGE: str = "https://hirschheissich.gitlab.io/twitter-status-bot/"
""":obj:`str`: Homepage of this bot."""
TEMPLATE_DIRECTORY = f"{PATH_PREFIX}templates"
""":obj:`str`: Name of the directory containing the templates."""
HEADER_TEMPLATE = f"{TEMPLATE_DIRECTORY}/header.png"
""":obj:`str`: Path of the template for the header."""
FOOTER_TEMPLATE = f"{TEMPLATE_DIRECTORY}/footer.png"
""":obj:`str`: Path of the template for the footer."""
BODY_TEMPLATE = f"{TEMPLATE_DIRECTORY}/body.png"
""":obj:`str`: Path of the template for the body."""
VERIFIED_TEMPLATE = f"{TEMPLATE_DIRECTORY}/verified.png"
""":obj:`str`: Path of the template for the »verified« symbol."""
VERIFIED_IMAGE = Image.open(VERIFIED_TEMPLATE)
""":class:`Pillow.Image.Image`: The »verified« symbol as Pillow image in the correct size."""
VERIFIED_IMAGE.thumbnail((27, 27))
BACKGROUND = "#16202cff"
""":obj:`str`: Background color."""
TEXT_MAIN = "#ffffff"
""":obj:`str`: Color of the main text."""
TEXT_SECONDARY = "#8d99a5ff"
""":obj:`str`: Color of secondary text."""
FONTS_DIRECTORY = f"{PATH_PREFIX}fonts"
""":obj:`str`: Name of the directory containing the fonts."""
FONT_HEAVY = f"{FONTS_DIRECTORY}/seguibl.ttf"
""":obj:`str`: Font of the main text."""
FONT_SEMI_BOLD = f"{FONTS_DIRECTORY}/seguisb.ttf"
""":obj:`str`: Font of the secondary text."""
FALLBACK_PROFILE_PICTURE = "logo/TwitterStatusBot-rectangle.png"
""":obj:`str`: Path of the picture to use as profile picture, if the user has none."""
HEADERS_DIRECTORY = f"{PATH_PREFIX}headers"
""":obj:`str`: Name of the directory containing the saved headers."""
FOOTER_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 24)
""":class:`PIL.ImageFont.Font`: Font to use for the footer."""
USER_NAME_FONT = ImageFont.truetype(FONT_HEAVY, 24)
""":class:`PIL.ImageFont.Font`: Font to use for the username."""
USER_HANDLE_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 23)
""":class:`PIL.ImageFont.Font`: Font to use for the user handle."""
BIG_TEXT_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 70)
""":class:`PIL.ImageFont.Font`: Font to use for big text in the body."""
SMALL_TEXT_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 36)
""":class:`PIL.ImageFont.Font`: Font to use for small text in the body."""
HYPHENATOR = Hyphenator("en_US")
""":class:`PyHyphen.Hyphenator`: A hyphenator to use to wrap text."""
