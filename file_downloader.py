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
    self.SUBDOMAIN = 27
    self.PORT = 56
    self.VIDEO_DIR = 55
    self.EXTENSION = 25

  def download(self):
    logging.debug("Source html url: %s", self.target)
    source_html = Request().get(self.target)
    self.store_source_html(source_html)

    video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', source_html, re.MULTILINE)
    url_info = video_info_match.group(1).split('|')
    download_link = 'https://{subdomain}.mp4upload.com:{port}/d/{video_dir}/video.{ext}'.format(
      subdomain=url_info[self.SUBDOMAIN], port=url_info[self.PORT],
      video_dir=url_info[self.VIDEO_DIR], ext=url_info[self.EXTENSION ]
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

# CUR_DIR = os.path.dirname(__file__)
# save_as = os.path.join(CUR_DIR, 'dummy.mp4')
# StreamtapeDownloader('https://streamtape.net/e/8qmvLzvgqRIovjy/', save_as, None).download()

# Mp4uploadDownloader('https://www.mp4upload.com/embed-wc6347pguqft.html', save_as, None).download()