import logging
import os
import unicodedata
from logging.handlers import TimedRotatingFileHandler

import pytils as pytils
from django.core.files.storage import FileSystemStorage


class ASCIIFileSystemStorage(FileSystemStorage):
    """
    Convert unicode characters in name to ASCII characters.
    """

    def get_valid_name(self, name):
        name_parts = name.split('.')
        name = unicodedata.normalize('NFKD', pytils.translit.slugify(name_parts[0])).encode('ascii', 'ignore').decode()
        name = name + '.' + name_parts[-1]
        return super(ASCIIFileSystemStorage, self).get_valid_name(name)


def get_logger(loglevel=logging.INFO):
    logger = logging.getLogger('MessageWorker')
    logger.setLevel(loglevel)
    fp = TimedRotatingFileHandler(os.path.dirname(os.path.realpath(__file__)) +
                                  '/../log', when='D', interval=2,
                                  backupCount=7)
    fp.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s: [%(levelname)s] %(message)s')
    fp.setFormatter(formatter)
    logger.addHandler(fp)
    return logger
