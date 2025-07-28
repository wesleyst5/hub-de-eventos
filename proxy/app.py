from flask import Flask, request, jsonify
import jwt
from auth import authenticate_request
from kafka_client import KafkaClient
from billing import BillingManager
import os
from datetime import datetime, timedelta
import json
from confluent_kafka import Consumer, TopicPartition

app = Flask(__name__)

kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
billing = BillingManager()
kafka_client = KafkaClient(kafka_bootstrap, schema_registry_url)

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # token válido por 1 hora

@app.route("/token", methods=["POST"])
def get_token():
    data = request.json
    user = data.get("user")
    tenant = data.get("tenant")
    if not user or not tenant:
        return jsonify({"error": "user and tenant are required"}), 400

    payload = {
        "user": user,
        "tenant": tenant,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return jsonify({"token": token})

@app.route("/produce", methods=["POST"])
def produce():
    user = authenticate_request(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    tenant = user.get("tenant")
    client_id = data.get("client_id")
    topic = f"{tenant}.{data.get('topic')}"
    message = data.get("message")
    if not topic or not message or not client_id:
        return jsonify({"error": "Missing topic, message or client_id"}), 400

    try:
        kafka_client.produce(topic, message)
        message_json = json.dumps(message)
        message_bytes = len(message_json.encode('utf-8'))
        billing.register_produce(tenant, topic, client_id, mensagens=1, bytes_=message_bytes)
        return jsonify({"status": "Message produced"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/consume", methods=["GET"])
def consume():
    user = authenticate_request(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    tenant = user.get("tenant")
    client_id = request.args.get("client_id")
    topic = request.args.get("topic")
    start_offset = request.args.get("start_offset", type=int)
    start_time_str = request.args.get("start_time")

    if not topic or not client_id:
        return jsonify({"error": "Missing topic or client_id"}), 400

    topic_full = f"{tenant}.{topic}"

    start_timestamp = None
    if start_time_str:
        try:
            dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            start_timestamp = int(dt.timestamp() * 1000)  # Kafka usa timestamp em ms
        except Exception:
            return jsonify({"error": "Invalid start_time format. Use ISO8601"}), 400

    try:
        # Criação direta do consumidor Kafka usando confluent_kafka
        consumer = Consumer({
            "bootstrap.servers": kafka_bootstrap,
            "group.id": f"{tenant}_{client_id}",
            "auto.offset.reset": "earliest",
            "enable.partition.eof": True
        })

        consumer.subscribe([topic_full])
        consumer.poll(1.0)  # força a obtenção das partições
        partitions = consumer.assignment()

        if start_offset is not None:
            for p in partitions:
                consumer.seek(TopicPartition(topic_full, p.partition, start_offset))
        elif start_timestamp is not None:
            offsets_for_times = [TopicPartition(topic_full, p.partition, start_timestamp) for p in partitions]
            offsets = consumer.offsets_for_times(offsets_for_times, timeout=10.0)
            for tp in offsets:
                if tp.offset != -1:
                    consumer.seek(tp)
                else:
                    consumer.seek(TopicPartition(topic_full, tp.partition, 0))
        else:
            consumer.subscribe([topic_full])

        messages = []
        timeout = 5.0  # segundos
        start = datetime.utcnow().timestamp()

        while datetime.utcnow().timestamp() - start < timeout:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                continue  # pode ser fim da partição
            try:
                messages.append(json.loads(msg.value().decode('utf-8')))
            except Exception:
                continue  # ignora mensagens inválidas

        consumer.close()

        total_messages = len(messages)
        total_bytes = sum(len(json.dumps(m).encode('utf-8')) for m in messages)

        billing.register_consume(tenant, client_id, topic_full,
                                 mensagens=total_messages, bytes_=total_bytes)

        return jsonify({"messages": messages})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
