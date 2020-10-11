#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Methods for creating the stickers."""
import datetime as dtm
import pytz
from tempfile import NamedTemporaryFile
from typing import Union
from telegram import User
from telegram.ext import CallbackContext
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from hyphen import Hyphenator
from textwrap2 import fill

TEMPLATE_DIRECTORY = 'templates'
""":obj:`str`: Name of the directory containing the templates."""
HEADER_TEMPLATE = f'{TEMPLATE_DIRECTORY}/header.png'
""":obj:`str`: Path of the template for the header."""
FOOTER_TEMPLATE = f'{TEMPLATE_DIRECTORY}/footer.png'
""":obj:`str`: Path of the template for the footer."""
BODY_TEMPLATE = f'{TEMPLATE_DIRECTORY}/body.png'
""":obj:`str`: Path of the template for the body."""
VERIFIED_TEMPLATE = f'{TEMPLATE_DIRECTORY}/verified.png'
""":obj:`str`: Path of the template for the »verified« symbol."""
VERIFIED_IMAGE = Image.open(VERIFIED_TEMPLATE)
VERIFIED_IMAGE.thumbnail((27, 27))
""":class:`Pillow.Image.Image`: The »verified« symbol as Pillow image in the correct size."""
BACKGROUND = '#16202cff'
""":obj:`str`: Background color."""
TEXT_MAIN = '#ffffff'
""":obj:`str`: Color of the main text."""
TEXT_SECONDARY = '#8d99a5ff'
""":obj:`str`: Color of secondary text."""
FONTS_DIRECTORY = 'fonts'
""":obj:`str`: Name of the directory containing the fonts."""
FONT_HEAVY = f'{FONTS_DIRECTORY}/seguibl.ttf'
""":obj:`str`: Font of the main text."""
FONT_SEMI_BOLD = f'{FONTS_DIRECTORY}/seguisb.ttf'
""":obj:`str`: Font of the secondary text."""
FALLBACK_PROFILE_PICTURE = 'logo/TwitterStatusBot-rectangle.png'
""":obj:`str`: Path of the picture to use as profile picture, if the user has none."""
HEADERS_DIRECTORY = 'headers'
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
HYPHENATOR = Hyphenator('en_US')
""":class:`PyHyphen.Hyphenator`: A hyphenator to use to wrap text."""


class HyphenationError(Exception):

    def __init__(self) -> None:
        super().__init__('Something went wrong trying to hyphenate your text. Please note that '
                         'words may not be longer than 100 characters. Also, currently only '
                         'English is properly supported for hyphenation.')


def mask_circle_transparent(image: Union[Image.Image, str]) -> Image.Image:
    """
    Cuts a circle from an square image.

    Args:
        image: Either the image path or a loaded :class:`PIL.Image.Image`.

    Returns:
        :class:`PIL.Image.Image`:
    """
    if isinstance(image, str):
        image = Image.open(image)

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
    mask = mask.filter(ImageFilter.DETAIL())

    result = image.copy()
    result.putalpha(mask)

    return result


def shorten_text(text: str, max_width: int, font: ImageFont.ImageFont) -> str:
    """
    Shortens the given text such that it does not exceeds ``max_width`` pixels wrt the given
    ``font``. Trailing dots are added to indicate that the text was shortened.

    Args:
        text: The text to shorten.
        max_width: Maximum width in pixels.
        font: The font the shortening is executed for.

    Returns:
        str: The shortened text
    """
    (width, _), _ = font.font.getsize(text)
    i = 0
    short_text = text
    while width > max_width:
        i += 1
        short_text = f'{text[:-i]}...'
        (width, _), _ = font.font.getsize(short_text)
    return short_text


def build_footer(timezone: str = 'Europe/Berlin') -> Image.Image:
    """
    Creates the footer for the sticker by adding the current timestamp.

    Args:
        timezone: Optional. The timezone to use for the timestamp. Must be one of the timezones
          supported by ``pytz``. Defaults to ``'Europe/Berlin'``.

    Returns:
        :class:`PIL.Image.Image`: The footer as Pillow image.
    """
    now = dtm.datetime.now(tz=pytz.timezone(timezone))
    date_string = ' '.join([now.strftime('%I:%M %p'), '•', now.strftime('%b %d, %Y')])

    # Offsets
    top = 28
    left = 27

    image = Image.open(FOOTER_TEMPLATE)
    draw = ImageDraw.Draw(image)
    draw.text((left, top), date_string, fill=TEXT_SECONDARY, font=FOOTER_FONT)
    return image


