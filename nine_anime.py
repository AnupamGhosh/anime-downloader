# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url,
# eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
# For analyzing URL params for EPISODES_URL, EPISODE_INFO open chrome devtools.
# Check the initiator column to understand the code flow & logic how data is sent to server

import json
import os
import random
import re
import time
from pathlib import Path
from typing import Dict

import utils
from logger import logging
from make_request import Request, Request9anime
from querySelector import GetElements, SearchNodeParser

class NineAnime:
  EPISODES_URL = '/ajax/anime/servers'
  EPISODE_INFO = '/ajax/anime/episode'

  def __init__(self, base_path: str, name_prefix: str, start: str, episode_count: int):
    self.base_path = base_path
    self.filename_prefix = name_prefix
    self.start_episode = start - 1
    self.get_episodes = episode_count
    self.request = Request9anime(base_path)

  def anime_html_filepath(self) -> str:
    '''Episodes html of the anime'''
    return os.path.join(self.cache_directory(), 'python.html')

  def cache_directory(self) -> Path:
    return utils.get_cache_directory(self.filename_prefix)

  def store_cookies(self):
    paths = [self.base_path]
    for path in paths:
      res_meta_data = self.request.res_headers(path)
      cookies = NineAnime.get_cookies(res_meta_data)
      for key in cookies:
        self.request.save_cookie(key, cookies[key])

  @staticmethod
  def get_cookies(res_headers) -> Dict[str, str]:
    cookie_headers = [val for header, val in res_headers if header == 'set-cookie']
    cookies = {}
    for cookie_str in cookie_headers:
      key, val = cookie_str.split(';', 1)[0].strip().split('=', 1)
      cookies[key] = val
    return cookies

  def get_episodes_html(self):
    path_matched = re.search(r".*\.(\w+)\/(\w+)", self.base_path)
    servers_id = path_matched.group(1)
    episode_id = path_matched.group(2)
    episode_url = NineAnime.EPISODES_URL
    content = self.request.get(episode_url, {'id': servers_id, 'episode': episode_id})

    try:
      html_episodes = content
      path = self.anime_html_filepath()
      with open(path, 'w') as html_text:
        html_text.write(html_episodes)
    except Exception as e:
      logging.debug("content:\n%s", content)
      raise e

  def get_episode_ids(self, server_id):
    path = self.anime_html_filepath()
    with open(path, 'r') as fp:
      html = fp.read()
    parser = EpisodeDataId(html, server_id)
    return parser.get_episode_ids()

  def get_videolinks(self, episode_ids: [str]) -> Dict[int, str]:
    # get video source html page
    start = self.start_episode
    get_episodes = self.get_episodes
    anime_ep_ids = episode_ids[start: start + get_episodes]
    source_info_path = NineAnime.EPISODE_INFO
    url_decoder = VideoURLDecoder()
    logging.debug('headers:\n%s', self.request.headers)
    videolinks = {}
    for i in range(get_episodes):
      current_ep = start + i + 1
      episode_hash = anime_ep_ids[i]
      if not episode_hash:
        logging.info(f'Hash not found for episode {current_ep}! Skipping.')
        continue

      logging.debug("Episode %s data-id=%s", current_ep, episode_hash)
      # sensitive code
      content = self.request.get(source_info_path, {
          'id': episode_hash})
      try:
        source_html_url = url_decoder.get(json.loads(content)['url'])
        logging.info(f'Link for episode {current_ep}')
      except Exception:
        logging.exception(f'source_info_url response:\n{content}')
        return
      videolinks[current_ep] = source_html_url
      # to avoid being blocked by spamming
      duration = random.uniform(0.2, 1)
      time.sleep(duration)

    return videolinks
      
  def cache_videolinks(self, videolinks: Dict[int, str]):
    videolinks_path = Path(os.path.join(self.cache_directory(), 'videolinks.json'))
    old_links = self.get_cached_links()
    for key, val in videolinks.items():
      old_links[key] = val

    with open(videolinks_path, 'w') as fp:
      json.dump(old_links, fp)

  def get_cached_links(self) -> Dict[int, str]:
    videolinks_path = Path(os.path.join(self.cache_directory(), 'videolinks.json'))
    links = {}
    if videolinks_path.is_file():
      with open(videolinks_path, 'r') as fp:
        raw_text = fp.read()
        links = json.loads(raw_text)

    return links

  # temp funciton
  def episodes_json_to_html(self):
    read_path = os.path.join(self.cache_directory(), 'episodes.json')
    with open(read_path, 'r') as fp:
      ep_json = json.loads(fp.read())

    try:
      html_episodes = ep_json['html']
    except Exception as err:
      logging.info('ep_json=%s', ep_json)
      raise err

    path = self.anime_html_filepath()
    with open(path, 'w') as html_text:
      html_text.write(html_episodes)

  def update_videolinks(self, server_id):
    self.store_cookies()
    #  @FIXME need to mimic recaptcha_en.js to send token param to EPISODES_URL.
    # devtools from chrome doesn't even return the correct result for EPISODES_URL. Use Firefox.
    # self.get_episodes_html()
    self.episodes_json_to_html()

    episode_ids = self.get_episode_ids(server_id)
    videolinks = self.get_videolinks(episode_ids)
    self.cache_videolinks(videolinks)
    # os.remove(self.anime_html_filepath())


class EpisodeDataId:
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

class VideoURLDecoder:
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

  def get(self, hash):
    part1 = hash[0:9]
    part2 = self.generate_part2(hash[9:])
    return self.html_link(part1, part2)
