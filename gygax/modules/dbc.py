# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.dbc` --- Module for playing Dragon-Blood-Clan.
==================================================================
"""

from gygax.modules import roll

def dbc(bot, sender, text):
    need = 6       # The next die needed.
    dice_count = 5 # The number of dice to roll.
    rolls_left = 3 # The number of rolls left.
    reply = []     # The reply to the sender.

    # Roll until we have 6, 5 and 4 or we run out of rolls.
    while need > 3 and rolls_left > 0:
        results = roll.roll_dice(dice_count, 6)
        reply.append("[{}]".format(
            ", ".join(map(str, reversed(sorted(results))))))
        rolls_left -= 1

        # Check for needed dice
        while need > 3 and need in results:
            results.remove(need)
            need -= 1
            dice_count -= 1

    if need > 3:
        reply.append("no luck")
    else:
        reply.append("score: {}".format(sum(results)))
        reply.append("rolls left: {}".format(rolls_left))
    bot.reply(", ".join(reply))
dbc.command = ".dbc"
