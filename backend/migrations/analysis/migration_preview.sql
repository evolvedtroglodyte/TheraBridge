INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> 7cce0565853d, create auth tables
-- Running upgrade  -> 7cce0565853d

CREATE TYPE userrole AS ENUM ('THERAPIST', 'PATIENT', 'ADMIN');

CREATE TYPE userrole AS ENUM ('THERAPIST', 'PATIENT', 'ADMIN');

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR NOT NULL, 
    hashed_password VARCHAR NOT NULL, 
    full_name VARCHAR NOT NULL, 
    role userrole NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE sessions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    refresh_token VARCHAR NOT NULL, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    is_revoked BOOLEAN DEFAULT 'false' NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

ALTER TABLE sessions ADD CONSTRAINT uq_sessions_refresh_token UNIQUE (refresh_token);

ALTER TABLE sessions ADD CONSTRAINT fk_sessions_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE;

INSERT INTO alembic_version (version_num) VALUES ('7cce0565853d') RETURNING alembic_version.version_num;

INFO  [alembic.runtime.migration] Running upgrade 7cce0565853d -> 808b6192c57c, Add authentication schema and missing user columns
-- Running upgrade 7cce0565853d -> 808b6192c57c

DROP INDEX idx_patient_triggers;

DROP TABLE patient_triggers;

DROP INDEX idx_patient_strategies;

DROP TABLE patient_strategies;

DROP INDEX idx_action_items_patient;

DROP TABLE action_items;

DROP INDEX idx_sessions_patient_date;

DROP INDEX idx_sessions_status;

DROP INDEX idx_sessions_therapist_date;

ALTER TABLE users ADD COLUMN full_name VARCHAR(255) NOT NULL;

ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL;

ALTER TABLE users ALTER COLUMN role TYPE userrole;

ALTER TABLE users DROP CONSTRAINT users_email_key;

CREATE UNIQUE INDEX ix_users_email ON users (email);

UPDATE alembic_version SET version_num='808b6192c57c' WHERE alembic_version.version_num = '7cce0565853d';

COMMIT;

