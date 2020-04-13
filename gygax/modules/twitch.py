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
        if args:
            user_ids = query("users", "login", *args, index="id").keys()
        else:
            user_ids = following_ids(nick)
        if not user_ids:
            bot.reply("no users to check")
            return
        online = query("streams", "user_id", *user_ids)
        if not online:
            bot.reply("no users online")
            return
        for stream in online.values():
            bot.reply(format_stream(stream))

    elif command == "following":
        user_ids = following_ids(nick)
        if not user_ids:
            bot.reply("you are not following any channels")
            return
        bot.reply("you are following: {}".format(", ".join(
            query("users", "id", *user_ids, index="display_name").keys()))

    elif command == "follow":
        if not args:
            bot.reply("which users to follow?")
            return
        for user_id in query("users", "login", *args, index="id"):
            watchdog._following[user_id].add(nick)
        bot.reply("done")

    elif command == "unfollow":
        if not args:
            bot.reply("which users to unfollow?")
            return
        for user_id in query("users", "login", *args, index="id"):
            watchdog._following[user_id].remove(nick)
            if not watchdog._following[user_id]:
                del watchdog._following[user_id]
        bot.reply("done")

    else:
        bot.reply("unknown command")

twitch.command = ".twitch"

def watchdog(bot):
    if watchdog._following:
        online = query("streams", "user_id", *watchdog._following.keys())
        for user_id, stream in online.values():
            if user_id not in watchdog._last_online:
                for target in watchdog._following[user_id]:
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

def following_ids(nick):
    return [user_id for user_id, nicks in watchdog._following.items() if nick in nicks]

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
