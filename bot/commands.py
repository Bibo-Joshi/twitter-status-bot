#!/usr/bin/env python3
"""Methods for simple commands."""
from typing import cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Sticker, Update, User
from telegram.constants import ChatAction

from bot.constants import HOMEPAGE, LTR, RTL
from bot.twitter import HyphenationError
from bot.userdata import CCT, UserData
from bot.utils import get_sticker_photo_stream


async def sticker_message(update: Update, context: CCT) -> None:
    """
    Answers a text message by providing the requested sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    msg = cast(Message, update.effective_message)
    user = cast(User, update.effective_user)
    context.application.create_task(context.bot.send_chat_action(user.id, ChatAction.UPLOAD_PHOTO))
    stream = await get_sticker_photo_stream(cast(str, msg.text), user, context)
    sticker = cast(Sticker, (await msg.reply_sticker(stream)).sticker)
    user_data = cast(UserData, context.user_data)
    if user_data.store_stickers:
        user_data.sticker_file_ids[sticker.file_unique_id] = sticker.file_id


async def info(update: Update, context: CCT) -> None:
    """
    Returns some info about the bot.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
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
                InlineKeyboardButton("Inline Mode ✍️", switch_inline_query=""),
            ]
        )

    await cast(Message, update.effective_message).reply_text(text, reply_markup=keyboard)


async def toggle_store_stickers(update: Update, context: CCT) -> None:
    """Toggles whether or not to store stickers for the user.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
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

    await message.reply_text(text)


async def toggle_text_direction(update: Update, context: CCT) -> None:
    """Toggles whether the user wants to use left-to-right or right-to-left text.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)

    mapping = {LTR: RTL, RTL: LTR}
    user_data.text_direction = mapping[user_data.text_direction]
    description = "left-to-right" if user_data.text_direction == LTR else "right-to-left"

    await message.reply_text(f"The sticker text will be set as {description} now.")


async def show_fallback_picture(update: Update, context: CCT) -> None:
    """Shows the users current fallback profile picture, if set.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if not user_data.fallback_photo:
        await message.reply_text(
            "You don't have a fallback picture set. Use /set_fallback_picture to set one."
        )
    else:
        await message.reply_photo(
            user_data.fallback_photo.file_id,
            caption="This is your current fallback profile picture. You can delete it with "
            "/delete_fallback_picture or set a new one with /set_fallback_picture.",
        )


async def delete_fallback_picture(update: Update, context: CCT) -> None:
    """Deletes the users current fallback profile picture, if set.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    user_data = cast(UserData, context.user_data)
    message = cast(Message, update.effective_message)
    if not user_data.fallback_photo:
        await message.reply_text(
            "You don't have a fallback picture set. Use /set_fallback_picture to set one."
        )
    else:
        user_data.update_fallback_photo(None)
        await message.reply_text(
            "Fallback picture deleted. Use /set_fallback_picture to set a new one."
        )
