#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Methods for the bot functionality."""
import logging
import traceback
import html
from configparser import ConfigParser
from tempfile import NamedTemporaryFile

from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot, StickerSet,
                      ChatAction, User, InlineQueryResultCachedSticker)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Dispatcher, CommandHandler, MessageHandler, Filters, \
    InlineQueryHandler
from telegram.utils.helpers import mention_html
from emoji import emojize

from twitter import build_sticker

config = ConfigParser()
config.read('bot.ini')

logger = logging.getLogger(__name__)

ADMIN: int = int(config['TwitterStatusBot']['admins_chat_id'])
""":obj:`int`: Chat ID of the admin as read from ``bot.ini``."""
STICKER_SET_NAME: str = config['TwitterStatusBot']['sticker_set_name']
""":obj:`str`: The name of the sticker set used to generate the sticker as read from
``bot.ini``."""
HOMEPAGE: str = 'https://hirschheissich.gitlab.io/twitter-status-bot/'
""":obj:`str`: Homepage of this bot."""


def info(update: Update, context: CallbackContext) -> None:
    """
    Returns some info about the bot.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    text = emojize(('I\'m <b>Twitter Status Bot</b>. My profession is generating custom stickers '
                    ' looking like tweets.'
                    '\n\nTo learn more about me, please visit my homepage '
                    ':slightly_smiling_face:.'),
                   use_aliases=True)

    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(emojize('Twitter Status Bot :robot_face:', use_aliases=True),
                             url=HOMEPAGE))

    update.message.reply_text(text, reply_markup=keyboard)


def error(update: Update, context: CallbackContext) -> None:
    """
    Informs the originator of the update that an error occured and forwards the traceback to the
    admin.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # Inform sender of update, that something went wrong
    if update.effective_message:
        text = emojize('Something went wrong :worried:. I informed the admin :nerd_face:.',
                       use_aliases=True)
        update.effective_message.reply_text(text)

    # Get traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    trace = ''.join(tb_list)

    # Gather information from the update
    payload = ''
    if update.effective_user:
        payload += ' with the user {}'.format(
            mention_html(update.effective_user.id, update.effective_user.first_name))
    if update.effective_chat.username:
        payload += f' (@{html.escape(update.effective_chat.username)})'
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    text = f'Hey.\nThe error <code>{html.escape(str(context.error))}</code> happened' \
           f'{payload}. The full traceback:\n\n<code>{html.escape(trace)}</code>'

    # Send to admin
    context.bot.send_message(ADMIN, text)


def build_sticker_set_name(bot: Bot) -> str:
    """
    Builds the sticker set name given by ``STICKER_SET_NAME`` for the given bot.

    Args:
        bot: The Bot owning the sticker set.

    Returns:
        str
    """
    return '{}_by_{}'.format(STICKER_SET_NAME, bot.username)


def get_sticker_set(bot: Bot, name: str) -> StickerSet:
    """
    Get's the sticker set and creates it, if needed.

    Args:
        bot: The Bot owning the sticker set.
        name: The name of the sticker set.

    Returns:
        StickerSet
    """
    try:
        return bot.get_sticker_set(name)
    except BadRequest as e:
        if 'invalid' in str(e):
            with open('./logo/TwitterStatusBot-round.png', 'rb') as sticker:
                bot.create_new_sticker_set(ADMIN, name, STICKER_SET_NAME, '🐦', png_sticker=sticker)
            return bot.get_sticker_set(name)
        else:
            raise e


def clean_sticker_set(bot: Bot) -> None:
    """
    Cleans up the sticker set, i.e. deletes all but the first sticker.

    Args:
        bot: The bot.
    """
    sticker_set = get_sticker_set(bot, build_sticker_set_name(bot))
    if len(sticker_set.stickers) > 1:
        for sticker in sticker_set.stickers[1:]:
            try:
                bot.delete_sticker_from_set(sticker.file_id)
            except BadRequest as e:
                if 'Stickerset_not_modified' in str(e):
                    pass
                else:
                    raise e


def get_sticker_id(text: str, user: User, context: CallbackContext) -> str:
    """
    Gives the sticker ID for the requested sticker.

    Args:
        text: The text to display on the tweet.
        user: The user the tweet is created for.
        context: The callback context as provided by the dispatcher.

    Returns:
        str: The stickers file ID
    """
    bot = context.bot

    clean_sticker_set(context.bot)

    sticker_set_name = build_sticker_set_name(bot)
    emojis = '🐦'

    with NamedTemporaryFile(suffix='.png', delete=False) as file:
        sticker = build_sticker(text, user, context)
        sticker.save(file.name)
        file.close()

        get_sticker_set(bot, sticker_set_name)
        bot.add_sticker_to_set(ADMIN, sticker_set_name, emojis, png_sticker=open(file.name, 'rb'))

    sticker_set = get_sticker_set(bot, sticker_set_name)
    sticker_id = sticker_set.stickers[-1].file_id

    return sticker_id


def message(update: Update, context: CallbackContext) -> None:
    """
    Answers a text message by providing the requested sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    msg = update.effective_message
    context.bot.send_chat_action(update.effective_user.id, ChatAction.UPLOAD_PHOTO)
    file_id = get_sticker_id(msg.text, update.effective_user, context)
    msg.reply_sticker(file_id)
    clean_sticker_set(context.bot)


def inline(update: Update, context: CallbackContext) -> None:
    """
    Answers an inline query by providing the requested sticker.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    query = update.inline_query.query

    if not query:
        return
    else:
        file_id = get_sticker_id(update.inline_query.query, update.effective_user, context)

    update.inline_query.answer(
        [InlineQueryResultCachedSticker(id='tweet', sticker_file_id=file_id)],
        is_personal=True,
    )
    clean_sticker_set(context.bot)


def default_message(update: Update, context: CallbackContext) -> None:
    """
    Answers any message with a note that it could not be parsed.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    update.effective_message.reply_text('Sorry, but I can only text messages. '
                                        'Send "/help" for more information.')


def register_dispatcher(disptacher: Dispatcher) -> None:
    """
    Adds handlers. Convenience method to avoid doing that all in the main script.
    Also sets the bot commands.

    Args:
        disptacher: The :class:`telegram.ext.Dispatcher`.
    """
    dp = disptacher

    # error handler
    dp.add_error_handler(error)

    # basic command handlers
    dp.add_handler(CommandHandler(['start', 'help'], info))

    # functionality
    dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_handler(MessageHandler(Filters.all, default_message))
    dp.add_handler(InlineQueryHandler(inline))

    # Bot commands
    dp.bot.set_my_commands([['help', 'Displays a short info message about the Twitter Status Bot'],
                            ['start', 'See "/help"']])
