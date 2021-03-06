#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This code is not supported by Google
#

__author__ = "salrashid123@gmail.com for Google"
__author__ = "jonathanho@google.com (Jonathan Ho)"

import connector
import datetime
import urllib2
import xml.dom.minidom


class SitemapConnector(connector.TimedConnector):
  """A connector that crawls a site given a sitemap.xml file.

  Downloads the given sitemap.xml file, parses out the URLs inside, and then
  sends those URLs as either metadata-and-url or content feeds.
  """

  CONNECTOR_TYPE = 'sitemap-connector'
  CONNECTOR_CONFIG = {
      'surl': { 'type': 'text', 'label': 'Sitemap URL' },
      'delay': { 'type': 'text', 'label': 'Fetch Delay' }
  }

  def init(self):
    self.setInterval(int(self.getConfigParam('delay')))

  def run(self):
  # the parameters into the 'run' method
    self.logger().info('TIMER INVOKED for %s ' % self.getName())
    # now go get the sitemap.xml file itself
    u = self.getConfigParam('surl')
    req = urllib2.Request(u)
    response = urllib2.urlopen(req)
    content = response.read()
    #parse out the sitemap and get all the urls
    sitemap_urls = []
    xmldoc = xml.dom.minidom.parseString(content)
    m_node = xmldoc.getElementsByTagName('url')
    for rnode in m_node:
      rchild = rnode.childNodes
      for nodes in rchild:
        if nodes.nodeName == 'loc':
          sitemap_urls.append(nodes.childNodes[0].nodeValue)
#        if nodes.nodeName == 'lastmod':
#          now = datetime.datetime.now()
#          strt = nodes.childNodes[0].nodeValue
#          lastmodtime_time = time.strptime(strt, "%Y-%m-%d")
#          lastmodtime_date = datetime.datetime(*lastmodtime_time[:6])
    #for each url in the sitemap, send them in batches to the GSA
    #the batch size is specified by the 'load' parameter from the config page
    i = 0
    feed_type = 'metadata-and-url'
    #feed_type = 'incremental'
    feed = connector.Feed(feed_type)
    for url in sitemap_urls:
      if feed_type == 'metadata-and-url':
        feed.addRecord(url=url, displayurl=url, action='add',
                       mimetype='text/html')
      else:
        content = urllib2.urlopen(url).read()
        feed.addRecord(url=url, displayurl=url, action='add',
                       mimetype='text/html', content=content)
      #if the number of urls were going to send to the GSA right now is more
      #than what its expecting, send what we have now and reset the counter
      #afer waiting 1 min (this is the poormans traversal rate limit delay)
      if i >= float(self.getLoad()):
        self.logger().debug('Posting %s URLs to the GSA for connector [%s]' % (
            i, self.getName()))
        self.pushFeed(feed)
        feed.clear()
        i = 0
      else:
        i = i+1
    if i>0:
      self.logger().debug(('Final posting %s URLs to the GSA '
                           'for connector [%s]') % (i, self.getName()))
      self.pushFeed(feed)
      feed.clear()