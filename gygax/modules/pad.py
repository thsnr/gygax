# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.pad` --- Module for creating pads on collabedit.com
=======================================================================
"""

from http import client

from gygax.modules import admin

def pad(bot, sender, text):
    if not admin.is_admin(sender):
        bot.reply("unauthorized")
        return

    # We can't use urllib, because collabedit uses weird redirects which make
    # urllib think we are redirected in an endless loop.
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
    bot.reply("http://collabedit.com{}".format(r2.getheader("Location")))
    conn.close()
pad.command = ".pad"
