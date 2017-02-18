# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.gatherer` --- Module to track live channels on twitch.tv
============================================================================
"""

import codecs
import collections
import json
from urllib import parse, request

from gygax import irc

def check_channels(*channels):
    url = "https://api.twitch.tv/kraken/streams"
    mime = "application/vnd.twitchtv.v2+json"

    # In the future we might want to use pagination, but currently 100 channels
    # is more than enough.
    params = parse.urlencode({"channel": ",".join(channels), "limit": "100"})

    req = request.Request("{}?{}".format(url, params))
    req.add_header("Accept", mime)
    with request.urlopen(req) as f:
        utf8 = codecs.getreader("utf-8")
        data = json.load(utf8(f))

    # Return a dict from an online channel's name to the channel's metadata.
    results = {}
    for stream in data["streams"]:
        results[stream["channel"]["name"]] = stream["channel"]
    return results

def format_metadata(metadata):
    return "{} ({}) is online with status: {}".format(
            metadata["name"], metadata["url"], metadata["status"])

def twitch(bot, sender, text):
    words = text.split()
    if not len(words):
        bot.reply("missing command, use one of: " +
                "check, following, follow, unfollow")
        return

    command = words[0]
    args = words[1:]
    nick, _, _ = irc.split_name(sender)

    if command == "check":
        check = args if len(args) else list(following(nick))
        if not len(check):
            bot.reply("no channels to check")
            return
        results = check_channels(*check)
        if not len(results):
            bot.reply("no channels online")
            return
        for data in results.values():
            bot.reply(format_metadata(data))

    elif command == "following":
        channels = ", ".join(following(nick))
        if not len(channels):
            bot.reply("you are not following any channels")
            return
        bot.reply("you are following: " + channels)

    elif command == "follow":
        if not len(args):
            bot.reply("which channels to follow?")
            return
        for channel in args:
            watchdog._following[channel].add(nick)
        bot.reply("done")

    elif command == "unfollow":
        if not len(args):
            bot.reply("which channels to unfollow?")
            return
        for channel in args:
            watchdog._following[channel].remove(nick)
        bot.reply("done")

    else:
        bot.reply("unknown command")
twitch.command = ".twitch"

def watchdog(bot):
    if len(watchdog._following):
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
