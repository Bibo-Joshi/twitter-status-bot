=========
Changelog
=========

Version 3.1
===========
*Released 2023-01-01*

* Upgrade ``python-telegram-bot`` to v20.0
* Upgrade ``ptbstats`` to v2.1
* Fix a bug where the ``toggle_store_stickers`` setting was not respected for text stickers
* Improve the error handler

Version 3.0
===========
*Released 2022-05-22*

* Upgrade ``python-telegram-bot`` to v20.0a0 introducing ``asyncio``.
* Upgrade ``ptbstats`` to v2.0, which is not backwards compatible.

Version 2.2.1
=============
*Released 2021-09-18*

Fixes some minor bugs.

Version 2.2
===========
*Released 2021-09-18*

**New Features:**

* Select a custom timezone via ``/set_timezone``
* Switch between left-to-right and right-to-left text via ``/toggle_text_direction``

Version 2.1
===========
*Released 2021-09-06*

**Major Changes:**

* Use the ``send_sticker`` method again instead of adding stickers to a sticker set. This reduces the number of requests required to create one sticker and should make the bot more stable.
* When a new inline query comes in while another one is still processed, terminate the creation of the first sticker as quickly as possible.

Version 2.0.1
=============
*Released 2021-07-02*

**Bug fixes:**

* Fix multiline tweets

**Minor changes:**

* Update error handling
* Update Code Quality Checks

Version 2.0
===========
*Released 2021-07-01*

**New Features:**

* Set/show/delete fallback picture when the bot can't access your profile picture (because there is none or due to privacy settings)
* Toggle whether or not to save sent stickers
* Delete selected saved stickers

**Major Changes:**

* Rearranged a lot of internals
* Upgraded to PTB v13.7
* Don't answer inline queries if there is already a new one for the user

Version 1.5.2
=============
*Released 2021-03-13*

**New Features:**

* Remember generated stickers and suggest them in inline mode

**Minor changes:**

* Bump dependencies
* Improve error handler
* Use bytes stream instead of temporary files

Version 1.5.1
=============
*Released 2020-08-24*

**Minor changes:**

* Update PTB to v13.0
* Update ``ptbstats`` to v1.3
* Handle hyphenation errors by warning users
* Handle flood control errors by going to sleep

Version 1.5
===========
*Released 2020-08-24*

**Minor changes:**

* Update ``ptbstats`` to v1.2
* Don't accept empty inline queries for stats
* Handle exceptions for updates without ``effective_chat`` better

Version 1.4
===========
*Released 2020-08-16*

**Enhancements:**

* Include the `ptbstats <https://bibo-joshi.github.io/ptbstats/>`_ plugin for statistics

Version 1.3
===========
*Released 2020-07-26*

**Bug fixes:**

* Handle messages only when in private chat. The bot apparently was added to some channels, but that just doesn't make any sense.
* Fix failing of documentation build

Version 1.2
===========
*Released 2020-07-18*

Bug fixes:

* Make deletion of stickers from set even more robust
* Handle edited messages

Version 1.1
===========
*Released 2020-06-20*

Bug fixes:

* Make inline results personal for each user
* Make deletion of stickers from set more robust

Version 1.0
===========
*Released 2020-06-19*

Initial release. Adds basic functionality.