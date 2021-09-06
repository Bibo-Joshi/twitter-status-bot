#!/usr/bin/env python3
"""Methods for the inline mode."""
import logging
from threading import Event, Thread
from typing import cast, Dict, Any, Union
from uuid import uuid4

from telegram import (
    Update,
    InlineQuery,
    InlineQueryResultCachedSticker,
    User,
    ChosenInlineResult,
    Sticker,
)

from bot.constants import STICKER_CHAT_ID_KEY
from bot.utils import get_sticker_photo_stream
from bot.userdata import CCT, UserData

logger = logging.getLogger(__name__)


def _check_event(event: Event) -> None:
    if event.is_set():
        logger.debug('Sticker creation terminated because event was set')
        raise RuntimeError('Sticker creation terminated because event was set')


def inline_thread(update: Update, context: CCT, event: Event) -> None:
    """Answers an inline query by providing the corresponding sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
        event: ``event.is_set()`` will be checked before the time consuming
            parts of the sticker creation and if the event is set, the creation will be terminated.
    """
    try:
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
        photo_stream = get_sticker_photo_stream(
            inline_query.query, cast(User, update.effective_user), context
        )

        _check_event(event)
        # Send it to the dumpster chat to get the chat_id
        sticker = cast(Sticker, context.bot.send_sticker(sticker_chat_id, photo_stream).sticker)
        file_unique_id, file_id = sticker.file_unique_id, sticker.file_id

        # Store the IDs so we can know which sticker was selected
        key = str(uuid4())
        user_data.temp_file_ids[key] = (file_unique_id, file_id)
        kwargs["results"].insert(
            0, InlineQueryResultCachedSticker(id=key, sticker_file_id=file_id)
        )

        _check_event(event)
        # Answer the inline query
        inline_query.answer(**kwargs, is_personal=True, auto_pagination=True, cache_time=0)
    except Exception as exc:  # pylint: disable=W0703
        if 'Sticker creation terminated' not in str(exc):
            context.dispatcher.dispatch_error(update=update, error=exc)


def inline(update: Update, context: CCT) -> None:
    """Answers an inline query by starting a thread running :meth:`inline_thread` and terminating
    any existing such thread for the current user.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    inline_query = cast(InlineQuery, update.inline_query)
    query = inline_query.query

    if query:
        thread = user_data.inline_query_thread
        if thread and thread.is_alive():
            cast(Event, user_data.inline_query_event).set()
            thread.join()

        event = user_data.inline_query_event = Event()
        new_thread = Thread(
            name=f'{cast(User, update.effective_user).id}{query}',
            target=inline_thread,
            kwargs={'update': update, 'context': context, 'event': event},
        )
        new_thread.start()
        user_data.inline_query_event = event
        user_data.inline_query_thread = new_thread
    else:
        file_ids = list(user_data.sticker_file_ids.values())
        results = [
            InlineQueryResultCachedSticker(id=f"tweet {i}", sticker_file_id=sticker_id)
            for i, sticker_id in enumerate(reversed(file_ids))
        ]
        inline_query.answer(results=results, is_personal=True, auto_pagination=True, cache_time=0)


def handle_chosen_inline_result(update: Update, context: CCT) -> None:
    """
    Appends the chosen sticker ID to the users corresponding list.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    result_id = cast(ChosenInlineResult, update.chosen_inline_result).result_id
    if not result_id.startswith("tweet"):
        temp_dict = user_data.temp_file_ids
        cached = temp_dict.get(result_id)
        if cached and user_data.store_stickers:
            user_data.sticker_file_ids[cached[0]] = cached[1]
        temp_dict.clear()
