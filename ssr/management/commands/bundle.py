from os import remove
from os.path import exists
from shutil import rmtree
from django.core.management.base import BaseCommand, CommandError
from ...worker import Worker  # type: ignore
from ...settings import Settings  # type: ignore


class Command(BaseCommand):
    help = 'Bundle JavaScript templates using Parcel bundler'

    def handle(self, *args, **options):
        for build_dir in (Settings.bundles_dir, Settings.static_dir):
            if exists(build_dir):
                rmtree(build_dir, ignore_errors=True)
        if exists(Settings.hash_file):
            # Generate new hash for cache busting
            remove(Settings.hash_file)
        worker = Worker()
        worker.use_builders()
        worker.run()
