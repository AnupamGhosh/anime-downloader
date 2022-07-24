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
import urllib.parse
from pathlib import Path
from typing import Dict, Tuple

import utils
from logger import logging
from make_request import Request9anime
from querySelector import GetElements, SearchNodeParser

class NineAnime:
  EPISODES_URL = '/ajax/anime/servers'
  EPISODE_INFO = '/ajax/anime/episode'

  def __init__(self, base_path: str, name_prefix: str):
    self.base_path = base_path
    self.filename_prefix = name_prefix
    self.request = Request9anime(base_path)

  def anime_html_filepath(self) -> str:
    '''Episodes html of the anime'''
    return os.path.join(self.cache_directory(), 'python.html')

  def cache_directory(self) -> Path:
    return utils.get_cache_directory(self.filename_prefix)

  def store_cookies(self):
    name, cookie = self.waf_cookie()
    self.request.save_cookie(name, cookie)

  def waf_cookie(self) -> Tuple[str, str]:
    res = self.request.get(self.base_path)
    match = re.search(r"fromCharCode[^\d]+(\d+)", res)
    hash_val = match[1]
    waf_cookie = ''
    for i in range(len(hash_val) // 2):
      integer = int(hash_val[i * 2: (i + 1) * 2], 16)
      ascii = chr(integer)
      waf_cookie += ascii

    return 'waf_cv', waf_cookie

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

  def get_videolinks(self, episode_ids: Dict[int, str]) -> Dict[int, str]:
    # get video source html page
    source_info_path = NineAnime.EPISODE_INFO
    url_decoder = VideoURLDecoder()
    logging.debug('headers:\n%s', self.request.headers)
    videolinks = {}
    for current_ep, episode_hash in episode_ids.items():
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

  def update_videolinks(self, server_id, force=False):
    # self.store_cookies()
    #  @FIXME need to mimic recaptcha_en.js to send token param to EPISODES_URL.
    # devtools from chrome doesn't even return the correct result for EPISODES_URL. Use Firefox.
    # self.get_episodes_html()
    self.episodes_json_to_html()
    episode_ids = self.get_episode_ids(server_id)

    cached_links = self.get_cached_links() if not force else {}
    need_episodes = {k: v for k, v in episode_ids.items() if not cached_links.get(str(k))}

    if not need_episodes:
      return

    videolinks = self.get_videolinks(need_episodes)
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
    episode_ids = {}
    for element in elements:
      episode_no = int(element['data-base'])
      episode_ids[episode_no] = json.loads(element['data-sources'])[self.server_id]
    return episode_ids

class VideoURLDecoder:
  def __init__(self):
    self.Key = 'c/aUAorINHBLxWTy3uRiPt8J+vjsOheFG1E0q2X9CYwDZlnmd4Kb5M6gSVzfk7pQ'

  def generate_part2(self, t):
    t = re.sub(r'==?$', '', t)
    u = 0
    e = 0
    x = ''
    for c in t:
        u <<= 6 # e <<= 7813 + 2594 * 2 + 2599 * -5
        r = self.Key.find(c)
        u |= r
        e += 6
        if e == 24:
            x += chr((16711680 & u) >> 16)
            x += chr((65280 & u) >> 8)
            x += chr(255 & u)
            u = 0
            e = 0

    if e == 12:
        u >>= 4
        x += chr(u)
    elif e == 18:
        u >>= 2
        x += chr((65280 & u) >> 8)
        x += chr(255 & u)

    return x

  def html_link(self, t, n):
    C = 256
    u = 0
    x = list(range(C))
    for i in range(C):
        u = (u + x[i] + ord(t[i % len(t)])) % C
        x[i], x[u] = x[u], x[i]


    o = 0
    u = 0
    e = ''
    for i in range(len(n)):
        o = (o + i) % C
        u = (u + x[o]) % C
        x[o], x[u] = x[u], x[o]
        e += chr(ord(n[i]) ^ x[(x[o] + x[u]) % C])

    assert e.startswith('http'), e
    return e

  def get(self, hash):
    hash = hash.replace("\\", "") # remove \
    part1 = hash[0:6]
    part2 = self.generate_part2(hash[6:])
    url = self.html_link(part1, part2)
    url = urllib.parse.unquote(url) 
    return url


if __name__ == '__main__':
  decoder = VideoURLDecoder()
  # t = 'vanHb8wY9uwgdVYLsUd3jTSnTWCyIVezi+iqM8z4f6iim7WJW5iiIC0iAUXqwQVH4FT3AeUhVtVp'
  # print(decoder.generate_part2(t))
  # url = 'TDFex7vanHb8wY9uwgdVYLsUd3jTSnTWCyIVezi+iqM8z4f6iim7WJW5iiIC0iAUXqwQVH4FT3AeUhVtVp'
  # print(decoder.get(url))
  # https://9anime.id/watch/my-senpai-is-annoying-dub.1nnzm
  url = 'Dy20Y1ysKegjDYCKGJBJzvuYCi3iGKuE5D0slBSnxDqOA89nyTO8pMWlXBz/IJFaT1SPsw9l9yx3a8Df3B'
  print(decoder.get(url))

  url = 'ImbS1m17PgEWXLOJNMsvTbZNH+XFHLYF6Rg+AJee0fXHfr89bgmmy+9GOlE7bmM6xS\/yPJG20EGvyq5nji'
  url = 'wpfJpC02fj\/KNSL45wXMpzFXnT038s2O0\/SNWNJJDgPwuqRhQufUdSbSvihI0vftPmlOcH4d5dFiGyzj6r'
  url = 'qjApEfLtAiApTgMHkRBlWZGu4Bd6R1nUGdxbM60kxacjaHr7SzQ\/UPL4qUbp2UAQigng5dTWOc0BiojXzi'
  url = 'wpfJpC02fj\/KNSL45wXMpzFXnT038s2O0\/SNWNJJDgPwuqRhQufUdSbSvihI0vftPmlOcH4d5dFiGyzj6r'
  # url = '8u27oef/RW5FOSrUD1PTH2WYa8Mb0EoAYx20OAQaWWz37GPxjUqBQ03pXZt1KgXjYqWg0IyN2FFnzaDUQH'
  print(decoder.get(url))

  url = 'DYIe11DAJYitfckjGLWt8a01xUHgB7DmsHKalmo1xoSH62SZoBTMaYepKNbVq14HLfDqEfCAgcdhZITMRN'
  print(decoder.get(url))

'''
before ajax of episode
L: function(t, n) {
  return new A5 // n=8d422d111457c82439b34e19cc5d1160b089f12d2f361a551db5752ffb5f650c
'''