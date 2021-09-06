#!/usr/bin/env python3
"""Utility methods for the bot functionality."""
from io import BytesIO
from threading import Event
from typing import cast

from telegram import (
    Update,
    User,
    Message,
)
from telegram.ext import ConversationHandler, TypeHandler

from bot.twitter import build_sticker
from bot.userdata import CCT


def get_sticker_photo_stream(text: str, user: User, context: CCT, event: Event = None) -> BytesIO:
    """
    Gives the sticker ID for the requested sticker.

    Args:
        text: The text to display on the tweet.
        user: The user the tweet is created for.
        context: The callback context as provided by the dispatcher.
        event: Optional. If passed, ``event.is_set()`` will be checked before the time consuming
            parts of the sticker creation and if the event is set, the creation will be terminated.

    Returns:
        Tuple[str, str]: The stickers unique file ID and file ID
    """
    sticker_stream = BytesIO()
    sticker = build_sticker(text, user, context, event=event)
    sticker.save(sticker_stream, format="PNG")
    sticker_stream.seek(0)

    return sticker_stream


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
