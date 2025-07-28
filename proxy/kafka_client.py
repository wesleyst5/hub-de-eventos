from confluent_kafka import Producer, Consumer, KafkaException
import os
import json

class KafkaClient:
    def __init__(self, bootstrap_servers, schema_registry_url):
        self.bootstrap_servers = bootstrap_servers
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})
        self.consumer_config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'proxy-group',
            'auto.offset.reset': 'earliest'
        }

    def produce(self, topic, message):
        self.producer.produce(topic, json.dumps(message).encode("utf-8"))
        self.producer.flush()

    def consume(self, topic, timeout=5):
        consumer = Consumer(self.consumer_config)
        consumer.subscribe([topic])
        messages = []
        while True:
            msg = consumer.poll(timeout=timeout)
            if msg is None:
                break
            if msg.error():
                raise KafkaException(msg.error())
            messages.append(json.loads(msg.value().decode("utf-8")))
        consumer.close()
        return messages

    def create_consumer(self, client_id, topic):
        """
        Cria um consumidor Kafka para um client_id específico, sem usar group.id (para billing por consumidor).
        """
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': f"{client_id}-{topic}",  # Grupo único por client_id e tópico
            'enable.auto.commit': False,
            'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(config)
        return consumer
