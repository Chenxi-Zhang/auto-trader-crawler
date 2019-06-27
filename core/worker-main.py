
import sys
from queue import Queue
from threading import Thread

from core.classes.carspider import CarSpiderMultiThread
from core.classes.rabbitmq import (
    open_mq_worker,
    open_mq_sender,
    URL_QUEUE_NAME,
    DATA_QUEUE_NAME
)
from core.util.base import serialize_dict

def receive_url(url_queue, ip, port, ch_queue_name):
    with open_mq_worker(url_queue, ip, port, ch_queue_name) as mq:
        mq.start_receive()

def send_data(data_queue, ip, port, ch_queue_name):
    with open_mq_sender(data_queue, ip, port, ch_queue_name) as mq:
        mq.start_send(serialize_dict)

def request_url(url_queue, response_queue):
    car_spider = CarSpiderMultiThread(None, url_queue)
    car_spider.request_car(url_queue, 32, response_queue.put)

def main():
    if len(sys.argv) != 3:
        print('Usage: <ip> <port>')
        return
    ip, port = sys.argv[1], sys.argv[2]
    thread_num = 4
    url_queue = Queue(2000)
    response_queue = Queue(2000)
    car_record_queue = Queue(2000)
    spider = CarSpiderMultiThread(None, url_queue=url_queue, car_response_queue=response_queue, car_record_queue=car_record_queue)
    t_receive = Thread(target=receive_url, args=(url_queue, ip, port, URL_QUEUE_NAME))
    t_receive.start()
    t_request = Thread(target=request_url, args=(url_queue, response_queue))
    t_request.start()
    threads_parse = []
    for i in range(thread_num):
        t_parse = Thread(target=spider.parse_car_page, args=(response_queue, car_record_queue.put))
        t_parse.start()
        threads_parse.append(t_parse)
    t_send = Thread(target=send_data, args=(car_record_queue, ip, port, DATA_QUEUE_NAME))
    t_send.start()

    t_receive.join()
    t_request.join()
    for t_parse in threads_parse:
        t_parse.join()
    t_send.join()



if __name__ == "__main__":
    main()
