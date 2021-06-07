#!/usr/bin/env python3
"""Methods for the inline mode."""
from typing import cast, Dict, Any
from uuid import uuid4

from telegram import Update, InlineQuery, InlineQueryResultCachedSticker, User, ChosenInlineResult

from bot.utils import get_sticker_id
from bot.userdata import CCT, UserData


def inline(update: Update, context: CCT) -> None:
    """
    Answers an inline query by providing the requested sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    user_data = cast(UserData, context.user_data)
    user_data.increase_inline_query_count()

    inline_query = cast(InlineQuery, update.inline_query)
    query = inline_query.query

    file_ids = list(user_data.sticker_file_ids.values())
    kwargs: Dict[str, Any] = {
        "results": [
            InlineQueryResultCachedSticker(id=f"tweet {i}", sticker_file_id=sticker_id)
            for i, sticker_id in enumerate(reversed(file_ids))
        ]
    }

    if query:
        file_unique_id, file_id = get_sticker_id(
            inline_query.query, cast(User, update.effective_user), context
        )
        key = str(uuid4())
        user_data.temp_file_ids[key] = (file_unique_id, file_id)
        kwargs["results"].insert(
            0, InlineQueryResultCachedSticker(id=key, sticker_file_id=file_id)
        )

    if user_data.get_inline_query_count() <= 1:
        inline_query.answer(**kwargs, is_personal=True, auto_pagination=True, cache_time=0)

    user_data.decrease_inline_query_count()


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
