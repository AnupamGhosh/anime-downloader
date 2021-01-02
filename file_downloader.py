import re
import os
import logging
from make_request import Request, Request9anime

class Downloader():
  def __init__(self):
    self.browser_req = f'User-Agent: {Request.USER_AGENT_BROWSER}'
    self.referer = f'Referer: {Request9anime.DOMAIN}'
    self.source_req_header = {}

  def store_source_html(self, html, save_at, target):
    if not save_at:
      return
    with open(save_at, 'w') as source_html_file:
      source_html_file.write('<!-- %s -->\n' % target)
      source_html_file.write(html)

  def parse_link(self, source):
    raise NotImplementedError

  def get_source_html(self, target):
    return Request(self.source_req_header).get(target)

  def download(self, target, save_loc, source_html_path):
    logging.debug("Source html url: %s", target)
    source_html = self.get_source_html(target)
    self.store_source_html(source_html, source_html_path, target)
    link = self.parse_link(source_html)
    # return self.fetch(link, save_loc)
    return 0

  def fetch(self, download_link, save_loc):
    logging.debug("Download link: %s", download_link)
    returncode = os.system("wget --no-check-certificate {url} --header '{browser}' --header '{referer}' -O {save_loc}".format(
      url=download_link, save_loc=save_loc, browser=self.browser_req, referer=self.referer)
    )
    if returncode > 0:
      return os.system("curl -k '{url}' -H '{browser}' -H '{referer}' -o {save_loc}".format(
        url=download_link, save_loc=save_loc, browser=self.browser_req, referer=self.referer)
      )
    return returncode

class Mp4uploadDownloader(Downloader):
  def __init__(self):
    super().__init__()
    self.referer = f'Referer: https://www.mp4upload.com/'
    self.server_id = 35

  def parse_link(self, source):
    video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', source)
    url_info = video_info_match.group(1).split('|')
    url_regex = re.compile(r'(\w{1,2})://(\w{1,2})\.(\w{1,2})\.(\w{1,2}):(\w{1,2})/(\w{1,2})/(\w{1,2})/(\w{1,2})\.(\w{1,2})')
    url_parts = [url_info[int(match, 36)] for match in url_regex.findall(source)[0]]
    download_link = '{protocol}://{subdomain}.{SLD}.{TLD}:{port}/d/{dir}/{filename}.{ext}'.format(
      protocol=url_parts[0], subdomain=url_parts[1], SLD=url_parts[2], TLD=url_parts[3], port=url_parts[4],
      dir=url_parts[6], filename=url_parts[7], ext=url_parts[8]
    )
    return download_link


class StreamtapeDownloader(Downloader):
  def __init__(self):
    super().__init__()
    self.server_id = 40
    self.source_req_header = {
      'authority': 'streamtape.to',
      'cache-control': 'max-age=0',
      'upgrade-insecure-requests': '1',
      'sec-fetch-site': 'none',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-user': '?1',
      'sec-fetch-dest': 'document',
      'accept-language': 'en-GB,en;q=0.9',
    }

  def parse_link(self, source):
    match = re.search(r"videolink.+innerHTML.+(['\"])(.+)(\1)", source)
    address = match.group(2)
    get_video = re.search(r'^.*(get_video.*)', address)
    download_link = 'https://streamtape.to/{address}'.format(address=get_video.group(1))
    res_headers = Request().res_headers(download_link)
    redirect_url = None
    for header, val in res_headers:
      if header.lower() in ['x-redirect', 'location']:
        redirect_url = val
    if redirect_url is None:
      raise ValueError(f'StreamtapeDownloader: Redirect url is None for {download_link}')
    elif 'streamtape_do_not_delete' in redirect_url:
      raise ValueError(f'StreamtapeDownloader: Download link {download_link} incorrect!')
    return redirect_url


if __name__ == "__main__":
  logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.DEBUG)

  streamtape_link = 'https://streamtape.to/e/0VolVxpedjTbbaq/?site=9anime.app'
  header = {
    'authority': 'streamtape.to',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-GB,en;q=0.9',
  }
  req = Request(header)
  source = req.get(streamtape_link)
  downloader = StreamtapeDownloader()
  print(downloader.parse_link(source))
