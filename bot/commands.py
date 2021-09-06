#!/usr/bin/env python3
"""Methods for simple commands."""
from typing import cast

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    User,
    ChatAction,
    Sticker,
)

from bot.utils import get_sticker_photo_stream
from bot.constants import HOMEPAGE
from bot.twitter import HyphenationError
from bot.userdata import CCT, UserData


def sticker_message(update: Update, context: CCT) -> None:
    """
    Answers a text message by providing the requested sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    msg = cast(Message, update.effective_message)
    user = cast(User, update.effective_user)
    context.bot.send_chat_action(user.id, ChatAction.UPLOAD_PHOTO)
    stream = get_sticker_photo_stream(cast(str, msg.text), user, context)
    sticker = cast(Sticker, msg.reply_sticker(stream).sticker)
    cast(UserData, context.user_data).sticker_file_ids[sticker.file_unique_id] = sticker.file_id


def info(update: Update, context: CCT) -> None:
    """
    Returns some info about the bot.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    if context.args:
        text = str(HyphenationError())
        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("Try again", switch_inline_query="")
        )
    else:
        text = (
            "I'm <b>Twitter Status Bot</b>. My profession is generating custom"
            " stickers looking like tweets. I'm mainly useful in inline mode, but there are"
            " also a few commands that I understand:\n\n"
            "• /help or /info displays this message.\n"
            "• /toggle_store_stickers (de)activates the saving of stickers. Storing stickers "
            "means that I will keep track of the stickers that you send and suggest them to "
            " you in inline mode. Deactivating this will delete all stored stickers.\n"
            "• /delete_sticker deletes one specific stored sticker.\n"
            "• /set_fallback_picture sets a profile picture that will be used if you don't have a"
            "profile picture or I don't have access to it due to your privacy settings.\n"
            "• /delete_fallback_picture deletes the fallback profile picture.\n"
            "• /show_fallback_picture show the currently set fallback picture.\n"
            "\nTo learn more about me, please visit my homepage 🙂."
        )

        keyboard = InlineKeyboardMarkup.from_column(
            [
                InlineKeyboardButton(
                    "Twitter Status Bot 🤖",
                    url=HOMEPAGE,
                ),
                InlineKeyboardButton(
                    "News Channel 📣",
                    url="https://t.me/BotChangelogs",
                ),
                InlineKeyboardButton("Inline Mode ✍️", switch_inline_query=''),
            ]
        )

    cast(Message, update.effective_message).reply_text(text, reply_markup=keyboard)


def toggle_store_stickers(update: Update, context: CCT) -> None:
    """
    Returns some info about the bot.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if user_data.store_stickers:
        text = "Stickers will no longer be stored. Currently stored stickers were removed."
        user_data.sticker_file_ids.clear()
        user_data.store_stickers = False
    else:
        text = "Sent stickers be stored. will from now."
        user_data.store_stickers = True

    message.reply_text(text)


def show_fallback_picture(update: Update, context: CCT) -> None:
    """Shows the users current fallback profile picture, if set.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if not user_data.fallback_photo:
        message.reply_text(
            "You don't have a fallback picture set. Use /set_fallback_picture to set one."
        )
    else:
        message.reply_photo(
            user_data.fallback_photo.file_id,
            caption='This is your current fallback profile picture. You can delete it with '
            '/delete_fallback_picture or set a new one with /set_fallback_picture.',
        )


def delete_fallback_picture(update: Update, context: CCT) -> None:
    """Deletes the users current fallback profile picture, if set.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if not user_data.fallback_photo:
        message.reply_text(
            "You don't have a fallback picture set. Use /set_fallback_picture to set one."
        )
    else:
        user_data.update_fallback_photo(None)
        message.reply_text('Fallback picture deleted. Use /set_fallback_picture to set a new one.')
