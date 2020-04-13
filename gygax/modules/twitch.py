# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.twitch` --- Track live streams on Twitch
============================================================
"""

import codecs
import collections
import json
import logging
from urllib import parse, request

from gygax import irc

log = logging.getLogger("gygax.modules.twitch")

client_id = None

def reset(bot, config):
    if not config or "client_id" not in config:
        raise KeyError("no client_id provided")
    global client_id
    client_id = config["client_id"]

def twitch(bot, sender, text):
    words = text.split()
    if not words:
        bot.reply("missing command, use one of: " +
                "check, following, follow, unfollow")
        return

    command, args = words[0], words[1:]
    nick, _, _ = irc.split_name(sender)

    if command == "check":
        check = args or list(following(nick))
        if not check:
            bot.reply("no channels to check")
            return
        online = query("streams", "user_login", *check)
        if not online:
            bot.reply("no channels online")
            return
        for stream in online.values():
            bot.reply(format_stream(stream))

    elif command == "following":
        channels = ", ".join(following(nick))
        if not channels:
            bot.reply("you are not following any channels")
            return
        bot.reply("you are following: " + channels)

    elif command == "follow":
        if not args:
            bot.reply("which channels to follow?")
            return
        for channel in args:
            watchdog._following[channel].add(nick)
        bot.reply("done")

    elif command == "unfollow":
        if not args:
            bot.reply("which channels to unfollow?")
            return
        for channel in args:
            watchdog._following[channel].remove(nick)
        bot.reply("done")

    else:
        bot.reply("unknown command")

twitch.command = ".twitch"

def watchdog(bot):
    if watchdog._following:
        online = query("streams", "user_login", *watchdog._following.keys(), index="user_name")
        for channel, stream in online.values():
            if channel not in watchdog._last_online:
                for target in watchdog._following[channel.lower()]:
                    bot.message(target, format_stream(stream))
        watchdog._last_online = set(online.keys())

# FIXME: Make _following persistent.
watchdog._following = collections.defaultdict(set)
watchdog._last_online = set()
watchdog.tick = 1

def format_stream(stream):
    return "{} ({}) is online with title: {}".format(
            stream.get("user_name"),
            "https://twitch.tv/{}".format(stream.get("user_name").lower()),
            stream.get("title", "[missing title?]"))

def following(nick):
    for channel, followers in watchdog._following.items():
        if nick in followers:
            yield channel

def query(what, field, *values, index=None):
    # In the future we might want to use pagination, but currently limit all
    # requests to 100 responses.

    filters = [(field, value) for value in values]
    req = request.Request("https://api.twitch.tv/helix/{}?{}".format(
        what, parse.urlencode(filters + [("limit", 100)])))
    req.add_header("Client-ID", client_id)

    log.debug(req.full_url)
    with request.urlopen(req) as resp:
        data = json.load(codecs.getreader("utf-8")(resp)).get("data", [])

    results = {}
    index = index or field
    for result in data:
        if index in result:
            results[result[index]] = result
    return results
