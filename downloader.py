# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url,
# eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
# analyze every params carefully when editing API calls

from HTMLParser import HTMLParser
import logging
import json
import os
import re

from make_request import Request, Request9anime
from querySelector import GetElements, SearchNodeParser

class EpisodeDataId(GetElements):
  def __init__(self, html, server_id):
    selector = [
      {'tag': 'div', 'class': ['server'], 'attr': {'data-id': str(server_id)}},
      {'tag': 'ul', 'class': ['episodes']},
      {'tag': 'a'}
    ]
    self.episode_ids = []
    super(EpisodeDataId, self).__init__(selector)
    parser = SearchNodeParser(self)
    parser.feed(html)

  def matched_element(self, attr):
    ep_no = int(attr['data-base'])
    if ep_no <= len(self.episode_ids):
      self.episode_ids[ep_no - 1] = attr['data-id']
    else:
      self.episode_ids.append(attr['data-id'])
    assert ep_no == len(self.episode_ids)

  def get_episode_ids(self):
    return self.episode_ids

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

  def get_episode_ids(self):
    path = self.anime_html_filepath
    with open(path, 'r') as fp:
      html = fp.read()
    parser = EpisodeDataId(html, SERVER)
    return parser.get_episode_ids()

  def get_mcloudKey(self):
    mcloud_headers = {
      'referer': '%s%s' % (Request9anime.DOMAIN, self.base_path)
    }
    mcloud_js_val = Request(mcloud_headers).get('https://mcloud.to/key')
    mcloud_regex = re.search(r"mcloudKey=['\"](\w+)['\"]", mcloud_js_val)
    mcloudKey = mcloud_regex.group(1)
    return mcloudKey

  def download_videos(self, episode_ids):
    # get video source html page
    start = self.start_episode
    get_episodes = self.get_episodes
    anime_ep_ids = episode_ids[start: start + get_episodes]
    source_info_path = '/ajax/episode/info'
    mcloud = self.get_mcloudKey()
    logging.debug('headers:\n%s', self.request.headers)
    for i in xrange(get_episodes):
      logging.debug("Episode %s data-id=%s", start + i + 1, anime_ep_ids[i])
      current_ep = start + i + 1
      # most sensitive code
      content = self.request.get(source_info_path, {
          'id': anime_ep_ids[i], 'server': SERVER, 'mcloud': mcloud})
      logging.info("source_info_url response:\n%s", content)
      source_html_url = json.loads(content)['target']

      logging.debug("Source html url: %s", source_html_url)
      source_html_path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (
          self.filename_prefix, current_ep))
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
      returncode = os.system('wget --no-check-certificate %s -O %s' % (
          download_link, save_as)) and os.system('curl -k %s -o %s' % (download_link, save_as))
      if not returncode:
        os.remove(source_html_path)

  def download(self):
    self.store_cookies()
    self.get_episodes_html()
    episode_ids = self.get_episode_ids()
    self.download_videos(episode_ids)
    os.remove(self.anime_html_filepath)


logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.INFO)
CUR_DIR = os.path.dirname(__file__)
SERVER = 35
with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
  config = json.load(config_fp)
BASE_PATH = config['base_path']
Downloader(
    BASE_PATH, config['filename_prefix'], config['start_episode'], config['get_episodes'],
    str(config['save_in']).replace(' ', '\\ ')
).download()
