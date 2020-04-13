# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.twitch` --- Track live streams on Twitch
============================================================
"""

import codecs
import collections
import json
from urllib import parse, request

from gygax import irc

client_id = None

def reset(bot, config):
    if not config or "client_id" not in config:
        raise KeyError("no client_id provided")
    global client_id
    client_id = config["client_id"]

def check_channels(*channels):
    # In the future we might want to use pagination, but currently 100 channels
    # is more than enough.
    logins = [("user_login", channel) for channel in channels]
    req = request.Request("https://api.twitch.tv/helix/streams?{}".format(
        parse.urlencode(logins + [("limit", 100)])))
    req.add_header("Client-ID", client_id)

    with request.urlopen(req) as resp:
        data = json.load(codecs.getreader("utf-8")(resp)).get("data")

    # Return a dict from an online channel's name to the channel's metadata.
    results = {}
    for stream in data:
        name = stream.get("user_name", "").lower()
        if name:
            results[name] = stream
    return results

def format_metadata(metadata):
    return "{} ({}) is online with title: {}".format(
            metadata.get("user_name"),
            "https://twitch.tv/{}".format(metadata.get("user_name").lower()),
            metadata.get("title", "[missing title?]"))

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
        results = check_channels(*check)
        if not results:
            bot.reply("no channels online")
            return
        for data in results.values():
            bot.reply(format_metadata(data))

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
        online = check_channels(*watchdog._following.keys())
        for channel in online:
            if channel not in watchdog._last_online:
                for target in watchdog._following[channel]:
                    bot.message(target, format_metadata(online[channel]))
        watchdog._last_online = set(online.keys())

# FIXME: Make _following persistent.
watchdog._following = collections.defaultdict(set)
watchdog._last_online = set()
watchdog.tick = 1

def following(nick):
    for channel, followers in watchdog._following.items():
        if nick in followers:
            yield channel
