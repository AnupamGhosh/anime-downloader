import logging
import sys

def setup_logger():
  stdout_handler = logging.StreamHandler(stream=sys.stdout)
  stdout_formatter = logging.Formatter('%(filename)s:%(funcName)s:%(lineno)d %(levelname)s %(message)s')

  logger = logging.getLogger()
  stdout_handler.setFormatter(stdout_formatter)
  logger.addHandler(stdout_handler)
  loglevel = logging.INFO if sys.stdout.isatty() else logging.DEBUG
  logger.setLevel(loglevel)
  return logger

logging = setup_logger()