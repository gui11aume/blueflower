# -*- coding:utf-8 -*-

import re
import sys

from BrowserDecoy import BrowserDecoy


class CellCrawler(object):
   """A crawler to retrive the links to the articles of Cell."""

   # Regular expressions used for crawling.
   BASE_URL = 'http://www.cell.com/'
   PREV_NEXT = 'href="/(issue?[^"]+)'
   ARTICLES = 'id="Articles".*'
   FULL_TEXT = 'href="/(fulltext/[^"]+)'

   def __init__(self, out=sys.stdout):
      self.out = out
      self.decoy = BrowserDecoy()
      self.visited = set([])

   def start(self, url="current", headers={'Host': 'www.cell.com'}):
      """Start crawling by getting the content of the current issue.
      Take a cookie as we go and initiate recursive crawling.

      NB: All URLs are assumed to be relative.
      """

      # Instantiate a browser decoy.
      full_url = self.BASE_URL + url
      self.decoy.connect(full_url, headers)

      # Get the url to previous issue.
      to_previous_issue = re.findall(self.PREV_NEXT, self.decoy.read())

      # Update headers with referer and cookie.
      headers.update({'Referer': full_url})
      headers.update(self.decoy.get_cookie_items())

      self.visited.add(full_url)

      # Crawl!
      self.crawl(
          url_list = to_previous_issue,
          headers = headers
      )

   def crawl(self, url_list, headers):

      # Skip visited urls.
      urls_to_visit = set(url_list).difference(self.visited)

      for url in urls_to_visit:
         # Connect.
         self.decoy.connect(self.BASE_URL + url, headers)

         # Get content and section of full articles.
         content = self.decoy.read()
         articles = re.search(self.ARTICLES, content, re.S).group()

         # Now grep a couple of links.
         to_prev_next = re.findall(self.PREV_NEXT, content)
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
