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

    async def queue_all_car_url(self, callback):
        async for url in self.get_all_href_visited_excluded_itr():
            url = self._url_validation(url)
            # car = CarParser(url)
            callback(url)
            print('Return: ' + url)

    def _url_validation(self, url):
        if url.startswith('/') or url.startswith('#'):
            url = url_concat([domain, url])
        return url

class CarSpiderMultiThread(object):
    def __init__(self, spider, url_queue=None, car_response_queue=None, car_record_queue=None):
        self.spider = spider
        self.car_url_queue = url_queue if url_queue else Queue(2000)
        self.url_load_finished = False
        self.car_response_queue = car_response_queue if car_response_queue else Queue(2000)
        self.response_load_finished = False
        self.car_record_queue = car_record_queue if car_record_queue else Queue(2000)
        self.record_load_finished = False

    def loading_cars(self, callback=print, loader_func=None):
        if not loader_func:
            loader_func = self.spider.queue_all_car_url
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()

        loop.run_until_complete(loader_func(callback))
        self.url_load_finished = True

    def is_url_load_finished(self):
        return self.url_load_finished

    def request_car(self, input_queue, max_worker=32, callback=print, finish_sign=None):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        # if not callback:
        #     def _callback(data):
        #         print(data)
        #     callback = _callback
        if not finish_sign:
            finish_sign = self.is_url_load_finished
        while not finish_sign() or not input_queue.empty():
            loop.run_until_complete(async_get_html_response(input_queue, callback, max_worker))
        self.response_load_finished = True

    def is_response_load_finished(self):
        return self.response_load_finished

    def parse_car_page(self, input_queue=None, callback=print, finish_sign=None):
        car_parser = CarParser('')
        # if not callback:
        #     callback = print
        if not input_queue:
            input_queue = self.car_url_queue
        if not finish_sign:
            finish_sign = self.is_response_load_finished
        while not finish_sign() or not input_queue.empty():
            try:
                resp = input_queue.get(timeout=3)
                if not resp:
                    continue
                soup = bs_parse(resp)
                record = car_parser.is_car_page(soup)
                if not record:
                    continue
                callback(record)
                print('car parsed')
            except Exception as e:
                print(e)

    def is_record_load_finished(self):
        return self.record_load_finished

    def write_car_info(self, filepath, input_queue, finish_sign=None):
        if not finish_sign:
            finish_sign = self.is_record_load_finished
        with open(filepath, 'w+') as f:
            def _callback(data):
                data = data + '\n'
                f.write(data)
                print('recording...')
            self.record_car_info(input_queue, _callback, finish_sign)
        #     while not finish_sign() or not input_queue.empty():
        #         try:
        #             record = input_queue.get(timeout=3)
        #             record = serialize_dict(record) + '\n'
        #             f.write(record)
        #             print("recording...")
        #         except:
        #             pass
        # print('record write finished')

    def record_car_info(self, input_queue, callback=print, finish_sign=None):
        if not finish_sign:
            finish_sign = self.is_record_load_finished
        while not finish_sign() or not input_queue.empty():
            try:
                print('Try to record data')
                record = input_queue.get(timeout=3)
                callback(record)
                print('Record successful')
            except Exception as e:
                print(e)


    def go(self, thread_num=4):
        t_loading = Thread(target=self.loading_cars, args=(self.car_url_queue.put,))
        t_loading.start()
        t_request = Thread(target=self.request_car, args=(self.car_url_queue, 128, self.car_response_queue.put))
        t_request.start()
        threads = []
        for _ in range(thread_num):
            t_parse = Thread(target=self.parse_car_page, args=(self.car_response_queue, self.car_record_queue.put))
            threads.append(t_request)
            t_parse.start()
        filepath = path.join(BASEDIR, 'records', 'all-records.txt')
        t_writing = Thread(target=self.write_car_info, args=(filepath, self.car_record_queue))
        t_writing.start()
        t_loading.join()
        t_request.join()
        for t in threads:
            t.join()
        self.record_load_finished = True
        t_writing.join()

    def start_url_load(self, url_queue=None):
        if not url_queue:
            url_queue = self.car_url_queue
        t_loading = Thread(target=self.loading_cars, args=(url_queue.put,))
        t_loading.start()
        return t_loading
