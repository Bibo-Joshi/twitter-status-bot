#!/usr/bin/env python3
"""Methods for the inline mode."""
import logging
from asyncio import CancelledError, Event
from contextlib import suppress
from typing import Any, Dict, Union, cast
from uuid import uuid4

from telegram import (
    ChosenInlineResult,
    InlineQuery,
    InlineQueryResultCachedSticker,
    Sticker,
    Update,
    User,
)

from bot.constants import STICKER_CHAT_ID_KEY
from bot.userdata import CCT, UserData
from bot.utils import get_sticker_photo_stream

logger = logging.getLogger(__name__)


def _check_event(event: Event) -> None:
    if event.is_set():
        logger.debug("Sticker creation terminated because event was set")
        raise CancelledError("Sticker creation terminated because event was set")


async def inline_task(update: Update, context: CCT, event: Event) -> None:
    """Answers an inline query by providing the corresponding sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
        event: ``event.is_set()`` will be checked before the time consuming
            parts of the sticker creation and if the event is set, the creation will be terminated.
    """
    with suppress(CancelledError):  # suppress the know error
        inline_query = cast(InlineQuery, update.inline_query)
        user_data = cast(UserData, context.user_data)
        sticker_chat_id = cast(Union[int, str], context.bot_data[STICKER_CHAT_ID_KEY])

        # Read existing file_ids from user_data
        file_ids = list(user_data.sticker_file_ids.values())
        kwargs: Dict[str, Any] = {
            "results": [
                InlineQueryResultCachedSticker(id=f"tweet {i}", sticker_file_id=sticker_id)
                for i, sticker_id in enumerate(reversed(file_ids))
            ]
        }

        _check_event(event)
        # Build photo
        photo_stream = await get_sticker_photo_stream(
            inline_query.query, cast(User, update.effective_user), context
        )

        _check_event(event)
        # Send it to the dumpster chat to get the chat_id
        sticker = cast(
            Sticker, (await context.bot.send_sticker(sticker_chat_id, photo_stream)).sticker
        )
        file_unique_id, file_id = sticker.file_unique_id, sticker.file_id

        # Store the IDs so we can know which sticker was selected
        key = str(uuid4())
        user_data.temp_file_ids[key] = (file_unique_id, file_id)
        kwargs["results"].insert(
            0, InlineQueryResultCachedSticker(id=key, sticker_file_id=file_id)
        )

        _check_event(event)
        # Answer the inline query
        await inline_query.answer(**kwargs, is_personal=True, auto_pagination=True, cache_time=0)


async def inline(update: Update, context: CCT) -> None:
    """Answers an inline query by starting a task running :meth:`inline_task` and terminating
    any existing such task for the current user.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    user_data = cast(UserData, context.user_data)
    inline_query = cast(InlineQuery, update.inline_query)
    query = inline_query.query

    if query:
        task = user_data.inline_query_task
        if task and not task.done():
            cast(Event, user_data.inline_query_event).set()

        event = user_data.inline_query_event = Event()
        new_task = context.application.create_task(
            inline_task(update=update, context=context, event=event)
        )
        user_data.inline_query_event = event
        user_data.inline_query_task = new_task
    else:
        file_ids = list(user_data.sticker_file_ids.values())
        results = [
            InlineQueryResultCachedSticker(id=f"tweet {i}", sticker_file_id=sticker_id)
            for i, sticker_id in enumerate(reversed(file_ids))
        ]
        await inline_query.answer(
            results=results, is_personal=True, auto_pagination=True, cache_time=0
        )


async def handle_chosen_inline_result(update: Update, context: CCT) -> None:
    """
    Appends the chosen sticker ID to the users corresponding list.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the application.
    """
    user_data = cast(UserData, context.user_data)
    result_id = cast(ChosenInlineResult, update.chosen_inline_result).result_id
    if not result_id.startswith("tweet"):
        temp_dict = user_data.temp_file_ids
        cached = temp_dict.get(result_id)
        if cached and user_data.store_stickers:
            user_data.sticker_file_ids[cached[0]] = cached[1]
        temp_dict.clear()
