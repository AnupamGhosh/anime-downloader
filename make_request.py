import httplib
import urllib
import re
import time
import logging

class Request(object):
  def __init__(self, headers=None):
    headers = headers or {}
    self.headers = {
      'accept': 'application/json, text/javascript, */*; q=0.01',
      'x-requested-with': 'XMLHttpRequest',
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    self.headers.update(headers)
    self.cookies = []
    self._res_text = ''
    
  def save_cookie(self, key, value):
    self.cookies.append('%s=%s' % (key, value))

  def make_request(self, url, params):
    params = params or {}
    reg_match = re.match(r"https:\/\/([^\/]*)([^?]*)(.*)", url)
    domain = reg_match.group(1)
    path = reg_match.group(2)
    temp_params = reg_match.group(3)
    if len(temp_params) > 1:
      temp_params = re.findall(r"([^=]+)=([^&]+)&", temp_params + '&')
      params.update({key: val for key, val in temp_params})
    if len(params):
      path += '?' + urllib.urlencode(params)

    con = httplib.HTTPSConnection(domain)
    logging.debug("Requesting url: https://%s%s", domain, path)
    headers = self.headers.copy()
    headers['cookie'] = '; '.join(self.cookies)
    con.request('GET', path, None, headers)
    res = con.getresponse()
    self._res_text = res.read()
    con.close()
    return res

  def get(self, url, params=None):
    self.make_request(url, params)
    return self._res_text

  def res_headers(self, url, params=None):
    return self.make_request(url, params).getheaders()

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
    params['ts'] = int(time.time())
    url = '%s%s' % (Request9anime.DOMAIN, path)
    return super(Request9anime, self).make_request(url, params)