def build_header(user: User, user_picture: Image.Image = None) -> Image.Image:
    """
    Creates the header for the sticker customized for the given user. The header will be saved as
    file and can be reused.

    Args:
        user: The Telegram user this header is build for.
        user_picture: Optional. The profile picture of the user. Defaults to the bots logo.

    Returns:
        :class:`PIL.Image.Image`: The header as Pillow image.
    """

    # Get Background
    background: Image = Image.open(HEADER_TEMPLATE)

    # Add user picture
    up_left = 25
    up_top = 25

    if not user_picture:
        user_picture = mask_circle_transparent(FALLBACK_PROFILE_PICTURE)

    user_picture = mask_circle_transparent(user_picture)
    user_picture.thumbnail((78, 78))
    background.alpha_composite(user_picture, (up_left, up_top))

    # Add user name
    un_left = 118
    un_top = 30
    draw = ImageDraw.Draw(background)
    user_name = shorten_text(user.full_name, 314, USER_NAME_FONT)
    draw.text((un_left, un_top), user_name, fill=TEXT_MAIN, font=USER_NAME_FONT)

    # Add user handle
    uh_left = 118
    uh_top = 62
    draw = ImageDraw.Draw(background)
    user_handle = shorten_text(f'@{user.username or user.first_name}', 370, USER_HANDLE_FONT)
    draw.text((uh_left, uh_top), user_handle, fill=TEXT_SECONDARY, font=USER_HANDLE_FONT)

    # Add verified symbol
    (un_width, _), _ = USER_NAME_FONT.font.getsize(user_name)
    v_left = un_left + un_width + 4
    v_top = 34
    background.alpha_composite(VERIFIED_IMAGE, (v_left, v_top))

    # Save for later use
    background.save(f'{HEADERS_DIRECTORY}/{user.id}.png')
    return background


def get_header(user: User, context: CallbackContext) -> Image.Image:
    """
    Gets the header for the sticker customized for the given user. The header either be loaded from
    file or created anew, if there is no header for the user or users info changed.

    Args:
        user: The Telegram user this header is build for.
        context: The :class:`telegram.ext.CallbackContext` as provided by the
            :class:`telegram.ext.Dispatcher`. Used to check, if for the given user an up to date
            header already exists.

    Returns:
        :class:`PIL.Image.Image`: The header as Pillow image.
    """
    bot = context.bot

    profile_photos = bot.get_user_profile_photos(user.id, limit=1)
    if profile_photos.total_count > 0:
        photo = profile_photos.photos[0][0]
        photo_file_id = photo.file_id
        photo_file_unique_id = photo.file_unique_id
    else:
        photo_file_id = None
        photo_file_unique_id = None
    user.photo_file_unique_id = photo_file_unique_id

    stored_user = context.bot_data.get(user.id, None)
    if (stored_user and stored_user.full_name == user.full_name
            and stored_user.username == user.username
            and stored_user.photo_file_unique_id == user.photo_file_unique_id):
        # Try to return saved header
        # If saving failed, we need to create a new one
        try:
            return Image.open(f'{HEADERS_DIRECTORY}/{user.id}.png')
        except FileNotFoundError:
            pass

    # Get users profile picture, if it exists
    if photo_file_id:
        photo_file = bot.get_file(photo_file_id)
        with NamedTemporaryFile(suffix='.png', delete=False) as file:
            photo_file.download(file.name)
            file.close()
            user_picture = Image.open(file.name)
    else:
        user_picture = None

    context.bot_data[user.id] = user
    return build_header(user, user_picture)


def build_body(text: str) -> Image.Image:
    """
    Builds the body for the sticker by setting the given text.

    Args:
        text: The text to display.

    Returns:
        :class:`PIL.Image.Image`: The body as Pillow image.
    """
    max_chars_per_line = 26
    max_pixels_per_line = 450

    def single_line_text(position, text_, font, bg):  # type: ignore
        _, height = font.getsize(text_)
        bg = bg.resize((bg.width, height + top + 1))
        draw = ImageDraw.Draw(bg)
        draw.text(position, text_, fill=TEXT_MAIN, font=font)

        return bg

    def multiline_text(position, text_, bg):  # type: ignore
        spacing = 4
        _, height = SMALL_TEXT_FONT.getsize_multiline(text_, spacing=spacing)
        bg = bg.resize((bg.width, height - spacing))
        draw = ImageDraw.Draw(bg)
        draw.multiline_text(position, text_, fill=TEXT_MAIN, font=SMALL_TEXT_FONT, spacing=spacing)

        return bg

    background = Image.open(BODY_TEMPLATE)
    left = 27

    if '\n' in text:
        top = -12
        lines = text.split('\n')
        try:
            text = '\n'.join(
                [fill(line, max_chars_per_line, use_hyphenator=HYPHENATOR) for line in lines])
        except Exception:
            raise HyphenationError
        background = multiline_text((left, top), text, background)
    else:
        width, _ = BIG_TEXT_FONT.getsize(text)
        top = -12
        if width > max_pixels_per_line:
            width, _ = SMALL_TEXT_FONT.getsize(text)
            if width > max_pixels_per_line:
                try:
                    text = fill(text, max_chars_per_line, use_hyphenator=HYPHENATOR)
                except Exception:
                    raise HyphenationError
                background = multiline_text((left, top), text, background)
            else:
                background = single_line_text((left, top), text, SMALL_TEXT_FONT, background)
        else:
            top = -26
            background = single_line_text((left, top), text, BIG_TEXT_FONT, background)

    return background


def build_sticker(text: str, user: User, context: CallbackContext) -> Image.Image:
    header = get_header(user, context)
    body = build_body(text)
    footer = build_footer()

    sticker = Image.new('RGBA', (512, header.height + body.height + footer.height))
    sticker.paste(header, (0, 0))
    sticker.paste(body, (0, header.height))
    sticker.paste(footer, (0, header.height + body.height))
    sticker.thumbnail((512, 512))

    return sticker
