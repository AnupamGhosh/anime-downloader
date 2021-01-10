# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url,
# eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
# analyze every params carefully when editing API calls

import json
import os
import re
import sys
from pathlib import Path

from download_command import DownloadMode
from file_downloader import Mp4uploadDownloader, StreamtapeDownloader
from gcloud_upload_client import GdriveUploader
from logger import logging
from make_request import Request, Request9anime
from nine_anime import NineAnime, VideoURLDecoder
from querySelector import GetElements, SearchNodeParser


def main():
  CUR_DIR = os.path.dirname(__file__)
  with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
    config = json.load(config_fp)
  episodes_count = config['get_episodes']
  download_from = StreamtapeDownloader() # Mp4uploadDownloader()
  server_id = download_from.server_id
  save_at = Path(config['save_in'])
  download_mode = DownloadMode.FOREGROUND if sys.stdout.isatty() else DownloadMode.BACKGROUND

  nine_anime = NineAnime(
      config['base_path'], config['filename_prefix'], config['start_episode'], episodes_count
  )
  nine_anime.update_videolinks(server_id)
  print(nine_anime.get_cached_links())


  # if config.get('upload_to'):
  #   drive_id = str(config['upload_to'])
  #   uploader = GdriveUploader(4242, drive_id)
  #   downloader.add_subscriber(uploader)


if __name__ == "__main__":
  main()