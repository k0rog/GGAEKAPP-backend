from storages.backends.s3boto3 import S3Boto3Storage
import re
import os


class MediaStorage(S3Boto3Storage):
    location = 'media'

    def get_available_name(self, name, max_length=None):
        while self.exists(name):
            match = re.match('.*\((\d+)\)', name)
            if match:
                name = name[:match.start(1)] + str(int(match.group(1)) + 1) + name[match.end(1):]
            else:
                basename, ext = os.path.splitext(name)
                name = basename + '(1)' + ext
        return name


class StaticStorage(S3Boto3Storage):
    location = 'static'
