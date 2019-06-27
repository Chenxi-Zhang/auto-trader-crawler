
from threading import Thread
import sys
from queue import Queue
from os import path
from core.classes.carspider import (
    CarSpiderMultiThread
)
from core.classes.rabbitmq import (
    open_mq_worker,
    URL_QUEUE_NAME,
    DATA_QUEUE_NAME
)
from core.util.base import (
    BASEDIR
)

def main():
    if len(sys.argv) != 3:
        print('Usage: <ip> <port>')
        return
    ip, port = sys.argv[1], sys.argv[2]
    filepath = path.join(BASEDIR, 'records', 'all-records.txt')
    data_queue = Queue(2000)
    spider = CarSpiderMultiThread(None, url_queue=data_queue)
    t_write = Thread(target=spider.write_car_info, args=(filepath, data_queue, lambda :False))
    t_write.start()
    with open_mq_worker(data_queue, ip, port, queue_name=DATA_QUEUE_NAME) as mq:
        mq.start_receive()

    t_write.join()


if __name__ == "__main__":
    main()
