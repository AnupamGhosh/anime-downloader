import os
from pathlib import Path

def get_cache_directory(dir_name: str) -> Path:
  cache_dir = os.path.join(Path(__file__).parent, '__pycache__', dir_name)
  path = Path(cache_dir)
  if not path.is_dir():
    path.mkdir()

  return path