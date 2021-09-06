#!/usr/bin/env python3
"""Methods for creating the stickers."""
import datetime as dtm
import logging
from io import BytesIO
from threading import Event
from typing import Union, cast, Optional

import pytz
from telegram import User
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from textwrap2 import fill

from bot.constants import (
    HEADER_TEMPLATE,
    FOOTER_TEMPLATE,
    BODY_TEMPLATE,
    VERIFIED_IMAGE,
    TEXT_MAIN,
    TEXT_SECONDARY,
    FALLBACK_PROFILE_PICTURE,
    HEADERS_DIRECTORY,
    FOOTER_FONT,
    USER_NAME_FONT,
    USER_HANDLE_FONT,
    BIG_TEXT_FONT,
    SMALL_TEXT_FONT,
    HYPHENATOR,
)
from bot.userdata import CCT, UserData


logger = logging.getLogger(__name__)


class HyphenationError(Exception):
    """Custom exception class for hyphenation exceptions."""

    def __init__(self) -> None:
        super().__init__(
            "Something went wrong trying to hyphenate your text. Please note that "
            "words may not be longer than 100 characters. Also, currently only "
            "English is properly supported for hyphenation."
        )


def _check_event(event: Event = None) -> None:
    if event and event.is_set():
        logger.debug('Sticker creation terminated because event was set')
        raise RuntimeError('Sticker creation terminated because event was set')


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
        short_text = f"{text[:-i]}..."
        (width, _), _ = font.font.getsize(short_text)
    return short_text


def build_footer(timezone: str = "Europe/Berlin", event: Event = None) -> Image.Image:
    """
    Creates the footer for the sticker by adding the current timestamp.

    Args:
        timezone: Optional. The timezone to use for the timestamp. Must be one of the timezones
          supported by ``pytz``. Defaults to ``'Europe/Berlin'``.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the footer creation and if the event is set, the creation will be terminated.

    Returns:
        :class:`PIL.Image.Image`: The footer as Pillow image.
    """
    now = dtm.datetime.now(tz=pytz.timezone(timezone))
    date_string = " ".join([now.strftime("%I:%M %p"), "•", now.strftime("%b %d, %Y")])

    # Offsets
    top = 28
    left = 27

    _check_event(event)
    image = Image.open(FOOTER_TEMPLATE)
    draw = ImageDraw.Draw(image)
    draw.text((left, top), date_string, fill=TEXT_SECONDARY, font=FOOTER_FONT)
    return image


def build_header(  # pylint: disable=R0914
    user_data: UserData,
    user_picture: Image.Image = None,
    event: Event = None,
) -> Image.Image:
    """
    Creates the header for the sticker customized for the given user. The header will be saved as
    file and can be reused.

    Args:
        user_data: The user data for the user this header is build for.
        user_picture: Optional. The profile picture of the user. Defaults to the bots logo.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the header creation and if the event is set, the creation will be terminated.

    Returns:
        :class:`PIL.Image.Image`: The header as Pillow image.
    """
    _check_event(event)
    # Get Background
    background: Image = Image.open(HEADER_TEMPLATE)

    # Add user picture
    up_left = 25
    up_top = 25

    if not user_picture:
        _check_event(event)
        user_picture = mask_circle_transparent(FALLBACK_PROFILE_PICTURE)

    # crop a centered square
    if not user_picture.width == user_picture.height:
        side = min(user_picture.width, user_picture.height)
        left = (user_picture.width - side) // 2
        upper = (user_picture.height - side) // 2
        _check_event(event)
        user_picture = user_picture.crop((left, upper, left + side, upper + side))

    _check_event(event)
    # make it a circle an small
    user_picture = mask_circle_transparent(user_picture)
    user_picture.thumbnail((78, 78))
    background.alpha_composite(user_picture, (up_left, up_top))
    draw = ImageDraw.Draw(background)

    _check_event(event)
    # Add user name
    un_left = 118
    un_top = 30
    user_name = shorten_text(cast(str, user_data.full_name), 314, USER_NAME_FONT)
    draw.text((un_left, un_top), user_name, fill=TEXT_MAIN, font=USER_NAME_FONT)

    _check_event(event)
    # Add user handle
    uh_left = 118
    uh_top = 62
    user_handle = shorten_text(
        f"@{user_data.username or user_data.first_name}", 370, USER_HANDLE_FONT
    )
    draw.text((uh_left, uh_top), user_handle, fill=TEXT_SECONDARY, font=USER_HANDLE_FONT)

    _check_event(event)
    # Add verified symbol
    (un_width, _), _ = USER_NAME_FONT.font.getsize(user_name)
    v_left = un_left + un_width + 4
    v_top = 34
    background.alpha_composite(VERIFIED_IMAGE, (v_left, v_top))

    _check_event(event)
    # Save for later use
    background.save(f"{HEADERS_DIRECTORY}/{user_data.user_id}.png")
    return background


