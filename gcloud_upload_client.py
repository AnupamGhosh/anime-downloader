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

    response = await reader.read(100)
    logging.debug(f'Received: {response.decode()!r}')

    # Close the connection
    writer.close()
    await writer.wait_closed()
    return response


class GdriveUploader:
  def __init__(self, port: int, drive_id: str):
    self._uploader = AsyncGdriveConnector(port)
    self.drive_id = drive_id

  def notify(self, path):
    self.upload(path)

  def upload(self, path):
    payload = self.create_payload(path)
    logging.info('payload=%s', payload)
    response = asyncio.run(self._uploader.connect(payload))
    return response

  def create_payload(self, path: str) -> dict:
    return {
      'path': path,
      'drive_dir': self.drive_id
    }


def main():
  logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.DEBUG)
  drive_id = '14BzAsfL5ZOC8oH2pWgjOjilEapUWeDqH'
  uploader = GdriveUploader(4242, drive_id)
  response = uploader.upload('/Users/anupamghosh/Movies/Anohana/ano.mp4')
  logging.debug(f'response={response}')

if __name__ == "__main__":
    main()