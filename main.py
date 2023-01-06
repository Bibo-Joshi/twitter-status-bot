#!/usr/bin/env python3
"""The script that runs the bot."""
import functools
import logging
from configparser import ConfigParser

from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ContextTypes,
    Defaults,
    PersistenceInput,
    PicklePersistence,
)

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
        .post_init(
            functools.partial(
                setup_application, admin_id=admin_id, sticker_chat_id=sticker_chat_id
            )
        )
        .rate_limiter(
            # Don't apply rate limiting, but retry on `RetryAfter` errors
            AIORateLimiter(
                overall_max_rate=0,
                overall_time_period=0,
                group_max_rate=0,
                group_time_period=0,
                max_retries=3,
            )
        )
        .build()
    )

    # Start the Bot
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