def get_header(  # pylint: disable = R0914
    user: User, context: CCT, event: Event = None
) -> Image.Image:
    """
    Gets the header for the sticker customized for the given user. The header either be loaded from
    file or created anew, if there is no header for the user or users info changed.

    If the header needs to be generated anew, stored stickers are deleted.

    Args:
        user: The Telegram user this header is build for.
        context: The :class:`telegram.ext.CallbackContext` as provided by the
            :class:`telegram.ext.Dispatcher`. Used to check, if for the given user an up to date
            header already exists.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the header creation and if the event is set, the creation will be terminated.

    Returns:
        :class:`PIL.Image.Image`: The header as Pillow image.
    """
    drop_stored_stickers = False
    bot = context.bot
    user_data = cast(UserData, context.user_data)

    _check_event(event)
    profile_photos = bot.get_user_profile_photos(user.id, limit=1)
    if profile_photos and profile_photos.total_count > 0:
        photo = profile_photos.photos[0][0]
        photo_file_id: Optional[str] = photo.file_id
        photo_file_unique_id: Optional[str] = photo.file_unique_id
    else:
        photo_file_id = None
        photo_file_unique_id = None

    fallback_file_id = user_data.fallback_photo.file_id if user_data.fallback_photo else None
    fallback_unique_id = (
        user_data.fallback_photo.file_unique_id if user_data.fallback_photo else None
    )

    _check_event(event)
    if (
        user_data.full_name == user.full_name  # pylint: disable=R0916
        and user_data.username == user.username
        and user_data.photo_file_unique_id == (photo_file_unique_id or fallback_unique_id)
    ):
        # Try to return saved header
        try:
            return Image.open(f"{HEADERS_DIRECTORY}/{user.id}.png")
        except Exception:  # pylint: disable=W0703
            # If saving failed, we need to create a new one
            logger.debug(
                'Opening existing header for user %s failed. Building new header.', user.id
            )
    else:
        drop_stored_stickers = True

    # Get users profile picture, if it exists
    file_id = photo_file_id or fallback_file_id
    file_unique_id = photo_file_unique_id or fallback_unique_id
    if file_id:
        _check_event(event)
        photo_file = bot.get_file(file_id)
        picture_stream = BytesIO()
        _check_event(event)
        photo_file.download(out=picture_stream)
        picture_stream.seek(0)
        _check_event(event)
        user_picture = Image.open(picture_stream)
    else:
        user_picture = None

    user_data.update_user_info(user, photo_file_unique_id=file_unique_id)
    if drop_stored_stickers:
        user_data.sticker_file_ids.clear()
    return build_header(user_data, user_picture, event=event)


def build_body(text: str, event: Event = None) -> Image.Image:
    """
    Builds the body for the sticker by setting the given text.

    Args:
        text: The text to display.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the body creation and if the event is set, the creation will be terminated.

    Returns:
        :class:`PIL.Image.Image`: The body as Pillow image.
    """
    max_chars_per_line = 26
    max_pixels_per_line = 450

    def single_line_text(position, text_, font, background_):  # type: ignore
        _check_event(event)
        _, height = font.getsize(text_)
        background_ = background_.resize((background_.width, height + top + 1))
        draw = ImageDraw.Draw(background_)
        draw.text(position, text_, fill=TEXT_MAIN, font=font)

        return background_

    def multiline_text(position, text_, background_):  # type: ignore
        _check_event(event)
        spacing = 4
        _, height = SMALL_TEXT_FONT.getsize_multiline(text_, spacing=spacing)
        background_ = background_.resize((background_.width, height - spacing))
        draw = ImageDraw.Draw(background_)
        draw.multiline_text(position, text_, fill=TEXT_MAIN, font=SMALL_TEXT_FONT, spacing=spacing)

        return background_

    _check_event(event)
    background = Image.open(BODY_TEMPLATE)
    left = 27

    if "\n" in text:
        top = -12
        lines = text.split("\n")
        try:
            text = "\n".join(
                [fill(line, max_chars_per_line, use_hyphenator=HYPHENATOR) for line in lines]
            )
        except Exception as exc:
            raise HyphenationError from exc
        background = multiline_text((left, top), text, background)
    else:
        width, _ = BIG_TEXT_FONT.getsize(text)
        top = -12
        if width > max_pixels_per_line:
            width, _ = SMALL_TEXT_FONT.getsize(text)
            if width > max_pixels_per_line:
                try:
                    text = fill(text, max_chars_per_line, use_hyphenator=HYPHENATOR)
                except Exception as exc:
                    raise HyphenationError from exc
                background = multiline_text((left, top), text, background)
            else:
                background = single_line_text((left, top), text, SMALL_TEXT_FONT, background)
        else:
            top = -26
            background = single_line_text((left, top), text, BIG_TEXT_FONT, background)

    return background


def build_sticker(text: str, user: User, context: CCT, event: Event = None) -> Image.Image:
    """Builds the sticker.

    Arguments:
        text: Text of the tweet.
        user: The user the sticker is generated for.
        context: The callback context as provided by the dispatcher.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the sticker creation and if the event is set, the creation will be terminated.
    """
    header = get_header(user, context, event=event)
    body = build_body(text, event=event)
    footer = build_footer(event=event)

    _check_event(event)
    sticker = Image.new("RGBA", (512, header.height + body.height + footer.height))
    sticker.paste(header, (0, 0))
    sticker.paste(body, (0, header.height))
    sticker.paste(footer, (0, header.height + body.height))

    _check_event(event)
    sticker.thumbnail((512, 512))

    return sticker
