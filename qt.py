#!/usr/bin/python
# encoding: utf-8

import sys

from workflow import Workflow, web
from bs4 import BeautifulSoup

# Constants
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
SECONDS_PER_DAY = SECONDS_PER_MINUTE * MINUTES_PER_HOUR * HOURS_PER_DAY
CACHE_EXPIRATION = 7 * SECONDS_PER_DAY # 7 days should be good

# URLs
DOC_URL = 'http://doc.qt.io/qt-5/'
CLASSES_URL = DOC_URL + 'classes.html'
SEARCH_URL = DOC_URL + 'search-results.html?q='

# Shown in error logs. Users can find help here
HELP_URL = 'https://github.com/Atlante45/alfred-qtdoc'

UPDATE_SETTINGS = {'github_slug': 'Atlante45/alfred-qtdoc'}

log = None

def request_classes():
    r = web.get(CLASSES_URL)

    r.raise_for_status()
    
    return parse_classes_results(r.content)


def parse_classes_results(content):
    soup = BeautifulSoup(content)

    # Find all classes names and links
    def a_in_dd(tag):
        return tag.name == 'a' and tag.parent.name == 'dd'
    tables = soup.find('div', attrs={'class':'flowListDiv'}).find_all(a_in_dd)

    # Clean up results
    results = []
    for table in tables:
        results.append((table.text, table['href']))
    return results


def main(wf):
    # Update available?
    if wf.update_available:
        wf.add_item('A newer version is available',
                    '↩ to install update',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)
    
    # Cleaned up query
    query = 'q' + wf.args[0].replace(" ", "").lower()

    # Either download classes list or load it from cache
    def wrapper():
        return request_classes()
    results = wf.cached_data('results', wrapper, max_age=CACHE_EXPIRATION)

    atLeatOne = False
    for result in results:
        if len(result[0]) >= len(query) and result[0].lower().startswith(query):
            title = result[0]
            url = DOC_URL + result[1]
            wf.add_item(title=title, subtitle=url, arg=url, valid=True,
                        autocomplete=title.lower()[1:], uid=title,
                        copytext=url, largetext=title)
            atLeatOne = True

    if not atLeatOne:
        title = 'Search for ' + query
        subtitle = 'No result could be found, go to search page.'
        url = SEARCH_URL + query
        wf.add_item(title=title, subtitle=subtitle, arg=url, valid=True, largetext=title)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow(help_url=HELP_URL,
                  update_settings=UPDATE_SETTINGS)
    # Assign Workflow logger to a global variable for convenience
    log = wf.logger
    sys.exit(wf.run(main))