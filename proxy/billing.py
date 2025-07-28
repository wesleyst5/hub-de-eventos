import psycopg2
import os
from datetime import datetime

class BillingManager:
    def __init__(self):
        dsn = os.getenv("POSTGRES_DSN")
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True

    def register_produce(self, tenant, client_id, topic, mensagens, bytes_):
        self._register_event(tenant, client_id, topic, mensagens, bytes_, "produce")

    def register_consume(self, tenant, client_id, topic, mensagens, bytes_):
        self._register_event(tenant, client_id, topic, mensagens, bytes_, "consume")

    def _register_event(self, tenant, client_id, topic, mensagens, bytes_, action):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO billing (tenant, client_id, topic, mensagens, bytes, action, event_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (tenant, client_id, topic, mensagens, bytes_, action, datetime.utcnow())
            )
