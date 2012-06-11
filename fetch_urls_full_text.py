# -*- coding:utf-8 -*-

import re
import sys
import json

from datetime import datetime as dt
from BrowserDecoy import BrowserDecoy
from BeautifulSoup import BeautifulSoup

def remove_JS(string):
   """Strip JavaScript snippets from string."""
   return re.sub('<script.*?</script>', '', string, re.S)

class CellCrawler(object):
   """A crawler to retrive the links to the articles of Cell."""

   # Regular expressions used for crawling.
   BASE_URL = 'http://www.cell.com/'
   PREV_NEXT = '"/(issue\?pii[^"]+)'
   FULL_TEXT = '"/(fulltext/[^"]+)'
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

         if verbose:
            sys.stderr.write(self.BASE_URL + url + '\n')

         # Connect.
         retries = 0
         while retries < 3:
            # Give the conncetion 3 tries and then give up.
            try:
               self.decoy.connect(self.BASE_URL + url, headers)
               content = remove_JS(self.decoy.read())
               date_match = re.search(self.DATE, content).groups()
               date = dt.strptime(date_match[0], '%d %B %Y')
            except:
               retries += 1
               continue
            else:
               break

         if date > self.SWITCH_TIME:
            # After SWITCH_TIME (6 May 2005), research articles
            # have the 'article' class.
            BS = BeautifulSoup(content)
            article_tags = BS.findAll(attrs={'class': 'article'})
            articles = '\n'.join([str(tag) for tag in article_tags])
         else:
            # Before SWITCH_TIME (6 May 2005) there is no separation
            # between the different types of articles.
            articles = content


         # Now grep a couple of links.
         to_prev_next = re.findall(self.PREV_NEXT, content)
         to_pdf = re.findall(self.PDF, articles)
         to_full = re.findall(self.FULL_TEXT, articles)

         # Dump.
         self.out.write('"%s": ' % url)
         json.dump([to_pdf, to_full], self.out)
         self.out.write(',\n')

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
