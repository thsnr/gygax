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
following_db = None

def reset(bot, config):
    if not config or "client_id" not in config:
        raise KeyError("no client_id provided")
    global client_id
    client_id = config["client_id"]

    global following_db
    following_db = config.get("following_db")
    if following_db:
        try:
            with open(following_db) as fp:
                for user_id, nicks in json.load(fp).items():
                    watchdog._following[user_id].update(nicks)
        except FileNotFoundError:
            pass  # Nothing saved yet.

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
        online = augment_streams(query("streams", "user_id", *user_ids))
        if not online:
            bot.reply("no users online")
            return
        for stream in online.values():
            bot.reply(format_stream(stream))

    elif command == "following":
        bot.reply(following(nick))

    elif command == "follow":
        if not args:
            bot.reply("which users to follow?")
            return
        for user_id in query("users", "login", *args, index="id"):
            watchdog._following[user_id].add(nick)
        save_following()
        bot.reply(following(nick))

    elif command == "unfollow":
        if not args:
            bot.reply("which users to unfollow?")
            return
        for user_id in query("users", "login", *args, index="id"):
            watchdog._following[user_id].remove(nick)
            if not watchdog._following[user_id]:
                del watchdog._following[user_id]
        save_following()
        bot.reply(following(nick))

    else:
        bot.reply("unknown command")

twitch.command = ".twitch"

def watchdog(bot):
    if watchdog._following:
        online = query("streams", "user_id", *watchdog._following.keys())
        fresh = {k: v for k, v in online.items() if k not in watchdog._last_online}
        for user_id, stream in augment_streams(fresh).items():
            for target in watchdog._following[user_id]:
                bot.message(target, format_stream(stream))
        watchdog._last_online = set(online.keys())

watchdog._following = collections.defaultdict(set)
watchdog._last_online = set()
watchdog.tick = 1

def save_following():
    if following_db:
        with open(following_db, "w") as fp:
            json.dump({k: list(v) for k, v in watchdog._following.items()}, fp)

def augment_streams(streams):
    # Resolve game ids to game names.
    game_ids = [stream["game_id"] for stream in streams.values() if "game_id" in stream]
    games = query("games", "id", *game_ids) if game_ids else {}

    # Augment stream information with "stream_url" and "game_name".
    for stream in streams.values():
        stream["stream_url"] = "https://twitch.tv/{}".format(stream.get("user_name").lower())
        stream["game_name"] = games.get(stream.get("game_id"), {}).get("name")

    return streams  # For chaining.

def format_stream(stream):
    return "{} ({}) is playing {} with title: {}".format(
            stream.get("user_name") or "[missing user_name?]",
            stream.get("stream_url") or "[missing stream_url?]",
            stream.get("game_name") or "[missing game_name?]",
            stream.get("title") or "[missing title?]")

def following(nick):
    user_ids = following_ids(nick)
    if not user_ids:
        return "you are not following any users"
    return "you are following: {}".format(", ".join(
           query("users", "id", *user_ids, index="display_name").keys()))

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
