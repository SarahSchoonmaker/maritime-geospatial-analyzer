-- db/schema.sql

CREATE TABLE ports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    country VARCHAR(100),
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TABLE vessels (
    id SERIAL PRIMARY KEY,
    imo_number VARCHAR(50),
    name VARCHAR(255),
    timestamp TIMESTAMP,
    latitude DECIMAL,
    longitude DECIMAL,
    speed_kn DECIMAL,
    destination VARCHAR(255),
    status VARCHAR(100)
);
