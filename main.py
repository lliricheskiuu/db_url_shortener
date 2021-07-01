import random

from pathlib import Path
from urllib.parse import urlparse
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.core.management import execute_from_command_line
from django.urls import path, reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils.baseconv import base56

BASE_DIR = Path(__file__).resolve().parent

settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    SECRET_KEY='secret',
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [''],
        }
    ],
    DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'key_link.sqlite3'
            }
    },
)

ALLOWED_SCHEMES = {'http', 'https', 'ftp'}
MIN_KEY, MAX_KEY = 80106440, 550731775


def url_redirect(request, key):

    with connection.cursor() as cur:
        query_select = 'select link from key_link where key=%s'
        cur.execute(query_select, [key])
        link = cur.fetchone()

    return redirect(to=link)


def url_shortener(request):
    ctx = {}

    query_create = 'create table if not exists key_link (key text, link text)'
    with connection.cursor() as cur:
        cur.execute(query_create)
        print('create db key_link', cur.rowcount)

    with connection.cursor() as cur:
        delete = 'delete from key_link'
        cur.execute(delete)
        print(delete, cur.rowcount)

    if request.POST:
        url = request.POST.get('url')
        if urlparse(url).scheme in ALLOWED_SCHEMES:
            key = base56.encode(random.randint(MIN_KEY, MAX_KEY))
            cache.add(key, url)

            with connection.cursor() as cur:
                values = (key, url)
                query_insert = 'insert into key_link (key,link) values (%s,%s)'
                cur.execute(query_insert, values)
                print(query_insert, cur.rowcount)

            ctx['key'] = key
        else:
            ctx['message'] = f'Invalid URL {url}. Allowed schemes: ' + ','.join(ALLOWED_SCHEMES)
    return render(request, 'result.html', ctx)


urlpatterns = [
    path('url', url_shortener),
    path('url/<key>', url_redirect, name='url_redirect')
]

if __name__ == '__main__':
    execute_from_command_line()