-- PostgreSQL reference schema. The application creates the same tables through
-- SQLAlchemy metadata; this file is provided for database review and hand setup.
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(320) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'USER',
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE facilities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  type VARCHAR(32) NOT NULL,
  node INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_demo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE emergency_units (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  type VARCHAR(32) NOT NULL,
  current_node INTEGER NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'AVAILABLE',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_demo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE roads (
  id SERIAL PRIMARY KEY,
  source INTEGER NOT NULL,
  destination INTEGER NOT NULL,
  weight DOUBLE PRECISION NOT NULL CHECK (weight > 0),
  blocked BOOLEAN NOT NULL DEFAULT FALSE,
  is_demo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE emergencies (
  id SERIAL PRIMARY KEY,
  reporter_id INTEGER REFERENCES users(id),
  emergency_type VARCHAR(32) NOT NULL,
  location INTEGER NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'REPORTED',
  assigned_unit_id VARCHAR(64) REFERENCES emergency_units(id),
  facility_id INTEGER REFERENCES facilities(id),
  route JSONB,
  alternative_route JSONB,
  travel_cost DOUBLE PRECISION,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assignments (
  id SERIAL PRIMARY KEY,
  emergency_id INTEGER NOT NULL REFERENCES emergencies(id),
  unit_id VARCHAR(64) NOT NULL REFERENCES emergency_units(id),
  facility_id INTEGER REFERENCES facilities(id),
  route JSONB NOT NULL,
  travel_cost DOUBLE PRECISION NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE emergency_history (
  id SERIAL PRIMARY KEY,
  emergency_id INTEGER NOT NULL REFERENCES emergencies(id),
  old_status VARCHAR(32),
  new_status VARCHAR(32) NOT NULL,
  changed_by INTEGER REFERENCES users(id),
  note VARCHAR(500),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
