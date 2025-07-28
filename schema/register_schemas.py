import requests
import os

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

schemas = {
    "tenant1.topic1": {
        "type": "record",
        "name": "ExampleRecord",
        "fields": [
            {"name": "field1", "type": "string"},
            {"name": "field2", "type": "int"}
        ]
    }
}

def register_schemas():
    for subject, schema in schemas.items():
        url = f"{SCHEMA_REGISTRY_URL}/subjects/{subject}/versions"
        payload = {"schema": str(schema).replace("'", '"')}
        r = requests.post(url, json=payload)
        print(f"Registered schema for {subject}: {r.status_code}")

if __name__ == "__main__":
    register_schemas()
