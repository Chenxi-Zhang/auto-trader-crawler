import urllib.parse as urlparser
import json
import requests
import asyncio
import concurrent.futures as cf
import os
from bs4 import BeautifulSoup as bs

BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def url_remove_query(url):
    '''

    :param url: str
    :return: str
    '''
    url_part = list(urlparser.urlparse(url))
    url_part[4] = ''
    return urlparser.urlunparse(url_part)

def url_add_query(url, **kwargs):
    '''
    :param url: str
    :param kwargs: query dict
    '''
    url_part = list(urlparser.urlparse(url))
    query = dict(urlparser.parse_qsl(url_part[4]))
    query.update(kwargs)
    url_part[4] = urlparser.urlencode(query)
    return urlparser.urlunparse(url_part)

def url_concat(url_part_list):
    '''

    :param url_part_list: list of url part
    :return: str
    '''
    url = [k[1:] if k.startswith('/') else k for k in url_part_list]
    return '/'.join(url)

def str_to_url(str):
    '''
    '''
    return urlparser.quote(str)

def get_html_response(url):
    '''

    :param url: str
    :return: response
    '''
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
    try:
        print('Try request to: ' + url)
        response = requests.get(url, headers=headers)
        response.url = url
    except Exception as e:
        print(e)
        response = None
    return response

def queue_response_from_url(url, response_queue):
    response_queue.put(get_html_response(url))

async def async_get_html_response(url_queue, callback, max_worker=32):
    '''
    Core method to get multiple responses asynchronically
    '''
    urls = get_urls_from_queue(url_queue, max_worker)
    print('length of loaded url: ' + str(len(urls)))
    if not urls:
        return
    with cf.ThreadPoolExecutor(max_workers=max_worker) as executor:
        loop = asyncio.get_event_loop()
        futures = (
            loop.run_in_executor(
                executor,
                get_html_response,
                url
            ) for url in urls
        )
        for result in await asyncio.gather(*futures):
            callback(result)

async def async_get_html_response_itr(url_queue, max_worker=32):
    urls = get_urls_from_queue(url_queue, max_worker)
    print('length of loaded url: ' + str(len(urls)))
    if not urls:
        return
    with cf.ThreadPoolExecutor(max_workers=max_worker) as executor:
        loop = asyncio.get_event_loop()
        futures = (
            loop.run_in_executor(
                executor,
                get_html_response,
                url
            ) for url in urls
        )
        for result in await asyncio.gather(*futures):
            yield result

async def async_exec_func_list(callable_list, *args, max_worker=32):
    with cf.ThreadPoolExecutor(max_workers=max_worker) as executor:
        loop = asyncio.get_event_loop()
        futures = (
            loop.run_in_executor(
                executor,
                func,
                args
            ) for func in callable_list
        )
        for result in await asyncio.gather(*futures):
            pass

async def async_exec_func_list_itr(callable_list, *args, max_worker=32):
    print(args)
    with cf.ThreadPoolExecutor(max_workers=max_worker) as executor:
        loop = asyncio.get_event_loop()
        futures = (
            loop.run_in_executor(
                executor,
                func,
                args
            ) for func in callable_list
        )
        for result in await asyncio.gather(*futures):
            yield result

def get_urls_from_queue(url_queue, num=1):
    urls = []
    try:
        for _ in range(num):
            url = url_queue.get(timeout=1)
            if type(url) == bytes:
                url = str(url, 'utf8')
            urls.append(url)
    except:
        print('In async request, not enough url in url_queue')
    return urls

def bs_parse(response):
    '''

    :param response: response
    :return: soup
    '''
    soup = bs(response.content, 'html.parser')
    soup.url = response.url
    return soup

def soup_find_tag(soup, pattern, attr={}):
    '''
    param soup: soup
    param pattern: str
    param attr: dict
    return: tag
    '''
    return soup.find(pattern, attr)

def soup_tag_itr(soup, pattern, attr={}):
    '''
    '''
    tag = soup.find(pattern, attr)
    while tag:
        yield tag
        tag = tag.find_next(pattern, attr)

def serialize_dict(d):
    '''
    :param d: dict
    :return: str
    '''
    return json.dumps(d)

def deserialize_str(s):
    '''
    :param s: str
    :return: dict
    '''
    return json.loads(s)
