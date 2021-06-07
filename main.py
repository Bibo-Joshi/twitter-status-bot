#!/usr/bin/env python3
"""The script that runs the bot."""
import logging
from configparser import ConfigParser
from typing import cast, Dict

from telegram import ParseMode
from telegram.ext import Updater, Defaults, PicklePersistence, ContextTypes

from bot.setup import setup_dispatcher
from bot.userdata import UserData, CCT

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    # filename="tsb.log",
)
aps_logger = logging.getLogger('apscheduler')
aps_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Read configuration values from bot.ini
    config = ConfigParser()
    config.read("bot.ini")
    token = config["TwitterStatusBot"]["token"]
    admin_id = int(config["TwitterStatusBot"]["admins_chat_id"])
    sticker_set_name = config["TwitterStatusBot"]["sticker_set_name"]

    defaults = Defaults(parse_mode=ParseMode.HTML, disable_notification=True, run_async=True)
    # Cast due to a type hinting bug in ptb v13.6
    context_types = cast(ContextTypes[CCT, UserData, Dict, Dict], ContextTypes(user_data=UserData))
    persistence = PicklePersistence("tsb.pickle", context_types=context_types, single_file=False)
    updater = Updater(
        token,
        defaults=defaults,
        persistence=persistence,
        workers=8,
        context_types=context_types,
    )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    setup_dispatcher(dispatcher, admin_id, sticker_set_name)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
