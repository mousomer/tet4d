BEGIN;

CREATE SCHEMA assessment;
REVOKE ALL ON SCHEMA assessment FROM PUBLIC;
SET LOCAL search_path = assessment, pg_catalog;

CREATE TABLE protocol (
    ref text PRIMARY KEY,
    offline_grace_seconds integer NOT NULL CHECK (offline_grace_seconds >= 0)
);
CREATE TABLE item (
    ref text PRIMARY KEY,
    scorer text NOT NULL,
    presentation text NOT NULL,
    stimulus_sha256 bytea NOT NULL CHECK (octet_length(stimulus_sha256) = 32),
    exposure_identity text NOT NULL,
    UNIQUE (ref, scorer)
);
CREATE TABLE form (
    ref text PRIMARY KEY
);
CREATE TABLE form_item (
    form text REFERENCES form,
    ordinal integer CHECK (ordinal >= 0),
    item text NOT NULL REFERENCES item,
    PRIMARY KEY (form, ordinal),
    UNIQUE (form, ordinal, item)
);
CREATE TABLE protocol_visit (
    protocol text REFERENCES protocol,
    sequence text,
    phase text CHECK (phase IN ('baseline', 'posttest', 'retention')),
    form text NOT NULL REFERENCES form,
    PRIMARY KEY (protocol, sequence, phase),
    UNIQUE (protocol, sequence, phase, form)
);
CREATE TABLE protocol_arm (
    protocol text REFERENCES protocol,
    arm text,
    PRIMARY KEY (protocol, arm)
);
CREATE TABLE enrollment (
    id uuid PRIMARY KEY,
    protocol text NOT NULL REFERENCES protocol,
    sequence text NOT NULL,
    UNIQUE (id, protocol),
    UNIQUE (id, protocol, sequence)
);
CREATE TABLE enrollment_access (
    enrollment uuid PRIMARY KEY REFERENCES enrollment,
    principal uuid NOT NULL,
    revoked_at timestamptz
);
CREATE TABLE allocation (
    enrollment uuid PRIMARY KEY,
    protocol text NOT NULL,
    arm text NOT NULL,
    FOREIGN KEY (enrollment, protocol) REFERENCES enrollment (id, protocol),
    FOREIGN KEY (protocol, arm) REFERENCES protocol_arm
);
CREATE TABLE visit (
    id uuid PRIMARY KEY,
    enrollment uuid NOT NULL,
    protocol text NOT NULL,
    sequence text NOT NULL,
    phase text NOT NULL,
    form text NOT NULL,
    opens_at timestamptz NOT NULL,
    closes_at timestamptz NOT NULL CHECK (closes_at > opens_at),
    client_build text,
    started_at timestamptz,
    CHECK ((client_build IS NULL) = (started_at IS NULL)),
    UNIQUE (enrollment, phase),
    UNIQUE (id, form),
    FOREIGN KEY (enrollment, protocol, sequence) REFERENCES enrollment (id, protocol, sequence),
    FOREIGN KEY (protocol, sequence, phase, form) REFERENCES protocol_visit (protocol, sequence, phase, form)
);
CREATE TABLE slot (
    id uuid PRIMARY KEY,
    visit uuid NOT NULL,
    form text NOT NULL,
    ordinal integer NOT NULL,
    item text NOT NULL,
    scorer text NOT NULL,
    presented_at timestamptz,
    UNIQUE (visit, ordinal),
    FOREIGN KEY (visit, form) REFERENCES visit (id, form),
    FOREIGN KEY (form, ordinal, item) REFERENCES form_item (form, ordinal, item),
    FOREIGN KEY (item, scorer) REFERENCES item (ref, scorer)
);
CREATE TABLE attempt (
    id uuid PRIMARY KEY,
    slot uuid NOT NULL UNIQUE REFERENCES slot,
    x integer NOT NULL,
    y integer NOT NULL,
    z integer NOT NULL,
    w integer NOT NULL,
    latency_ms integer NOT NULL CHECK (latency_ms >= 0),
    UNIQUE (slot, id)
);
CREATE TABLE outcome (
    slot uuid PRIMARY KEY REFERENCES slot,
    status text NOT NULL CHECK (status IN ('submitted', 'invalid', 'interrupted', 'unpresented')),
    attempt uuid,
    observed_at timestamptz,
    timing text NOT NULL CHECK (timing IN ('unknown', 'before_window', 'in_window', 'after_window')),
    CHECK ((status = 'submitted') = (attempt IS NOT NULL)),
    CHECK ((observed_at IS NULL) = (timing = 'unknown')),
    CHECK (status <> 'unpresented' OR observed_at IS NULL),
    FOREIGN KEY (slot, attempt) REFERENCES attempt (slot, id)
);
CREATE TABLE visit_close (
    visit uuid PRIMARY KEY REFERENCES visit,
    status text NOT NULL CHECK (status IN ('completed', 'interrupted', 'expired')),
    closed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE exposure (
    enrollment uuid PRIMARY KEY REFERENCES allocation,
    activity text NOT NULL CHECK (activity IN ('rotation_3d', 'rotation_4d', 'none')),
    active_ms integer NOT NULL CHECK (active_ms >= 0),
    examples integer NOT NULL CHECK (examples >= 0),
    CHECK (activity <> 'none' OR (active_ms = 0 AND examples = 0))
);
CREATE TABLE receipt (
    enrollment uuid REFERENCES enrollment,
    command uuid,
    digest bytea NOT NULL CHECK (octet_length(digest) = 32),
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (enrollment, command)
);
REVOKE ALL ON ALL TABLES IN SCHEMA assessment FROM PUBLIC;

COMMIT;
