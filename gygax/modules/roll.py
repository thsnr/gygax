# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.roll` --- Module for rolling dice.
=================================================================
"""

import random

def roll(bot, sender, text):
    if not text:
        bot.reply(".roll what?")
        return
    try:
        count, size = text.split("d", 1)
        count = int(count) if len(count) else 1
        size = int(size)
        if count < 1 or count > 10 or size < 1 or size > 100:
            raise ValueError
    except ValueError:
        bot.reply("invalid die")
        return

    results = []
    for i in range(count):
        results.append(random.randint(1, size))
    bot.reply(str(results[0]) if count == 1 else "{} = {}".format(
            " + ".join(map(str, results)), sum(results)))
roll.command = ".roll"
