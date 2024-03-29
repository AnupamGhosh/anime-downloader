import json
import os
import sys
from pathlib import Path

import utils
from download_command import DownloadMode
from file_downloader import StreamtapeDownloader, Mp4uploadDownloader
from gcloud_upload_client import GdriveUploader
from logger import logging
from nine_anime import NineAnime


def main():
  CUR_DIR = os.path.dirname(__file__)
  with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
    config = json.load(config_fp)
  start_episode = config['start_episode']
  last_episode = config.get('end_episode')
  if not last_episode:
    episodes_count = config['get_episodes']
    last_episode = start_episode + episodes_count - 1

  filename_prefix = config['filename_prefix']
  cache_dir = utils.get_cache_directory(filename_prefix)
  download_from = config.get('download_from')
  VideoDownloader = Mp4uploadDownloader
  if download_from == 'streamtape':
    VideoDownloader = StreamtapeDownloader
  video_repo = VideoDownloader(cache_dir)
  server_id = video_repo.server_id
  save_at = Path(config['save_in'])
  download_mode = DownloadMode.FOREGROUND if sys.stdout.isatty() else DownloadMode.BACKGROUND

  nine_anime = NineAnime(config['base_path'], filename_prefix)
  nine_anime.update_videolinks(server_id)
  videolinks = nine_anime.get_cached_links()

  if config.get('upload_to'):
    drive_id = str(config['upload_to'])
    uploader = GdriveUploader(4242, drive_id)
    video_repo.add_subscriber(uploader)

  for episode in range(start_episode, last_episode + 1):
    videolink = videolinks.get(str(episode))
    if not videolink:
      logging.info(f'videolink unavailable for episode {episode}. Skipping.')
      continue

    save_loc = os.path.join(save_at, f'{filename_prefix}{episode}')
    video_repo.download(videolink, save_loc, download_mode)


if __name__ == "__main__":
  main()