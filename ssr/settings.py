from os.path import join
from platform import system
from tempfile import gettempdir
from django.conf import settings

BASE_DIR = join(settings.BASE_DIR, '.ssr')
TEMP_DIR = '/tmp' if system() == 'Darwin' else gettempdir()
SCRIPTS_DIR = join(BASE_DIR, 'scripts')
ENTRIES_DIR = join(SCRIPTS_DIR, 'entries')
CACHE_DIR = join(BASE_DIR, 'cache')
BUNDLES_DIR = join(BASE_DIR, 'bundles')
STATIC_DIR = join(BASE_DIR, 'static')
SOCKETS_DIR = join(TEMP_DIR, 'ssr')
HASH_FILE = join(BASE_DIR, 'hash.txt')
SERVER = join(SCRIPTS_DIR, 'server.mjs')
BUNDLER = join(SCRIPTS_DIR, 'bundler.mjs')
