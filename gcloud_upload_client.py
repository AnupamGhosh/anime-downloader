import asyncio
import json
import logging
from dataclasses import dataclass

@dataclass
class AsyncGdriveConnector:
  port: int
  ip: str = '127.0.0.1'

  async def connect(self, payload: dict):
    reader, writer = await asyncio.open_connection(self.ip, self.port)

    logging.debug(f'Sending message {payload}')
    writer.write(json.dumps(payload).encode())
    await writer.drain()

    data = await reader.read(100)
    logging.debug(f'Received: {data.decode()!r}')

    # Close the connection
    writer.close()
    await writer.wait_closed()


class GdriveUploader:
  def __init__(self, port: int, drive_id: str):
    self._uploader = AsyncGdriveConnector(port)
    self.drive_id = drive_id

  def notify(self, path):
    self.upload(path)

  def upload(self, path):
    payload = self.create_payload(path)
    logging.info('payload=%s', payload)
    asyncio.create_task(self._uploader.connect(payload))

  def create_payload(self, path: str) -> dict:
    return {
      'path': path,
      'drive_dir': self.drive_id
    }


def main():
  drive_id = '14BzAsfL5ZOC8oH2pWgjOjilEapUWeDqH'
  uploader = GdriveUploader(4242, drive_id)
  uploader.upload('/Users/anupamghosh/Movies/Anohana/ano.mp4')

if __name__ == "__main__":
    main()