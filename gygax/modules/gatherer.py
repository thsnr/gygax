# -*- coding: utf-8 -*-

"""
:mod:`gygax.modules.gatherer` --- Module to search from gatherer.wizards.com
=================================================================
"""

from urllib import request
from bs4 import BeautifulSoup


def gatherer(bot, sender, text):
    LIMIT = 5
    results = search(text)[0:LIMIT]

    if results:
        bot.reply("First %s results:" % LIMIT)
        for result in results:
            bot.reply("%s (%s)" % (result["name"], result["url"]))
    else:
        bot.reply("No results found!")

    return


def search(q):
    q = "".join(["+[%s]" % word for word in q.split(" ")])

    base_url = "http://gatherer.wizards.com/Pages/Search/Default.aspx"

    try:
        req = request.Request("%s?name=%s" % (base_url, q))
        response = request.urlopen(req)

        if (response.geturl().startswith(base_url)):
            resultsArray = []

            html = response.read()
            soup = BeautifulSoup(html)

            resultsContainerId = \
                "ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_searchResultsContainer"
            resultsContainer = soup.find("div", attrs={"id": resultsContainerId})

            if resultsContainer.contents:
                results = resultsContainer.find_all("div", attrs={"class": "cardInfo"})

                for result in results:
                    name = result.find("span", {"class": "cardTitle"}).find("a").text
                    url = result.find("span", {"class": "cardTitle"}).find("a")["href"]
                    url = url.replace("../", "http://gatherer.wizards.com/Pages/")

                    resultsArray += [{"name": name, "url": url}]
            return resultsArray
        else:   # request was redirected
            html = response.read()
            soup = BeautifulSoup(html)

            try:
                url = response.geturl()
                name = soup.find("div", attrs={"class": "contentTitle"}).find("span").contents[0]

                return [{"name": name, "url": url}]
            except:
                return []
    except:
        return []

gatherer.command = ".mtg"
