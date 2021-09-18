#!/usr/bin/env python3
"""The script that runs the bot."""
import logging
from configparser import ConfigParser

from telegram import ParseMode
from telegram.ext import Updater, Defaults, PicklePersistence, ContextTypes

from bot.setup import setup_dispatcher
from bot.userdata import UserData

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
    sticker_chat_id = config["TwitterStatusBot"]["sticker_chat_id"]

    defaults = Defaults(parse_mode=ParseMode.HTML, disable_notification=True, run_async=True)
    context_types = ContextTypes(user_data=UserData)
    persistence = PicklePersistence(
        "tsb.pickle", context_types=context_types, single_file=False, store_chat_data=False
    )
    updater = Updater(
        token,
        defaults=defaults,
        persistence=persistence,
        workers=8,
        context_types=context_types,
    )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    setup_dispatcher(dispatcher, admin_id, sticker_chat_id)

    # Start the Bot
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
