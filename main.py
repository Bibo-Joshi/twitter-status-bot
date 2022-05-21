#!/usr/bin/env python3
"""The script that runs the bot."""
import asyncio
import logging
from configparser import ConfigParser

from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, Defaults, PersistenceInput, PicklePersistence

from bot.setup import setup_application
from bot.userdata import UserData

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="tsb.log",
)
aps_logger = logging.getLogger("apscheduler")
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

    defaults = Defaults(parse_mode=ParseMode.HTML, disable_notification=True, block=False)
    context_types = ContextTypes(user_data=UserData)
    persistence = PicklePersistence(
        "tsb.pickle",
        context_types=context_types,
        single_file=False,
        store_data=PersistenceInput(chat_data=False),
    )
    application = (
        Application.builder()
        .token(token)
        .defaults(defaults)
        .persistence(persistence)
        .context_types(context_types)
        .build()
    )

    # Get the application to register handlers
    asyncio.get_event_loop().run_until_complete(
        setup_application(application, admin_id, sticker_chat_id)
    )

    # Start the Bot
    application.run_polling(drop_pending_updates=True, close_loop=False)


if __name__ == "__main__":
    main()
