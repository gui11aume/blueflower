# -*- coding:utf-8 -*-

import re
import sys

from datetime import datetime as dt
from BrowserDecoy import BrowserDecoy
from BeautifulSoup import BeautifulSoup

def remove_JS(string):
   """Strip JavaScript snippets from string."""
   return re.sub('<script>.*?</script>', '', string, re.S)

class CellCrawler(object):
   """A crawler to retrive the links to the articles of Cell."""

   # Regular expressions used for crawling.
   BASE_URL = 'http://www.cell.com/'
   PREV_NEXT = 'href="/(issue?[^"]+)'
   FULL_TEXT = 'href="/(fulltext/[^"]+)'
   PDF = 'href="(http://download.cell.com/pdf/[^"]+.pdf)"'
   DATE = '<title>.*, (.*)</title>'
   SWITCH_TIME = dt(2005, 5, 6, 0, 0)

   def __init__(self, out=sys.stdout):
      self.out = out
      self.decoy = BrowserDecoy()
      self.visited = set([])

   def start( self, url = "current", headers = {'Host': 'www.cell.com'},
         verbose = True):
      """Start crawling by getting the content of the current issue.
      Take a cookie as we go and initiate recursive crawling.

      NB: All URLs are assumed to be relative.
      """

      # Instantiate a browser decoy.
      full_url = self.BASE_URL + url
      self.decoy.connect(full_url, headers)

      if verbose:
         sys.stderr.write('started at %s\n' % full_url)

      # Get the url to previous issue.
      to_previous_issue = re.findall(self.PREV_NEXT, self.decoy.read())

      # Update headers with referer and cookie.
      headers.update({'Referer': full_url})
      headers.update(self.decoy.get_cookie_items())

      self.visited.add(full_url)

      # Crawl!
      self.crawl(
          url_list = to_previous_issue,
          headers = headers,
          verbose = verbose
      )

   def crawl(self, url_list, headers, verbose=True):

      # Skip visited urls.
      urls_to_visit = set(url_list).difference(self.visited)

      for url in urls_to_visit:

         # Connect.
         self.decoy.connect(self.BASE_URL + url, headers)

         # Get content and section of full articles.
         content = remove_JS(self.decoy.read())
         date_match = re.search(self.DATE, content).groups()
         date = dt.strptime(date_match[0], '%d %B %Y')

         if verbose:
            sys.stderr.write('connecting to %s' % (self.BASE_URL + url))
            sys.stderr.write(' (%s)\n' % date.strftime('%B %d, %Y'))

         if date > self.SWITCH_TIME:
            # Before SWITCH_TIME (6 May 2005) research articles
            # are at end of page, and separated from the rest.
            BS = BeautifulSoup(content)
            try:
               articles = BS.find('h3', attrs={'id': 'Articles'}).text
            except AttributeError:
               articles = ''
         else:
            # Before SWITCH_TIME (6 May 2005) there is no separation
            # between the different types of articles.
            articles = content


         # Now grep a couple of links.
         to_prev_next = re.findall(self.PREV_NEXT, content)
         to_pdf = re.findall(self.PDF, articles)
         if to_pdf:
            # Grab the pdfs if present.
            self.out.write('"%s": %s,\n' % (url, str(to_pdf)))
         else:
            # Otherwise grab links to full text.
            to_full_text = re.findall(self.FULL_TEXT, articles)
            self.out.write('"%s": %s,\n' % (url, str(to_full_text)))

         # Add url to visited and update referer...
         self.visited.add(url)
         headers['Referer'] = url

         # ... and crawl onwards!
         self.crawl(
             url_list = to_prev_next,
             headers = headers
         )


if __name__ == '__main__':
   # When called from the terminal, fetches all the (relative) links
   # to full text articles of Cell, and associates them with the
   # url of the corresponding issue.
   CellCrawler().start()
