import urllib
import urllib.request
import re
import time
from http.client import HTTPSConnection

from logger import logging

class Request(object):
  USER_AGENT_BROWSER = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
  
  def __init__(self, headers=None):
    headers = headers or {}
    self.headers = {
      'accept': 'application/json, text/javascript, */*; q=0.01',
      # 'x-requested-with': 'XMLHttpRequest',
      'user-agent': Request.USER_AGENT_BROWSER,
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    self.headers.update(headers)
    self.cookies = []
    
  def save_cookie(self, key, value):
    self.cookies.append('%s=%s' % (key, value))

  def make_request(self, url, params):

    req_params = f'?{urllib.parse.urlencode(params)}' if params else ''
    url = f'{url}{req_params}'
    headers = self.headers.copy()
    headers['cookie'] = '; '.join(self.cookies)
    logging.debug("Requesting url: %s, headers:%s", url, headers)
    request = urllib.request.Request(url, headers=headers)
    res = urllib.request.urlopen(request)
    return res

  def get(self, url, params=None):
    response = self.make_request(url, params)
    with response as fp:
      content = fp.read().decode(encoding='UTF-8', errors='strict')
    return content

  def res_headers(self, url, params=None):
    headers = self.make_request(url, params).headers
    return dict(headers.items())

class Request9anime(Request):
  DOMAIN = 'https://9anime.to'

  def __init__(self, base_path):
    super(Request9anime, self).__init__({
      'referer': '%s%s' % (Request9anime.DOMAIN, base_path),
    })
    self.cookies = [
      '_ga=GA1.2.1603338442.1589383036', '_gid=GA1.2.1309926967.1589383036', '_gat=1',
      '__atuvc=1%7C20', '__atuvs=5ebc0f7bf4605059000'
    ]

  def make_request(self, path, params):
    params = params or {}
    url = '%s%s' % (Request9anime.DOMAIN, path)
    return super(Request9anime, self).make_request(url, params)
