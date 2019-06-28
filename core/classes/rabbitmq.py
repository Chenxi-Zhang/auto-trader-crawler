from ..util.rabbitmq import (
    connect_to,
    send,
    URL_QUEUE_NAME,
    DATA_QUEUE_NAME
)

def open_mq_connection(ip, port=None):
    return MQbase(ip, port)

def open_mq_sender(queue, ip, port=None, queue_name='send-queue'):
    return MQSender(queue, ip, port, queue_name)

def open_mq_worker(queue, ip, port=None, queue_name='receive-queue'):
    return MQWorker(queue, ip, port, queue_name)

class MQbase(object):
    def __init__(self, ip, port=None, queue_name='my-queue'):
        self.ip = ip
        self.port = port
        self.conn = None
        self.channel = None
        self.queue_name = queue_name

    def __enter__(self):
        self.conn = connect_to(self.ip, self.port)
        self.channel = self.conn.channel()
        self.channel.queue_declare(queue=self.queue_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.channel.close()
        self.conn.close()

    def reconnect(self):
        if self.channel.is_open:
            self.channel.close()
        if self.conn.is_open:
            self.conn.close()
        self.__enter__()

    def send_msg(self, msg):
        # print('MQ: message sending...')
        send(self.channel, msg, self.queue_name)
        print('MQ: send successful')

    def set_receive(self, callback=None):
        if not callback:
            def _callback(ch, method, props, body):
                self.consume_data(body)
            callback = _callback
        self.channel.basic_consume(
            on_message_callback=callback,
            queue=self.queue_name,
            auto_ack=True
        )

    def consume_data(self, data):
        print(data)


class MQSender(MQbase):
    def __init__(self, send_queue, ip, port=None, queue_name='send-queue'):
        super().__init__(ip, port, queue_name)
        self.send_queue = send_queue
        self.is_send_over = False

    def send_over(self):
        self.is_send_over = True

    def start_send(self, data_serializer=None, finish_sign=None):
        if not finish_sign:
            finish_sign = self.send_over
        while not finish_sign() or not self.send_queue.empty():
            try:
                data = self.send_queue.get(timeout=3)
                if data_serializer:
                    data = data_serializer(data)
                if type(data) == str:
                    data = data.encode('utf8')
                if self.channel.is_closed:
                    self.reconnect()
                self.send_msg(data)
            except Exception as e:
                print(e)

class MQWorker(MQbase):
    def __init__(self, receive_queue, ip, port=None, queue_name='receive-queue'):
        super().__init__(ip, port, queue_name)
        self.receive_queue = receive_queue
        self.is_receive_over = False

    def start_receive(self):
        self.set_receive()
        self.channel.start_consuming()

    def consume_data(self, data):
        if type(data) == bytes:
            data = str(data, 'utf8')
        self.receive_queue.put(data)
        # print('consumed data')
