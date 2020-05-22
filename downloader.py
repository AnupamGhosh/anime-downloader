# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url, 
# eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
# analyze every params carefully when editing
# _ param is specific to urls and remains same for an anime page
# Currently the _ params are pinned to fairy tail dub
# @TODO need to find a way to automatically fetch _ from all.js

from HTMLParser import HTMLParser
import logging
import time
import random
import json
import os
import re

from make_request import Request, Request9anime

SERVER = 35 # mp4upload

class HTMLParser9anime(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.state_mc = EpisodeInfoMachine()

  def handle_starttag(self, tag, attrs):
    self.state_mc.start_tag(tag, attrs)

  def handle_endtag(self, tag):
    self.state_mc.end_tag(tag)

  def get_ep_ids(self):
    return self.state_mc.ep_infos

  @staticmethod
  def attrs2dict(attrs):
    return {name: value for name, value in attrs}


class EpisodeInfoMachine:
  def __init__(self):
    self.ep_infos = []
    self.SERVER = str(SERVER)
    self.state_server = StateServer(self)
    self.state_li = StateLi(self)
    self.state_start = StateStart(self)
    self.state_ul = StateUl(self)

    self.state = self.state_start

  def start_tag(self, tag, attrs):
    self.state = self.state.next_state(tag, attrs)

  def end_tag(self, tag):
    self.state = self.state.next_state(tag, [], close=True)

class StateStart(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)
    div_classes = attr.get('class', '').split(' ')
    data_id = attr.get('data-id')

    if 'server' in div_classes and data_id == self.mc.SERVER:
      return self.mc.state_server
    return self

class StateServer(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)
    ul_classes = attr.get('class', '').split(' ')

    if tag == 'ul' and 'episodes' in ul_classes and 'range' in ul_classes:
      return self.mc.state_ul
    return self

class StateUl(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    if tag == 'li' and not close:
      return self.mc.state_li
    if tag == 'ul' and close:
      return self.mc.state_server
    return self

class StateLi(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)

    if tag == 'li' and close:
      return self.mc.state_ul
        
    if tag == 'a' and not close:
      self.mc.ep_infos.append(attr['data-id'])
      assert int(attr['data-base']) == len(self.mc.ep_infos)
    return self

class Downloader(object):

  def __init__(self, base_path, name_prefix, start, episode_count, save_dir):
    self.base_path = base_path
    self.filename_prefix = name_prefix
    self.start_episode = start - 1
    self.get_episodes = episode_count
    self.save_dir = save_dir
    self.request = Request9anime(base_path)
    self.anime_html_filepath = os.path.join(CUR_DIR, '%s-python.html' % self.filename_prefix)

  def store_cookies(self):
    paths = [self.base_path, '/user/ajax/menu-bar']
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


  def get_episodes_html(self):
    path_matched = re.search(r".*\.(\w+)\/(\w+)", self.base_path)
    servers_id = path_matched.group(1)
    episode_id = path_matched.group(2)
    episode_url = '/ajax/film/servers'
    content = self.request.get(episode_url, {'id': servers_id, 'episode': episode_id})

    try:
      html_episodes = json.loads(content)['html']
      path = self.anime_html_filepath
      with open(path, 'w') as html_text:
        html_text.write(html_episodes)
    except Exception as e:
      logging.debug("content:\n%s", content)
      raise e

  def parse_episode_html(self):
    parser = HTMLParser9anime()
    path = self.anime_html_filepath
    with open(path, 'r') as html_text:
      html_text = open(path, 'r')
      parser.feed(html_text.read())
    return parser

  def get_mcloudKey(self):
    mcloud_headers = {
      'referer': '%s%s' % (Request9anime.DOMAIN, self.base_path)
    }
    mcloud_js_val = Request(mcloud_headers).get('https://mcloud2.to/key')
    mcloud_regex = re.search(r"mcloudKey=['\"](\w+)['\"]", mcloud_js_val)
    mcloudKey = mcloud_regex.group(1)
    return mcloudKey

  def download_videos(self, parser):
    # get video source html page
    start = self.start_episode
    get_episodes = self.get_episodes
    anime_ep_ids = parser.get_ep_ids()[start: start + get_episodes]
    source_info_path = '/ajax/episode/info'
    mcloud = self.get_mcloudKey()
    logging.debug('headers:\n%s', self.request.headers)
    for i in xrange(get_episodes):
      logging.debug("Episode %s data-id=%s", start + i + 1, anime_ep_ids[i])
      current_ep = start + i + 1
      # most sensitive code
      content = self.request.get(source_info_path, {'id': anime_ep_ids[i], 'server': SERVER, 'mcloud': mcloud})
      logging.info("source_info_url response:\n%s", content)
      source_html_url = json.loads(content)['target']

      logging.debug("Source html url: %s", source_html_url)
      source_html_path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (self.filename_prefix, current_ep))
      source_html = Request().get(source_html_url)
      with open(source_html_path, 'w') as source_html_file:
        source_html_file.write('<!-- %s -->\n' % source_html_url)
        source_html_file.write(source_html)

      html = source_html
      video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', html, re.MULTILINE)
      url_info = video_info_match.group(1).split('|')
      download_link = 'https://{subdomain}.mp4upload.com:{port}/d/{video_dir}/video.{ext}'.format(
        subdomain=url_info[27], port=url_info[56], video_dir=url_info[55], ext=url_info[25]
      )
      logging.debug("Download link: %s", download_link)
      save_as = os.path.join(self.save_dir, '%s%s.mp4' % (self.filename_prefix, current_ep))
      returncode = os.system('wget --no-check-certificate %s -O %s' % (download_link, save_as)) and os.system(
          'curl -k %s -o %s' % (download_link, save_as))
      if not returncode:
        os.remove(source_html_path)

  def download(self):
    self.store_cookies()
    self.get_episodes_html()
    parser = self.parse_episode_html()
    self.download_videos(parser)
    os.remove(self.anime_html_filepath)


logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.INFO)
CUR_DIR = os.path.dirname(__file__)
with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
  config = json.load(config_fp)
BASE_PATH = config['base_path']
Downloader(
    BASE_PATH, config['filename_prefix'], config['start_episode'], config['get_episodes'],
    str(config['save_in']).replace(' ', '\\ ')
).download()
