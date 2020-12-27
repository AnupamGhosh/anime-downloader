import asyncio
import logging
from dataclasses import dataclass

@dataclass
class AsyncGcloudUploader:
  port: int
  ip: str = '127.0.0.1'

  async def upload(self, payload: dict):
    reader, writer = await asyncio.open_connection(self.ip, self.port)

    logging.debug(f'Sending message {payload}')
    writer.write(str(payload))
    await writer.drain()

    data = await reader.read(100)
    logging.debug(f'Received: {data.decode()!r}')

    # Close the connection
    writer.close()
    await writer.wait_closed()

  def create_payload(self, path: str, drive_id: str) -> dict:
    return {
      'path': path,
      'drive_dir': drive_id
    }
