#!/usr/bin/env python3
"""Methods for initializing the application."""
import warnings
from typing import Union

from ptbstats import SimpleStats, register_stats, set_application
from telegram import BotCommandScopeChat, Update
from telegram.ext import (
    Application,
    ChosenInlineResultHandler,
    CommandHandler,
    ExtBot,
    InlineQueryHandler,
    JobQueue,
    MessageHandler,
    filters,
)

from bot.commands import (
    delete_fallback_picture,
    info,
    show_fallback_picture,
    sticker_message,
    toggle_store_stickers,
    toggle_text_direction,
)
from bot.constants import ADMIN_KEY, STICKER_CHAT_ID_KEY
from bot.deletesticker import delete_sticker_conversation
from bot.error import error, hyphenation_error
from bot.inline import handle_chosen_inline_result, inline
from bot.setfallbackpicture import set_fallback_picture_conversation
from bot.settimezone import build_set_timezone_conversation
from bot.userdata import CCT, UserData
from bot.utils import default_message

# B/C we know what we're doing
warnings.filterwarnings("ignore", message="If 'per_", module="telegram.ext.conversationhandler")
warnings.filterwarnings(
    "ignore",
    message=".*does not handle objects that can not be copied",
    module="telegram.ext.basepersistence",
)


async def setup_application(
    application: Application[ExtBot, CCT, UserData, dict, dict, JobQueue],
    admin_id: int,
    sticker_chat_id: Union[str, int],
) -> None:
    """
    Adds handlers and sets up ``bot_data``. Also sets the bot commands.

    Args:
        application: The :class:`telegram.ext.Application`.
        admin_id: The admins chat id.
        sticker_chat_id: The name of the chat where stickers can be sent to get their file IDs.
    """
    async with application:
        await _setup_application(
            application=application, admin_id=admin_id, sticker_chat_id=sticker_chat_id
        )


async def _setup_application(
    application: Application[ExtBot, CCT, UserData, dict, dict, JobQueue],
    admin_id: int,
    sticker_chat_id: Union[str, int],
) -> None:
    # error handlers
    application.add_error_handler(hyphenation_error)
    application.add_error_handler(error)

    # Set up stats
    set_application(application)

    def check_inline_query(update: object) -> bool:
        return isinstance(update, Update) and bool(update.chosen_inline_result)

    def check_text(update: object) -> bool:
        return (
            isinstance(update, Update)
            and bool(update.effective_message)
            and bool(
                (filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND).check_update(update)
            )
        )

    register_stats(SimpleStats("ilq", check_inline_query), admin_id=admin_id)
    register_stats(
        SimpleStats(
            "text",
            check_text,
        ),
        admin_id=admin_id,
    )

    # basic command handlers
    application.add_handler(CommandHandler(["start", "help", "info"], info))
    application.add_handler(CommandHandler("toggle_store_stickers", toggle_store_stickers))
    application.add_handler(CommandHandler("toggle_text_direction", toggle_text_direction))
    application.add_handler(delete_sticker_conversation)
    application.add_handler(set_fallback_picture_conversation)
    application.add_handler(build_set_timezone_conversation(application.bot))
    application.add_handler(CommandHandler("delete_fallback_picture", delete_fallback_picture))
    application.add_handler(CommandHandler("show_fallback_picture", show_fallback_picture))

    # functionality
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, sticker_message)
    )
    application.add_handler(
        MessageHandler(
            filters.ALL & filters.ChatType.PRIVATE & ~filters.ViaBot(application.bot.id),
            default_message,
        )
    )
    application.add_handler(InlineQueryHandler(inline))
    application.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))

    # Bot commands
    base_commands = [
        ["help", "Displays a short info message about the Twitter Status Bot"],
        ["start", 'See "/help"'],
        ["info", 'Same as "/help"'],
        ["toggle_store_stickers", "(De)activates the saving of stickers"],
        ["delete_sticker", "Deletes one specific stored sticker"],
        ["set_fallback_picture", "Sets fallback profile picture"],
        ["delete_fallback_picture", "Deletes fallback profile picture"],
        ["show_fallback_picture", "Shows current fallback profile picture"],
        ["set_timezone", "Sets the timezone used for the stickers"],
        [
            "toggle_text_direction",
            "Changes sticker text direction from right-to-left to left-to-right and vice versa",
        ],
    ]
    admin_commands = [
        ["ilq", "Show Statistics for inline requests"],
        ["text", "Show Statistics for text requests"],
    ]

    await application.bot.set_my_commands(base_commands)

    # For the admin we show stats commands
    await application.bot.set_my_commands(
        admin_commands + base_commands,
        scope=BotCommandScopeChat(chat_id=admin_id),
    )

    # Bot data
    application.bot_data[ADMIN_KEY] = admin_id
    application.bot_data[STICKER_CHAT_ID_KEY] = sticker_chat_id
