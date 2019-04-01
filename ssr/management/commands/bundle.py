from os import remove
from os.path import exists
from shutil import rmtree
from django.core.management.base import BaseCommand, CommandError
from ...worker import Worker  # type: ignore
from ...settings import HASH_FILE, BUNDLES_DIR, STATIC_DIR  # type: ignore


class Command(BaseCommand):
    help = 'Bundle JavaScript templates using Parcel bundler'

    def handle(self, *args, **options):
        for build_dir in (BUNDLES_DIR, STATIC_DIR):
            if exists(build_dir):
                rmtree(build_dir, ignore_errors=True)
        if exists(HASH_FILE):
            # Generate new hash for cache busting
            remove(HASH_FILE)
        worker = Worker()
        worker.use_builders()
        try:
            worker.run()
        except Exception as exception:
            raise CommandError(exception)
