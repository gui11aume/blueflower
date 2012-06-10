# -*- coding:utf-8 -*-

import urllib2
import cookielib

from gzip import GzipFile
from StringIO import StringIO


class BrowserDecoy(object):
   """Class to manage HTTP connections like a browser.
   Connections established through this object look like they
   originate from a browser. To this end, the BrowserDecoy
   object sets HTTP request headers to look like the ones
   produced by a browser and ensures that session cookies are
   passed during the request.

   EXAMPLE USAGE:
     decoy = BrowserDecoy()
     decoy.connect('http://google.com')
     decoy.read()
   """

   # Object of class |urllib2.OpenerDirector| to open HTTP
   # and HTTPS connections, and processcookies.
   cookies = cookielib.LWPCookieJar()
   handlers = [
       urllib2.HTTPHandler(),
       urllib2.HTTPSHandler(),
       urllib2.HTTPCookieProcessor(cookies),
   ]
   opener = urllib2.build_opener(*handlers)

   # Base request headers for HTTP connection.
   base_headers = {
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'gzip,deflate,sdch',
       'Accept-Language': 'en-US,en;q=0.8,fr;q=0.6',
       'Connection': 'keep-alive',
   }

   # User-Agent headers for different browsers.
   user_agent = {
      'chrome': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.151 Chrome/18.0.1025.151 Safari/535.19',
      'firefox': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0',
   }

# 'Referer': 'http://www.cell.com/current'
# 'Host': 'www.cell.com',

   def __init__(self, browser="chrome"):
      """Set User-Agent header to fit given browser."""
      self.browser = browser
      self.base_headers.update({
          'User-Agent': self.user_agent[browser],
      })

   def connect(self, URL, headers):
      """Connect with given headers to given URL.

      ARGUMENTS:
        URL: a string with the url to connect to.
        headers: a dictionary of request headers that will be
          added to the base headers.

      RETURN VALUE:
         An object of class urllib.addinfourl."""

      connection_headers = self.base_headers
      connection_headers.update(headers)
      request = urllib2.Request(url=URL, headers=connection_headers)
      self.connection = self.opener.open(request)


   def read(self):
      """Read and decode the content of current connection."""
      if self.connection.headers.get('content-encoding') == 'gzip':
         # Content is compressed by gzip. Read with StringIO/gzip.
         string_io = StringIO(self.connection.read())
         return GzipFile(fileobj=string_io, mode='rb').read()
      else:
         # Content is not gzipped, just read.
         return self.connection.read()


   def get_cookie_items(self):
      """Return cookies of current connection as (key,value) pair."""
      return [(cookie.name, cookie.value) for cookie in self.cookies]
