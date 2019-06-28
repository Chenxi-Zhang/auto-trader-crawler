import pika

URL_QUEUE_NAME = 'url-queue'
DATA_QUEUE_NAME = 'data-queue'

def connect_to(ip_addr, port=None, credentials=None):
    '''
    Default rabbitmq connection port is 5672
    '''
    if not credentials:
        credentials = pika.PlainCredentials('test', 'test')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        ip_addr,
        port,
        '/',
        credentials=credentials,
        heartbeat=5))
    return connection

def send(channel, msg, router, exchange=''):
    channel.basic_publish(
        exchange=exchange,
        routing_key=router,
        body=msg
    )
