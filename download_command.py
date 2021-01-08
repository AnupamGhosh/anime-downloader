import asyncio
import logging
import os
from asyncio import StreamReader


class DownloadCommand:
  def __init__(self, url: str, save_loc: str, headers: [str]) -> None:
    self.url = url
    self.loc = save_loc
    self.headers = headers

  def run_foreground(self):
    returncode = os.system(str(self))
    return returncode

  async def run_background(self):
    cmd = str(self)
    process = await asyncio.create_subprocess_shell(
      cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    for out in [process.stderr, process.stdout]:
      reader = BufferedReader(out)
      while not out.at_eof():
        line = await reader.readline()
        logging.debug(line)
    
    await process.communicate()
    return process.returncode

  def run(self, mode):
    if mode == DownloadMode.FOREGROUND:
      return self.run_foreground()
    elif mode == DownloadMode.BACKGROUND:
      return asyncio.run(self.run_background())
    else:
      raise ValueError("mode shoud be value in DownloadMode!")

class WgetCommand(DownloadCommand):
  def __init__(self, url: str, save_loc: str, headers: [str]) -> None:
    super().__init__(url, save_loc, headers)

  def __str__(self):
    headers = ' '.join(map(lambda h: f"--header '{h}'", self.headers))
    cmd = f"wget --no-check-certificate {self.url} {headers} -O '{self.loc}'"
    return cmd
    
class CurlCommand(DownloadCommand):
  def __init__(self, url: str, save_loc: str, headers: [str]) -> None:
    super().__init__(url, save_loc, headers)

  def __str__(self):
    headers = ' '.join(map(lambda h: f"-H '{h}'", self.headers))
    cmd = f"curl -k {self.url} {headers} -o '{self.loc}'"
    return cmd


class BufferedReader:
  def __init__(self, reader: StreamReader):
    self.reader = reader
    self.buffer = []

  async def readline(self) -> str:
    while True:
      try:
        byte = await self.reader.readexactly(1)
      except asyncio.IncompleteReadError:
        self.reader.feed_eof()
        return ''
      if byte in [b'\n', b'\r']:
        line = ''.join(self.buffer)
        self.buffer = []
        return line
      else:
        self.buffer.append(byte.decode("utf-8", 'ignore'))

class DownloadMode:
  FOREGROUND = 0
  BACKGROUND = 1

if __name__ == "__main__":
  logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.DEBUG)

  wgetCommand = CurlCommand('https://assets.mixkit.co/videos/download/mixkit-sunlight-passing-through-the-leaves-of-a-tree-34371.mp4', 'temp.mp4', [])
  wgetCommand.run(DownloadMode.BACKGROUND)