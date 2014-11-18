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
        bot.reply('First %s results:' % LIMIT)
        for result in results:
            bot.reply("%s (%s)" % (result['name'], result['url']))
    else:
        bot.reply('No results found!')

    return

def search(q):
    req = request.Request("http://gatherer.wizards.com/Pages/Search/Default.aspx?name=+[%s]" % q)

    resultsArray = []

    try:
        response = request.urlopen(req)
        html = response.read()
        soup = BeautifulSoup(html)

        resultsContainer = soup.find("div", attrs = {"id": 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_searchResultsContainer'})
        if resultsContainer.contents:
            results = resultsContainer.find_all('div', attrs = { "class": 'cardInfo' })
            for result in results:
                name = result.find('span', {'class': 'cardTitle'}).find('a').text
                url = result.find('span', {'class': 'cardTitle'}).find('a')['href'].replace('../', 'http://gatherer.wizards.com/Pages/')
                resultsArray += [{'name': name, 'url': url}]
        return resultsArray

    except:
        return []

gatherer.command = ".gatherer"
