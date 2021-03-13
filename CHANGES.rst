=========
Changelog
=========

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
===========
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

* Include the `ptbstats <https://hirschheissich.gitlab.io/ptbstats/>`_ plugin for statistics

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