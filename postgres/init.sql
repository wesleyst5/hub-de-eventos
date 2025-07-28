CREATE TABLE IF NOT EXISTS billing (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    mensagens INTEGER NOT NULL,
    bytes INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    event_time TIMESTAMP NOT NULL
);
