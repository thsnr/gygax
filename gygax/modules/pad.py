# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.pad` --- Module for creating pads on collabedit.com
=======================================================================
"""

import dbm
from http import client

from gygax.modules import admin

def pad(bot, sender, text):
    key = text.encode("utf-8")
    with dbm.open("pad", "c") as db:
        if key in db:
            bot.reply(db[key].decode("utf-8"))
            return

        if not admin.is_admin(sender):
            bot.reply("not authorized to create new pad")
            return

        # We can't use urllib, because collabedit uses weird redirects which
        # make urllib think we are redirected in an endless loop.
        conn = client.HTTPConnection("collabedit.com")
        conn.request("GET", "/new")
        r1 = conn.getresponse()
        if r1.status != 302:
            raise Exception("GET /new returned {} {}".format(r1.status, r1.reason))
        headers = {"Cookie": r1.getheader("Set-Cookie").split(";")[0]}
        r1.read() # Read the response body so we can make a new request.

        conn.request("GET", r1.getheader("Location"), headers=headers)
        r2 = conn.getresponse()
        if r2.status != 302:
            raise Exception("GET {} returned {} {}".format(
                r1.getheader("Location"), r2.status, r2.reason))
        conn.close()

        link = "http://collabedit.com{}".format(r2.getheader("Location"))
        db[key] = link.encode("utf-8")
        bot.reply(link)
pad.command = ".pad"
