import unicodedata

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
