from queue import Queue
import concurrent.futures as cf
import asyncio
from threading import Thread
from os import path
from .spider import Spider
from .carparser import CarParser
from ..util.base import (
    url_concat,
    str_to_url,
    url_add_query,
    serialize_dict,
    BASEDIR,
    url_remove_query,
    async_get_html_response_itr,
    bs_parse,
    async_get_html_response
)

car_base_url = 'http://www.autotrader.ca/cars'
domain = 'http://www.autotrader.ca'

class CarSpider(Spider):
    '''
    '''
    visited_web = {'/'}
    def __init__(self, brand, num, limit=100, offset=0):
        super().__init__(None)
        self.visited_web = CarSpider.visited_web
        self.brand = brand
        self.num = num
        self.base_url = url_concat([car_base_url, str_to_url(brand)])
        self.db_limit = limit
        self.db_offset = offset
        self.car_list_url_queue = Queue()
        self.car_url_queue = Queue()

    def load_part_list(self, limit, offset):
        '''
        `/cars/${make}?rcp=${record per page}&rcs=${offset}`
        '''
        url = url_add_query(self.base_url, rcp=limit, rcs=offset)
        response = self._load_content(url)
        return response

    async def car_list_response_itr(self):
        while self.db_offset < self.num:
            # response = self.load_part_list(self.db_limit, self.db_offset)
            self.car_list_url_queue.put(url_add_query(self.base_url, rcp=self.db_limit, rcs=self.db_offset))
            self.db_offset += self.db_limit
        while not self.car_list_url_queue.empty():
            async for response in async_get_html_response_itr(self.car_list_url_queue):
                if response:
                    yield response

    async def get_all_href_visited_excluded_itr(self):
        async for resp in self.car_list_response_itr():
            print('In get all href func: ' + str(resp))
            for url in self.parse_all_href_itr(resp):
                if not self.has_visited(url):
                    self.add_to_visit(url)
                    yield url

    async def get_all_car_info_itr(self):
        '''
        single thread method
        '''
        async for url in self.get_all_href_visited_excluded_itr():
            car = self.get_car_info(url)
            if car:
                yield car

    def get_car_info(self, url):
        url = self._url_validation(url)
        car = CarParser(url)
        if car.is_car_page():
            return car

    async def queue_all_car_url(self, queue):
        async for url in self.get_all_href_visited_excluded_itr():
            url = self._url_validation(url)
            # car = CarParser(url)
            queue.put(url)
            print('Put url to url_queue: ' + url)

    def _url_validation(self, url):
        if url.startswith('/') or url.startswith('#'):
            url = url_concat([domain, url])
        return url

class CarSpiderMultiThread(object):
    def __init__(self, spider, url_queue=None, car_response_queue=None, car_record_queue=None):
        self.spider = spider
        self.car_url_queue = url_queue if url_queue else Queue(2000)
        self.load_car_url_finished = False
        self.car_response_queue = car_response_queue if car_response_queue else Queue(2000)
        self.load_car_response_finished = False
        self.car_record_queue = car_record_queue if car_record_queue else Queue(2000)
        self.load_car_record_finished = False

    def loading_cars(self, loader_func=None):
        if not loader_func:
            loader_func = self.spider.queue_all_car_url
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(loader_func(self.car_url_queue))
        self.load_car_url_finished = True

    def is_load_car_url_finished(self):
        return self.load_car_url_finished

    def request_car(self, max_worker=32):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        while not self.load_car_url_finished or not self.car_url_queue.empty():
            loop.run_until_complete(async_get_html_response(self.car_url_queue, self.car_response_queue, max_worker))
        self.load_car_response_finished = True

    def is_load_car_info_finished(self):
        return self.load_car_response_finished

    def parse_car_page(self):
        car_parser = CarParser('')
        while not self.load_car_response_finished or not self.car_response_queue.empty():
            try:
                resp = self.car_response_queue.get(timeout=3)
                if not resp:
                    continue
                soup = bs_parse(resp)
                record = car_parser.is_car_page(soup)
                if not record:
                    continue
                self.car_record_queue.put(record)
            except:
                pass

    def record_car_info(self, filepath):
        with open(filepath, 'w+') as f:
            while not self.load_car_record_finished or not self.car_record_queue.empty():
                try:
                    record = self.car_record_queue.get(timeout=3)
                    record = serialize_dict(record) + '\n'
                    f.write(record)
                    print("recording...")
                except:
                    pass
        # print('record write finished')

    def go(self, thread_num=4):
        t_loading = Thread(target=self.loading_cars)
        t_loading.start()
        t_request = Thread(target=self.request_car, args=(128,))
        t_request.start()
        threads = []
        for _ in range(thread_num):
            t_parse = Thread(target=self.parse_car_page)
            threads.append(t_request)
            t_parse.start()
        filepath = path.join(BASEDIR, 'records', self.spider.brand+'.txt')
        t_writing = Thread(target=self.record_car_info, args=(filepath,))
        t_writing.start()
        t_loading.join()
        t_request.join()
        for t in threads:
            t.join()
        self.load_car_record_finished = True
        t_writing.join()
