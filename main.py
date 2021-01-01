# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url,
# eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
# analyze every params carefully when editing API calls

import logging
import json
import os
import re

from make_request import Request, Request9anime
from querySelector import GetElements, SearchNodeParser
from file_downloader import Mp4uploadDownloader, StreamtapeDownloader

class EpisodeDataId():
  def __init__(self, html: str, server_id: str):
    selector = [
      {'tag': 'div', 'class': ['body']},
      {'tag': 'ul', 'class': ['episodes']},
      {'tag': 'a'}
    ]
    self.server_id = str(server_id)
    self.query = GetElements(selector)
    parser = SearchNodeParser(self.query)
    parser.feed(html)

  def get_episode_ids(self):
    elements = self.query.matched_elements()
    episode_ids = [''] * int(elements[-1]['data-base'])
    for element in elements:
      episode_no = int(element['data-base'])
      episode_ids[episode_no - 1] = json.loads(element['data-sources'])[self.server_id]
    return episode_ids

class VideoHtmlGenerator():
  def __init__(self, hash):
    self.hash = hash

  def generate_part2(self, t):
    t = re.sub(r'==?$', '', t)
    x = ''
    e = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    r = 0
    u = 0
    for c in range(len(t)):
      r <<= 6
      n = t[c]
      i = e.find(n)
      if i >= 0:
        r |= i
      u += 6
      if u == 24:
        x += chr((16711680 & r) >> 16)
        x += chr((65280 & r) >> 8)
        x += chr(255 & r)
        r = 0
        u = 0

    if u == 12:
      r >>= 4
      x += chr(r)
      return x
    elif u == 18:
      r >>= 2
      x += chr((65280 & r) >> 8)
      x += chr(255 & r)
      return x
    else:
      return x

  def html_link(self, t, n):
    o = 256
    u = 0
    c = ''
    r = [i for i in range(o)]
    for e in range(o):
      u = (u + r[e] + ord(t[e % len(t)])) % o
      r[e], r[u] = r[u], r[e]

    u = 0
    e = 0
    for s in range(len(n)):
      e = (e + 1) % o
      u = (u + r[e]) % o
      r[e], r[u] = r[u], r[e]
      ord(n[s])
      c += chr(ord(n[s]) ^ r[(r[e] + r[u]) % o])
    return c

  def get(self):
    part1 = self.hash[0:9]
    part2 = self.generate_part2(self.hash[9:])
    return self.html_link(part1, part2)

class Downloader():

  def __init__(self, base_path, name_prefix, start, episode_count, save_dir, downloader):
    self.base_path = base_path
    self.filename_prefix = name_prefix
    self.start_episode = start - 1
    self.get_episodes = episode_count
    self.save_dir = save_dir
    self.request = Request9anime(base_path)
    self.downloader = downloader
    self.anime_html_filepath = os.path.join(CUR_DIR, '%s-python.html' % self.filename_prefix)
    self.subscribers = []

  def store_cookies(self):
    paths = [self.base_path]
    for path in paths:
      res_meta_data = self.request.res_headers(path)
      cookies = Downloader.get_cookies(res_meta_data)
      for key in cookies:
        self.request.save_cookie(key, cookies[key])

  @staticmethod
  def get_cookies(res_headers):
    cookie_headers = [val for header, val in res_headers if header == 'set-cookie']
    cookies = {}
    for cookie_str in cookie_headers:
      key, val = cookie_str.split(';', 1)[0].strip().split('=', 1)
      cookies[key] = val
    return cookies

  def add_subscriber(self, subscriber):
    self.subscribers.append(subscriber)

  def notify_downlaod(self, path):
    for subscriber in self.subscribers:
      subscriber.notify(path)


  def get_episodes_html(self):
    path_matched = re.search(r".*\.(\w+)\/(\w+)", self.base_path)
    servers_id = path_matched.group(1)
    episode_id = path_matched.group(2)
    episode_url = EPISODES_URL
    content = self.request.get(episode_url, {'id': servers_id, 'episode': episode_id})

    try:
      html_episodes = content
      path = self.anime_html_filepath
      with open(path, 'w') as html_text:
        html_text.write(html_episodes)
    except Exception as e:
      logging.debug("content:\n%s", content)
      raise e

  def get_episode_ids(self):
    path = self.anime_html_filepath
    with open(path, 'r') as fp:
      html = fp.read()
    parser = EpisodeDataId(html, SERVER)
    return parser.get_episode_ids()

  def download_videos(self, episode_ids):
    # get video source html page
    start = self.start_episode
    get_episodes = self.get_episodes
    anime_ep_ids = episode_ids[start: start + get_episodes]
    source_info_path = EPISODE_INFO
    logging.debug('headers:\n%s', self.request.headers)
    for i in range(get_episodes):
      logging.debug("Episode %s data-id=%s", start + i + 1, anime_ep_ids[i])
      current_ep = start + i + 1
      # sensitive code
      content = self.request.get(source_info_path, {
          'id': anime_ep_ids[i]})
      logging.info("source_info_url response:\n%s", content)
      source_html_url = VideoHtmlGenerator(json.loads(content)['url']).get()

      
      source_html_path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (
          self.filename_prefix, current_ep))
      save_as = os.path.join(self.save_dir, '%s%s.mp4' % (self.filename_prefix, current_ep))
      returncode = self.downloader.download(source_html_url, save_as, source_html_path)
      if not returncode:
        os.remove(source_html_path)
        self.notify_downlaod(save_as)


  # temp funciton
  def episodes_json_to_html(self):
    read_path = os.path.join(os.path.join(CUR_DIR, 'sample'), '%s-python.json' % self.filename_prefix)
    with open(read_path, 'r') as fp:
      ep_json = json.loads(fp.read())

    logging.debug('ep_json=%s', ep_json)
    html_episodes = ep_json['html']
    path = self.anime_html_filepath
    with open(path, 'w') as html_text:
      html_text.write(html_episodes)

  def download(self):
    self.store_cookies()
    #  @FIXME need to mimic recaptcha_en.js to send token param to EPISODES_URL.
    # devtools from chrome doesn't even return the correct result for EPISODES_URL. Use Firefox.
    # self.get_episodes_html()
    self.episodes_json_to_html()

    episode_ids = self.get_episode_ids()
    self.download_videos(episode_ids)
    os.remove(self.anime_html_filepath)


logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.INFO)
CUR_DIR = os.path.dirname(__file__)
with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
  config = json.load(config_fp)
BASE_PATH = config['base_path']
download_from = StreamtapeDownloader() # Mp4uploadDownloader()
SERVER = download_from.server_id
EPISODES_URL = '/ajax/anime/servers'
EPISODE_INFO = '/ajax/anime/episode'
Downloader(
    BASE_PATH, config['filename_prefix'], config['start_episode'], config['get_episodes'],
    str(config['save_in']).replace(' ', '\\ '), download_from
).download()
