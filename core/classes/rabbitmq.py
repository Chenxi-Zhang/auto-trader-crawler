from ..util.rabbitmq import (
    connect_to,
)

def open_mq_connection(ip, port=None):
    return MQbase(ip, port)

class MQbase(object):
    def __init__(self, ip, port=None):
        self.ip = ip
        self.port = port
        self.conn = None

    def __enter__(self):
        if not self.port:
            self.conn = connect_to(self.ip)
        else:
            self.conn = connect_to(self.ip, self.port)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
