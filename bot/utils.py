#!/usr/bin/env python3
"""Utility methods for the bot functionality."""
import logging
from io import BytesIO
from typing import cast, Tuple

from telegram import (
    Update,
    Bot,
    StickerSet,
    User,
    Message,
)
from telegram.error import BadRequest
from telegram.ext import ConversationHandler, TypeHandler

from bot.constants import ADMIN_KEY, STICKER_SET_LOGO, STICKER_SET_NAME_KEY
from bot.twitter import build_sticker
from bot.userdata import CCT

logger = logging.getLogger(__name__)


def build_sticker_set_name(bot: Bot, sticker_set_prefix: str) -> str:
    """
    Builds the sticker set name given by ``sticker_set_prefix`` for the given bot.

    Args:
        bot: The Bot owning the sticker set.
        sticker_set_prefix: The sticker set name (prefix).

    Returns:
        str
    """
    return f"{sticker_set_prefix}_by_{bot.username}"


def get_sticker_set(bot: Bot, name: str, admin_id: int, sticker_set_prefix: str) -> StickerSet:
    """
    Get's the sticker set and creates it, if needed.

    Args:
        bot: The Bot owning the sticker set.
        name: The name of the sticker set.
        admin_id: The admins chat id.
        sticker_set_prefix: The sticker set name prefix if one needs to build a new one.

    Returns:
        StickerSet
    """
    try:
        return bot.get_sticker_set(name)
    except BadRequest as exc:
        if "invalid" in str(exc):
            with open(STICKER_SET_LOGO, "rb") as sticker:
                bot.create_new_sticker_set(
                    admin_id, name, sticker_set_prefix, "🐦", png_sticker=sticker
                )
            return bot.get_sticker_set(name)
        raise exc


def clean_sticker_set(context: CCT) -> None:
    """
    Cleans up the sticker set, i.e. deletes all but the first sticker.

    Args:
        context: The callback context as provided by the dispatcher.
    """
    bot = context.bot
    admin_id = cast(int, context.bot_data[ADMIN_KEY])
    sticker_set_prefix = cast(str, context.bot_data[STICKER_SET_NAME_KEY])

    sticker_set = get_sticker_set(
        bot, build_sticker_set_name(bot, sticker_set_prefix), admin_id, sticker_set_prefix
    )
    if len(sticker_set.stickers) > 1:
        for sticker in sticker_set.stickers[1:]:
            try:
                bot.delete_sticker_from_set(sticker.file_id)
            except BadRequest as exc:
                if "Stickerset_not_modified" in str(exc):
                    pass
                else:
                    raise exc


def get_sticker_id(text: str, user: User, context: CCT) -> Tuple[str, str]:
    """
    Gives the sticker ID for the requested sticker.

    Args:
        text: The text to display on the tweet.
        user: The user the tweet is created for.
        context: The callback context as provided by the dispatcher.

    Returns:
        Tuple[str, str]: The stickers unique file ID and file ID
    """
    bot = context.bot

    admin_id = cast(int, context.bot_data[ADMIN_KEY])
    sticker_set_prefix = cast(str, context.bot_data[STICKER_SET_NAME_KEY])
    clean_sticker_set(context)

    sticker_set_name = build_sticker_set_name(bot, sticker_set_prefix)
    emojis = "🐦"

    sticker_stream = BytesIO()
    sticker = build_sticker(text, user, context)
    sticker.save(sticker_stream, format="PNG")
    sticker_stream.seek(0)

    get_sticker_set(bot, sticker_set_name, admin_id, sticker_set_prefix)
    admin_id = cast(int, context.bot_data[ADMIN_KEY])
    bot.add_sticker_to_set(admin_id, sticker_set_name, emojis, png_sticker=sticker_stream)

    sticker_set = get_sticker_set(bot, sticker_set_name, admin_id, sticker_set_prefix)
    sticker = sticker_set.stickers[-1]

    return sticker.file_unique_id, sticker.file_id


def default_message(update: Update, _: CCT) -> None:
    """
    Answers any message with a note that it could not be parsed.

    Args:
        update: The Telegram update.
        _: The callback context as provided by the dispatcher.
    """
    cast(Message, update.effective_message).reply_text(
        "Sorry, but I can only text messages. " 'Send "/help" for more information.'
    )


def conversation_timeout(update: Update, _: CCT) -> int:
    """Informs the user that the operation has timed out and ends the conversation.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        int: :attr:`telegram.ext.ConversationHandler.END`.
    """
    cast(User, update.effective_user).send_message('Operation timed out. Aborting.')

    return ConversationHandler.END


TIMEOUT_HANDLER = TypeHandler(Update, conversation_timeout)
""":class:`telegram.ext.TypeHandler`: A handler that can be used in the timeout state for
conversations."""


def conversation_fallback(update: Update, _: CCT) -> int:
    """Informs the user that the input was invalid and ends the conversation.

    Args:
        update: The Telegram update.
        _: The callback context as provided by the dispatcher.

    Returns:
        int: The next state.
    """
    cast(User, update.effective_user).send_message('Invalid input. Aborting operation.')

    return ConversationHandler.END


FALLBACK_HANDLER = TypeHandler(Update, conversation_fallback)
""":class:`telegram.ext.TypeHandler`: A handler that can be used in the fallbacks for
conversations."""
