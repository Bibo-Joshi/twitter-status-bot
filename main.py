#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The script that runs the bot."""
import logging
from configparser import ConfigParser
from telegram import ParseMode
from telegram.ext import Updater, Defaults, PicklePersistence, Filters

from ptbstats import set_dispatcher, register_stats, SimpleStats

import bot

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='tsb.log')

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Read configuration values from bot.ini
    config = ConfigParser()
    config.read('bot.ini')
    token = config['TwitterStatusBot']['token']
    admin = int(config['TwitterStatusBot']['admins_chat_id'])

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    defaults = Defaults(parse_mode=ParseMode.HTML, disable_notification=True)
    persistence = PicklePersistence('tsb.pickle')
    updater = Updater(token,
                      use_context=True,
                      defaults=defaults,
                      persistence=persistence,
                      workers=8)

    # Set up stats
    set_dispatcher(updater.dispatcher)
    register_stats(SimpleStats('ilq', lambda u: bool(u.inline_query and u.inline_query.query)),
                   admin_id=admin)
    register_stats(SimpleStats(
        'text',
        lambda u: bool(u.effective_message and (Filters.private & Filters.text & ~Filters.command)
                       (u))),
                   admin_id=admin)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    bot.register_dispatcher(dp)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
