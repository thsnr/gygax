# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.admin` --- Module for administrative tasks.
=================================================================
"""

def is_admin(sender):
    # Totally secure authorization method :)
    return sender.endswith("@tiit.users.quakenet.org")

def quit(bot, sender, text):
    if not is_admin(sender):
        bot.reply("unauthorized")
        return
    bot.quit(text) if len(text) else bot.quit()
quit.command = ".quit"

def load(bot, sender, module):
    if not is_admin(sender):
        bot.reply("unauthorized")
        return
    if bot._load_module(module):
        bot.reply("loaded module " + module)
    else:
        bot.reply("failed to load module " + module)
load.command = ".load"
