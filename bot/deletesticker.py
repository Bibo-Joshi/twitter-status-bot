#!/usr/bin/env python3
"""Conversation for deleting stored stickers."""
from typing import cast

from telegram import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton, Sticker
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from bot.userdata import CCT, UserData
from bot.utils import TIMEOUT_HANDLER, FALLBACK_HANDLER

STATE = 42


def start(update: Update, context: CCT) -> int:
    """Starts the conversation and asks for the sticker that's to be deleted.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        int: The next state.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if not user_data.store_stickers:
        message.reply_text(
            "I'm currently not storing any stickers for you. To activate that, "
            "use /toggle_store_stickers."
        )
        return ConversationHandler.END
    if not user_data.sticker_file_ids:
        message.reply_text("I don't have any stickers stored for you.")
        return ConversationHandler.END
    message.reply_text(
        "Please press the button below and select the sticker that you want to delete.",
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text='Click me 👆', switch_inline_query_current_chat='')
        ),
    )
    return STATE


def handle_sticker(update: Update, context: CCT) -> int:
    """Handles the sticker input and deletes the sticker if possible.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        int: The next state.
    """
    message = cast(Message, update.effective_message)
    sticker = cast(Sticker, message.sticker)
    user_data = cast(UserData, context.user_data)

    deleted = user_data.sticker_file_ids.pop(sticker.file_unique_id, None)
    if not deleted:
        message.reply_text(
            'Sorry, this is not a sticker that you have sent before. Aborting operation.'
        )
    else:
        message.reply_text('Sticker successfully deleted.')

    return ConversationHandler.END


delete_sticker_conversation = ConversationHandler(
    entry_points=[CommandHandler('delete_sticker', start)],
    states={
        STATE: [MessageHandler(Filters.sticker, handle_sticker)],
        ConversationHandler.TIMEOUT: [TIMEOUT_HANDLER],
    },
    fallbacks=[FALLBACK_HANDLER],
    conversation_timeout=30,
    persistent=False,
    per_user=True,
    per_chat=True,
)
