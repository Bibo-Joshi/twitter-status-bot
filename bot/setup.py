#!/usr/bin/env python3
"""Methods for initializing the dispatcher."""
import warnings
from typing import Union

from ptbstats import set_dispatcher, register_stats, SimpleStats
from telegram import BotCommandScopeChat
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    InlineQueryHandler,
    ChosenInlineResultHandler,
)

from bot.constants import ADMIN_KEY, STICKER_CHAT_ID_KEY
from bot.deletesticker import delete_sticker_conversation
from bot.setfallbackpicture import set_fallback_picture_conversation
from bot.settimezone import build_set_timezone_conversation
from bot.utils import default_message
from bot.commands import (
    info,
    sticker_message,
    toggle_store_stickers,
    show_fallback_picture,
    delete_fallback_picture,
    toggle_text_direction,
)
from bot.error import hyphenation_error, error
from bot.inline import inline, handle_chosen_inline_result
from bot.userdata import CCT, UserData

# B/C we know what we're doing
warnings.filterwarnings('ignore', message="If 'per_", module='telegram.ext.conversationhandler')
warnings.filterwarnings(
    'ignore',
    message=".*does not handle objects that can not be copied",
    module='telegram.ext.basepersistence',
)


def setup_dispatcher(
    dispatcher: Dispatcher[CCT, UserData, dict, dict],
    admin_id: int,
    sticker_chat_id: Union[str, int],
) -> None:
    """
    Adds handlers and sets up ``bot_data``. Also sets the bot commands.

    Args:
        dispatcher: The :class:`telegram.ext.Dispatcher`.
        admin_id: The admins chat id.
        sticker_chat_id: The name of the chat where stickers can be sent to get their file IDs.
    """
    # error handlers
    dispatcher.add_error_handler(hyphenation_error)
    dispatcher.add_error_handler(error)

    # Set up stats
    set_dispatcher(dispatcher)
    register_stats(
        SimpleStats("ilq", lambda u: bool(u.chosen_inline_result)),
        admin_id=admin_id,
    )
    register_stats(
        SimpleStats(
            "text",
            lambda u: bool(
                u.effective_message
                and (Filters.chat_type.private & Filters.text & ~Filters.command)(u)
            ),
        ),
        admin_id=admin_id,
    )

    # basic command handlers
    dispatcher.add_handler(CommandHandler(["start", "help"], info))
    dispatcher.add_handler(CommandHandler('toggle_store_stickers', toggle_store_stickers))
    dispatcher.add_handler(CommandHandler('toggle_text_direction', toggle_text_direction))
    dispatcher.add_handler(delete_sticker_conversation)
    dispatcher.add_handler(set_fallback_picture_conversation)
    dispatcher.add_handler(build_set_timezone_conversation(dispatcher.bot))
    dispatcher.add_handler(CommandHandler('delete_fallback_picture', delete_fallback_picture))
    dispatcher.add_handler(CommandHandler('show_fallback_picture', show_fallback_picture))

    # functionality
    dispatcher.add_handler(
        MessageHandler(Filters.text & Filters.chat_type.private, sticker_message)
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.all & Filters.chat_type.private & ~Filters.via_bot(dispatcher.bot.id),
            default_message,
        )
    )
    dispatcher.add_handler(InlineQueryHandler(inline))
    dispatcher.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))

    # Bot commands
    base_commands = [
        ["help", "Displays a short info message about the Twitter Status Bot"],
        ["start", 'See "/help"'],
        ['toggle_store_stickers', '(De)activates the saving of stickers'],
        ['delete_sticker', 'Deletes one specific stored sticker'],
        ['set_fallback_picture', 'Sets fallback profile picture'],
        ['delete_fallback_picture', 'Deletes fallback profile picture'],
        ['show_fallback_picture', 'Shows current fallback profile picture'],
        ['set_timezone', 'Sets the timezone used for the stickers'],
        [
            'toggle_text_direction',
            'Changes sticker text direction from right-to-left to left-to-right and vice versa',
        ],
    ]
    admin_commands = [
        ["ilq", "Show Statistics for inline requests"],
        ["text", "Show Statistics for text requests"],
    ]

    dispatcher.bot.set_my_commands(base_commands)
    # For the admin, we show stats commands

    dispatcher.bot.set_my_commands(
        admin_commands + base_commands,
        scope=BotCommandScopeChat(chat_id=admin_id),
    )

    # Bot data
    dispatcher.bot_data[ADMIN_KEY] = admin_id
    dispatcher.bot_data[STICKER_CHAT_ID_KEY] = sticker_chat_id
