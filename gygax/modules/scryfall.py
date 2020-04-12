# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.scryfall` --- Search Magic: The Gathering cards
===================================================================
"""

import codecs
import json
from urllib import error, parse, request

def mtg(bot, sender, text):
    def callback(resp):
        data = json.load(codecs.getreader("utf-8")(resp))
        reply_url(bot, data)

    if not named(text, "json", callback):
        # Probably too ambiguous, fall back to full search.
        mtgq(bot, sender, text)

mtg.command = ".mtg"

def mtgtext(bot, sender, text):
    def callback(resp):
        for line in codecs.getreader("utf-8")(resp).readlines():
            bot.reply(line.strip())

    if not named(text, "text", callback):
        # Probably too ambiguous, fall back to full search.
        mtgq(bot, sender, text)

mtgtext.command = ".mtgtext"

def named(card, fmt, callback):
    req = request.Request("https://api.scryfall.com/cards/named?{}".format(
        parse.urlencode({"fuzzy": card, "format": fmt})))
    try:
        with request.urlopen(req) as resp:
            callback(resp)
            return True
    except error.HTTPError:
        return False

def mtgq(bot, sender, text):
    params = parse.urlencode({"q": text})
    req = request.Request("https://api.scryfall.com/cards/search?{}".format(params))
    try:
        with request.urlopen(req) as resp:
            data = json.load(codecs.getreader("utf-8")(resp))
            total = data.get("total_cards", 0)
            data = data.get("data", None)
    except error.HTTPError:
        bot.reply("nothing found")
        return

    limit = 3
    for card in data[:limit]:
        reply_url(bot, card)
    if total > limit:
        bot.reply("see {} more at {}".format(
            total - limit,
            "https://scryfall.com/search?{}".format(params)))

mtgq.command = ".mtgq"

def reply_url(bot, data):
    bot.reply("{} ({})".format(
        data.get("name", "[missing name?]"),
        data.get("scryfall_uri", "[missing url?]")))
