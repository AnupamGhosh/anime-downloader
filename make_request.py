import urllib
import urllib.request

from logger import logging

class Request:
  USER_AGENT_BROWSER = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0'
  
  def __init__(self, headers=None):
    headers = headers or {}
    self.headers = {
      'accept': '*/*',
      # 'x-requested-with': 'XMLHttpRequest',
      'user-agent': Request.USER_AGENT_BROWSER,
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'accept-language': 'en-US,en;q=0.5',
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
    response = self.make_request(url, params)
    return response.getheaders()

class Request9anime(Request):
  DOMAIN = 'https://9anime.id'

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
