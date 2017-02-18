# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.roll` --- Module for rolling dice.
======================================================
"""

import random

def roll_dice(count, size):
    return [random.randint(1, size) for _ in range(count)]

def format_results(results):
    return str(results[0]) if len(results) == 1 else "{} = {}".format(
            " + ".join(map(str, results)), sum(results))

def roll(bot, sender, text):
    if not text:
        bot.reply("roll what?")
        return
    if text == "stats":
        bot.reply(", ".join(map(str, sorted([sum(sorted(roll_dice(4, 6))[1:]) for _ in range(6)])[::-1])))
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

    results = roll_dice(count, size)
    bot.reply(format_results(roll_dice(count, size)))
roll.command = ".roll"
