import asyncio
import re
from pathlib import Path

from download_command import WgetCommand, CurlCommand
from logger import logging
from make_request import Request, Request9anime

class Downloader:
  BACKGROUND_DOWNLOAD = 0
  FOREGROUND_DOWNLOAD = 1

  def __init__(self, cache_dir):
    self.browser_req = f'User-Agent: {Request.USER_AGENT_BROWSER}'
    self.referer = f'Referer: {Request9anime.DOMAIN}'
    self.source_req_header = {}
    self.cache_dir = cache_dir
    self.subscribers = []

  def vid_html_local(self, html_name) -> Path:
    return Path(self.cache_dir).joinpath(f'{html_name}.html')

  def store_source_html(self, html, html_name, episode_url):
    save_at = self.vid_html_local(html_name)
    if not save_at:
      return
    with open(save_at, 'w') as source_html_file:
      source_html_file.write('<!-- %s -->\n' % episode_url)
      source_html_file.write(html)

  def parse_link(self, source):
    raise NotImplementedError

  def get_source_html(self, target):
    return Request(self.source_req_header).get(target)

  def add_subscriber(self, subscriber):
    self.subscribers.append(subscriber)

  def notify_downlaod(self, path):
    for subscriber in self.subscribers:
      subscriber.notify(path)

  def download(self, target_url, save_loc, mode):
    logging.debug("Source html url: %s", target_url)
    source_html = self.get_source_html(target_url)
    html_name = Path(save_loc).name
    self.store_source_html(source_html, html_name, target_url)
    link = self.parse_link(source_html)
    path = f'{save_loc}.mp4'
    returncode = self.fetch(link, path, mode)
    
    if returncode == 0:
      self.vid_html_local(html_name).unlink()
      self.notify_downlaod(path)
    return returncode

  def fetch(self, download_link, save_loc, mode):
    logging.debug("Download link: %s", download_link)
    wget_command = WgetCommand(download_link, save_loc, [self.browser_req, self.referer])
    curl_command = CurlCommand(download_link, save_loc, [self.browser_req, self.referer])
    returncode = wget_command.run(mode)
    if returncode > 0:
      returncode = curl_command.run(mode)
    return returncode

class Mp4uploadDownloader(Downloader):
  def __init__(self, cache_dir):
    super().__init__(cache_dir)
    self.referer = f'Referer: https://www.mp4upload.com/'
    self.server_id = 35

  def parse_link(self, source):
    video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', source)
    url_info = video_info_match.group(1).split('|')
    url_regex = re.compile(r'(\w{1,2})://(\w{1,2})\.(\w{1,2})\.(\w{1,2}):(\w{1,2})/(\w{1,2})/(\w{1,2})/-?(\w{1,2})\.(\w{1,2})')
    url_parts = [url_info[int(match, 36)] for match in url_regex.findall(source)[0]]
    download_link = '{protocol}://{subdomain}.{SLD}.{TLD}:{port}/d/{dir}/{filename}.{ext}'.format(
      protocol=url_parts[0], subdomain=url_parts[1], SLD=url_parts[2], TLD=url_parts[3], port=url_parts[4],
      dir=url_parts[6], filename=url_parts[7], ext=url_parts[8]
    )
    return download_link


class StreamtapeDownloader(Downloader):
  def __init__(self, cache_dir):
    super().__init__(cache_dir)
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

  # changes very frequently
  def downloadlink_from_html(self, source):
    match = re.search(r"v.{0,9}ink.+innerHTML[^\"']+([^;]+)", source)
    address_str = match.group(1)
    address = asyncio.run(execute_js_statement(address_str))
    link = f'https:{address}'
    logging.debug(link)
    return link

  def parse_link(self, source):
    download_link = self.downloadlink_from_html(source)
    response = Request().make_request(download_link, '')
    return response.url

async def execute_js_statement(statement):
  s = re.sub(r'"', '\\"', statement)
  cmd = f'node -e "console.log({s})"'
  process = await asyncio.create_subprocess_shell(
    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
  )
  stdout, stderr = await process.communicate()
  if stderr:
    msg = stderr.decode()
    logging.error(f'{statement} statement failed with {msg}')
    raise Exception(msg)

  return stdout.decode()

if __name__ == "__main__":
  import logging
  logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.DEBUG)

  CUR_DIR = Path(__file__).parent
  html_path = CUR_DIR.joinpath("__pycache__/fruits/fruits4.html")
  with open(html_path, 'r') as fp:
    source = fp.read()
  cache_dir = CUR_DIR.joinpath('__pycache__')
  downloader = Mp4uploadDownloader(cache_dir)
  print(downloader.parse_link(source))
