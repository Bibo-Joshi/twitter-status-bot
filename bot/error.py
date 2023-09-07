#!/usr/bin/env python3
"""Methods for error handlers."""
import html
import json
import logging
import traceback
from typing import cast

from telegram import InlineQueryResultsButton, Update
from telegram.error import BadRequest, Forbidden

from bot.constants import ADMIN_KEY
from bot.twitter import HyphenationError
from bot.userdata import CCT

logger = logging.getLogger(__name__)


async def hyphenation_error(update: object, context: CCT) -> None:
    """Handles hyphenation errors by informing the triggering user about them.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    if not isinstance(context.error, HyphenationError) or not isinstance(update, Update):
        return

    if update.inline_query:
        await update.inline_query.answer(
            results=[],
            button=InlineQueryResultsButton(
                text="Click me! 👆", start_parameter="hyphenation_error"
            ),
        )
        return
    if update.effective_message:
        await update.effective_message.reply_text(str(context.error))


async def error(update: object, context: CCT) -> None:
    """Informs the originator of the update that an error occurred and forwards the traceback to
    the admin.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    admin_id = cast(int, context.bot_data[ADMIN_KEY])

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if (
        isinstance(context.error, (HyphenationError, Forbidden))
        or (isinstance(context.error, BadRequest) and "Query is too old" in str(context.error))
        or context.error is None
    ):
        return

    # Inform sender of update, that something went wrong
    if isinstance(update, Update) and update.effective_message:
        text = "Something went wrong 😟. I informed the admin 🤓."
        await update.effective_message.reply_text(text)

    # Get traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message_1 = (
        f"An exception was raised while handling an update\n\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>"
    )
    message_2 = f"<pre>{html.escape(tb_string)}</pre>"

    # Finally, send the messages
    # We send update and traceback in two parts to reduce the chance of hitting max length
    sent_message = await context.bot.send_message(chat_id=admin_id, text=message_1)
    try:
        await sent_message.reply_html(message_2)
    except BadRequest as exc:
        if "too long" not in str(exc):
            raise exc
        message = (
            f"Hey.\nThe error <code>{html.escape(str(context.error))}</code> happened."
            f" The traceback is too long to send, but it was written to the log."
        )
        await context.bot.send_message(chat_id=admin_id, text=message)
