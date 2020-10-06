import re
import os
import logging
from make_request import Request

class Downloader():
  def __init__(self, target, save_loc, source_html=None):
    self.save_loc = save_loc
    self.source_html_loc = source_html
    self.target = target

  def store_source_html(self, html):
    if not self.source_html_loc:
      return
    with open(self.source_html_loc, 'w') as source_html_file:
      source_html_file.write('<!-- %s -->\n' % self.target)
      source_html_file.write(html)

  def download(self, download_link):
    logging.debug("Download link: %s", download_link)
    returncode = os.system('wget --no-check-certificate {url} -O {save_loc}'.format(
      url=download_link, save_loc=self.save_loc)
    )
    if returncode > 0:
      return os.system('curl -k {url} -o {save_loc}'.format(url=download_link, save_loc=self.save_loc))
    return returncode

class Mp4uploadDownloader(Downloader):
  def __init__(self, target, save_loc, source_html):
    super().__init__(target, save_loc, source_html)

  def download(self):
    logging.debug("Source html url: %s", self.target)
    source_html = Request().get(self.target)
    self.store_source_html(source_html)

    video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', source_html)
    url_info = video_info_match.group(1).split('|')
    url_regex = re.compile(r'(\w{1,2})://(\w{1,2})\.(\w{1,2})\.(\w{1,2}):(\w{1,2})/(\w{1,2})/(\w{1,2})/(\w{1,2})\.(\w{1,2})')
    url_parts = [url_info[int(match, 36)] for match in url_regex.findall(source_html)[0]]
    download_link = '{protocol}://{subdomain}.{SLD}.{TLD}:{port}/d/{dir}/{filename}.{ext}'.format(
      protocol=url_parts[0], subdomain=url_parts[1], SLD=url_parts[2], TLD=url_parts[3], port=url_parts[4],
      dir=url_parts[6], filename=url_parts[7], ext=url_parts[8]
    )
    return super().download(download_link)


class StreamtapeDownloader(Downloader):
  def __init__(self, target, save_loc, source_html):
    super().__init__(target, save_loc, source_html)

  def download(self):
    logging.debug("Source html url: %s", self.target)
    source_html = Request().get(self.target)
    self.store_source_html(source_html)

    match = re.search(r'videolink[^>]+>([^<]+)', source_html, re.MULTILINE)
    download_link = 'https:{address}'.format(address=match.group(1))
    res_headers = Request().res_headers(download_link)
    redirect_url = None
    for header, val in res_headers:
      if header == 'X-Redirect':
        redirect_url = val
    return super().download(redirect_url)
