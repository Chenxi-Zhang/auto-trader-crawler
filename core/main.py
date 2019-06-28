
import time
import sys
from queue import Queue
from core.classes.carspider import (
    CarSpiderMultiThread,
    CarSpider,
)
from core.classes.makes import Makes
from core.classes.rabbitmq import (
    open_mq_sender,
    open_mq_worker,
    URL_QUEUE_NAME
)

def main():
    if len(sys.argv) != 3:
        print('Usage: <ip> <port>')
        return
    ip, port = sys.argv[1], sys.argv[2]
    maker = Makes()
    make = maker.load_makes(1)
    for brand, num in make.items():
        url_queue = Queue(2000)
        spider = CarSpider(brand, num)
        c = CarSpiderMultiThread(spider)
        t = c.start_url_load(url_queue)
        with open_mq_sender(url_queue, ip, port, queue_name=URL_QUEUE_NAME) as sender:
            sender.start_send(finish_sign=c.is_url_load_finished)
        t.join()

if __name__ == "__main__":
    main()
