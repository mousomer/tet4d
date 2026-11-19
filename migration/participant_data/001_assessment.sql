-- E4 local assessment storage: synthetic data only.
--
-- Tables live in `assessment` (study records, readable by research_reader)
-- and `assessment_private` (the account link and its audit trail). Every write
-- goes through SECURITY DEFINER functions in `assessment_api`, owned by the
-- non-superuser role assessment_owner. Callers get EXECUTE, never table
-- privileges. Errors are raised with SQLSTATE class T4; the message text is the
-- stable error code. See docs/architecture/participant_data_platform.md.

BEGIN;

DO $roles$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY[
        'assessment_owner', 'assessment_ingest', 'assessment_operator', 'research_reader'
    ] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = role_name) THEN
            EXECUTE format('CREATE ROLE %I NOLOGIN', role_name);
        END IF;
    END LOOP;
END
$roles$;

CREATE SCHEMA assessment AUTHORIZATION assessment_owner;
CREATE SCHEMA assessment_private AUTHORIZATION assessment_owner;
CREATE SCHEMA assessment_api AUTHORIZATION assessment_owner;
REVOKE ALL ON SCHEMA assessment, assessment_private, assessment_api FROM PUBLIC;

SET LOCAL ROLE assessment_owner;
SET LOCAL search_path = pg_catalog;

-- Immutable manifests -------------------------------------------------------

CREATE TABLE assessment.protocol (
    ref text PRIMARY KEY,
    offline_grace_seconds integer NOT NULL CHECK (offline_grace_seconds >= 0)
);
CREATE TABLE assessment.item (
    ref text PRIMARY KEY,
    scorer text NOT NULL,
    presentation text NOT NULL,
    stimulus_sha256 bytea NOT NULL CHECK (octet_length(stimulus_sha256) = 32),
    exposure_identity text NOT NULL,
    UNIQUE (ref, scorer)
);
CREATE TABLE assessment.form (
    ref text PRIMARY KEY
);
CREATE TABLE assessment.form_item (
    form text REFERENCES assessment.form,
    ordinal integer CHECK (ordinal >= 0),
    item text NOT NULL REFERENCES assessment.item,
    PRIMARY KEY (form, ordinal),
    UNIQUE (form, ordinal, item)
);
CREATE TABLE assessment.protocol_visit (
    protocol text REFERENCES assessment.protocol,
    sequence text,
    phase text CHECK (phase IN ('baseline', 'posttest', 'retention')),
    form text NOT NULL REFERENCES assessment.form,
    PRIMARY KEY (protocol, sequence, phase),
    UNIQUE (protocol, sequence, phase, form)
);
CREATE TABLE assessment.protocol_arm (
    protocol text REFERENCES assessment.protocol,
    arm text,
    PRIMARY KEY (protocol, arm)
);
CREATE TABLE assessment.protocol_activity (
    protocol text REFERENCES assessment.protocol,
    activity text,
    PRIMARY KEY (protocol, activity)
);

-- Study records (pseudonymous: no principal or account identifier) --------

CREATE TABLE assessment.enrollment (
    id uuid PRIMARY KEY,
    protocol text NOT NULL REFERENCES assessment.protocol,
    sequence text NOT NULL,
    UNIQUE (id, protocol),
    UNIQUE (id, protocol, sequence)
);
CREATE TABLE assessment.withdrawal (
    enrollment uuid PRIMARY KEY REFERENCES assessment.enrollment,
    withdrawn_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE assessment.allocation (
    enrollment uuid PRIMARY KEY,
    protocol text NOT NULL,
    arm text NOT NULL,
    UNIQUE (enrollment, protocol),
    FOREIGN KEY (enrollment, protocol) REFERENCES assessment.enrollment (id, protocol),
    FOREIGN KEY (protocol, arm) REFERENCES assessment.protocol_arm
);
CREATE TABLE assessment.visit (
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
    FOREIGN KEY (enrollment, protocol, sequence)
        REFERENCES assessment.enrollment (id, protocol, sequence),
    FOREIGN KEY (protocol, sequence, phase, form)
        REFERENCES assessment.protocol_visit (protocol, sequence, phase, form)
);
CREATE TABLE assessment.slot (
    id uuid PRIMARY KEY,
    visit uuid NOT NULL,
    form text NOT NULL,
    ordinal integer NOT NULL,
    item text NOT NULL,
    scorer text NOT NULL,
    presented_at timestamptz,
    UNIQUE (visit, ordinal),
    FOREIGN KEY (visit, form) REFERENCES assessment.visit (id, form),
    FOREIGN KEY (form, ordinal, item) REFERENCES assessment.form_item (form, ordinal, item),
    FOREIGN KEY (item, scorer) REFERENCES assessment.item (ref, scorer)
);
CREATE TABLE assessment.attempt (
    id uuid PRIMARY KEY,
    slot uuid NOT NULL UNIQUE REFERENCES assessment.slot,
    x integer NOT NULL,
    y integer NOT NULL,
    z integer NOT NULL,
    w integer NOT NULL,
    latency_ms integer NOT NULL CHECK (latency_ms >= 0),
    UNIQUE (slot, id)
);
CREATE TABLE assessment.outcome (
    slot uuid PRIMARY KEY REFERENCES assessment.slot,
    status text NOT NULL CHECK (status IN ('submitted', 'invalid', 'interrupted', 'unpresented')),
    attempt uuid,
    observed_at timestamptz,
    timing text NOT NULL CHECK (timing IN ('unknown', 'before_window', 'in_window', 'after_window')),
    CHECK ((status = 'submitted') = (attempt IS NOT NULL)),
    CHECK ((observed_at IS NULL) = (timing = 'unknown')),
    CHECK (status <> 'unpresented' OR observed_at IS NULL),
    FOREIGN KEY (slot, attempt) REFERENCES assessment.attempt (slot, id)
);
CREATE TABLE assessment.visit_close (
    visit uuid PRIMARY KEY REFERENCES assessment.visit,
    status text NOT NULL CHECK (status IN ('completed', 'interrupted', 'expired', 'withdrawn')),
    closed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE assessment.exposure (
    enrollment uuid PRIMARY KEY,
    protocol text NOT NULL,
    activity text NOT NULL,
    active_ms integer NOT NULL CHECK (active_ms >= 0),
    examples integer NOT NULL CHECK (examples >= 0),
    CHECK (activity <> 'none' OR (active_ms = 0 AND examples = 0)),
    FOREIGN KEY (enrollment, protocol) REFERENCES assessment.allocation (enrollment, protocol),
    FOREIGN KEY (protocol, activity) REFERENCES assessment.protocol_activity
);
CREATE TABLE assessment.receipt (
    enrollment uuid REFERENCES assessment.enrollment,
    command uuid,
    digest bytea NOT NULL CHECK (octet_length(digest) = 32),
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (enrollment, command)
);

-- Account link: reachable only by the owner and its definer functions -----

CREATE TABLE assessment_private.enrollment_access (
    enrollment uuid PRIMARY KEY REFERENCES assessment.enrollment,
    principal uuid NOT NULL,
    granted_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz
);
CREATE TABLE assessment_private.access_audit (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment uuid NOT NULL REFERENCES assessment.enrollment,
    principal uuid NOT NULL,
    action text NOT NULL CHECK (action IN ('grant', 'revoke')),
    at timestamptz NOT NULL DEFAULT clock_timestamp()
);

-- Private helpers ----------------------------------------------------------

CREATE FUNCTION assessment_private.fail(p_code text) RETURNS void
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
    state text := CASE p_code
        WHEN 'invalid_payload' THEN 'T4001'
        WHEN 'unsupported_version' THEN 'T4002'
        WHEN 'authorization_failure' THEN 'T4003'
        WHEN 'missing_dependency' THEN 'T4004'
        WHEN 'conflict' THEN 'T4005'
        WHEN 'visit_closed' THEN 'T4006'
        WHEN 'reconciliation_pending' THEN 'T4007'
        WHEN 'ineligible_baseline' THEN 'T4008'
        WHEN 'incomplete_visit' THEN 'T4009'
        WHEN 'invalid_expiry' THEN 'T4010'
        WHEN 'invalid_status' THEN 'T4011'
        WHEN 'invalid_manifest' THEN 'T4012'
        WHEN 'invalid_windows' THEN 'T4013'
        WHEN 'visit_not_started' THEN 'T4014'
    END;
BEGIN
    IF state IS NULL THEN
        RAISE EXCEPTION 'unknown error code %', p_code;
    END IF;
    RAISE EXCEPTION USING ERRCODE = state, MESSAGE = p_code;
END
$$;

CREATE FUNCTION assessment_private.lock_enrollment(p_enrollment uuid) RETURNS boolean
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    PERFORM 1 FROM assessment.enrollment WHERE id = p_enrollment FOR UPDATE;
    RETURN FOUND;
END
$$;

-- Collection (ingest, start, present, allocate) needs live access and no
-- withdrawal. Bookkeeping (closing visits) needs only the enrollment.
CREATE FUNCTION assessment_private.require_collection(p_enrollment uuid, p_principal uuid)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    IF NOT assessment_private.lock_enrollment(p_enrollment) THEN
        PERFORM assessment_private.fail(
            CASE WHEN p_principal IS NULL THEN 'missing_dependency' ELSE 'authorization_failure' END);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM assessment_private.enrollment_access
        WHERE enrollment = p_enrollment AND revoked_at IS NULL
          AND (p_principal IS NULL OR principal = p_principal)
    ) OR EXISTS (SELECT 1 FROM assessment.withdrawal WHERE enrollment = p_enrollment) THEN
        PERFORM assessment_private.fail('authorization_failure');
    END IF;
END
$$;

CREATE FUNCTION assessment_private.uuid_field(p_record jsonb, p_field text) RETURNS uuid
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog AS $$
DECLARE
    value text;
BEGIN
    IF jsonb_typeof(p_record -> p_field) IS DISTINCT FROM 'string' THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    value := p_record ->> p_field;
    IF value !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    RETURN value::uuid;
END
$$;

CREATE FUNCTION assessment_private.int_field(p_value jsonb, p_minimum bigint) RETURNS integer
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog AS $$
BEGIN
    IF jsonb_typeof(p_value) IS DISTINCT FROM 'number'
       OR p_value::text !~ '^-?[0-9]{1,10}$'
       OR p_value::text::bigint NOT BETWEEN p_minimum AND 2147483647 THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    RETURN p_value::text::integer;
END
$$;

-- Canonical wire form only: YYYY-MM-DDTHH:MM:SS.sssZ, or JSON null.
CREATE FUNCTION assessment_private.observed_at(p_record jsonb) RETURNS timestamptz
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog AS $$
BEGIN
    IF jsonb_typeof(p_record -> 'observed_at') = 'null' THEN
        RETURN NULL;
    END IF;
    IF jsonb_typeof(p_record -> 'observed_at') IS DISTINCT FROM 'string'
       OR (p_record ->> 'observed_at') !~ '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$' THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    RETURN (p_record ->> 'observed_at')::timestamptz;
END
$$;

CREATE FUNCTION assessment_private.create_visit(
    p_enrollment uuid, p_phase text, p_opens timestamptz, p_closes timestamptz
) RETURNS uuid LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
    new_visit uuid := gen_random_uuid();
    visit_form text;
    ordinals integer[];
BEGIN
    IF p_opens IS NULL OR p_closes IS NULL OR p_closes <= p_opens THEN
        PERFORM assessment_private.fail('invalid_windows');
    END IF;
    INSERT INTO assessment.visit (id, enrollment, protocol, sequence, phase, form, opens_at, closes_at)
    SELECT new_visit, e.id, e.protocol, e.sequence, p.phase, p.form, p_opens, p_closes
    FROM assessment.enrollment e
    JOIN assessment.protocol_visit p ON (p.protocol, p.sequence) = (e.protocol, e.sequence)
    WHERE e.id = p_enrollment AND p.phase = p_phase
    RETURNING form INTO visit_form;
    IF visit_form IS NULL THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    SELECT array_agg(ordinal ORDER BY ordinal) INTO ordinals
    FROM assessment.form_item WHERE form = visit_form;
    IF ordinals IS NULL OR ordinals <> ARRAY(SELECT generate_series(0, cardinality(ordinals) - 1)) THEN
        PERFORM assessment_private.fail('invalid_manifest');
    END IF;
    INSERT INTO assessment.slot (id, visit, form, ordinal, item, scorer)
    SELECT gen_random_uuid(), new_visit, f.form, f.ordinal, f.item, i.scorer
    FROM assessment.form_item f JOIN assessment.item i ON i.ref = f.item
    WHERE f.form = visit_form;
    RETURN new_visit;
END
$$;

-- Resolve every slot still without an outcome when a visit is closed.
CREATE FUNCTION assessment_private.fill_open_slots(p_visit uuid) RETURNS void
LANGUAGE sql SET search_path = pg_catalog AS $$
    INSERT INTO assessment.outcome (slot, status, timing)
    SELECT s.id, CASE WHEN s.presented_at IS NULL THEN 'unpresented' ELSE 'interrupted' END, 'unknown'
    FROM assessment.slot s
    WHERE s.visit = p_visit
      AND NOT EXISTS (SELECT 1 FROM assessment.outcome o WHERE o.slot = s.id);
$$;

CREATE FUNCTION assessment_private.write_slot(p_enrollment uuid, p_command jsonb) RETURNS void
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
    target uuid := assessment_private.uuid_field(p_command, 'slot');
    observed timestamptz := assessment_private.observed_at(p_command);
    window_row record;
    new_attempt uuid;
    new_status text;
    response jsonb;
BEGIN
    SELECT v.opens_at, v.closes_at, v.started_at, s.presented_at,
           EXISTS (SELECT 1 FROM assessment.visit_close c WHERE c.visit = v.id) AS closed
    INTO window_row
    FROM assessment.slot s JOIN assessment.visit v ON v.id = s.visit
    WHERE s.id = target AND v.enrollment = p_enrollment;
    IF NOT FOUND THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    IF window_row.closed THEN
        PERFORM assessment_private.fail('visit_closed');
    END IF;
    IF window_row.started_at IS NULL THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;

    IF p_command ->> 'kind' = 'submit' THEN
        new_status := 'submitted';
        new_attempt := assessment_private.uuid_field(p_command, 'attempt');
        response := p_command -> 'response';
        IF jsonb_typeof(response) IS DISTINCT FROM 'array' OR jsonb_array_length(response) <> 4 THEN
            PERFORM assessment_private.fail('invalid_payload');
        END IF;
        INSERT INTO assessment.attempt (id, slot, x, y, z, w, latency_ms)
        VALUES (
            new_attempt, target,
            assessment_private.int_field(response -> 0, -2147483648),
            assessment_private.int_field(response -> 1, -2147483648),
            assessment_private.int_field(response -> 2, -2147483648),
            assessment_private.int_field(response -> 3, -2147483648),
            assessment_private.int_field(p_command -> 'latency_ms', 0)
        );
    ELSE
        new_status := p_command ->> 'status';
        IF new_status IS NULL OR new_status NOT IN ('invalid', 'interrupted', 'unpresented') THEN
            PERFORM assessment_private.fail('invalid_payload');
        END IF;
        IF new_status = 'unpresented' AND observed IS NOT NULL THEN
            PERFORM assessment_private.fail('invalid_payload');
        END IF;
        IF new_status = 'unpresented' AND window_row.presented_at IS NOT NULL THEN
            PERFORM assessment_private.fail('conflict');
        END IF;
    END IF;

    INSERT INTO assessment.outcome (slot, status, attempt, observed_at, timing)
    VALUES (
        target, new_status, new_attempt, observed,
        CASE
            WHEN observed IS NULL THEN 'unknown'
            WHEN observed < window_row.opens_at THEN 'before_window'
            WHEN observed >= window_row.closes_at THEN 'after_window'
            ELSE 'in_window'
        END
    );
END
$$;

CREATE FUNCTION assessment_private.write_exposure(p_enrollment uuid, p_command jsonb) RETURNS void
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
    allocated_protocol text;
    reported_activity text := p_command ->> 'activity';
BEGIN
    SELECT protocol INTO allocated_protocol FROM assessment.allocation WHERE enrollment = p_enrollment;
    IF NOT FOUND THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    IF jsonb_typeof(p_command -> 'activity') IS DISTINCT FROM 'string' OR NOT EXISTS (
        SELECT 1 FROM assessment.protocol_activity a
        WHERE a.protocol = allocated_protocol AND a.activity = reported_activity
    ) THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    INSERT INTO assessment.exposure (enrollment, protocol, activity, active_ms, examples)
    VALUES (
        p_enrollment, allocated_protocol, reported_activity,
        assessment_private.int_field(p_command -> 'active_ms', 0),
        assessment_private.int_field(p_command -> 'examples', 0)
    );
EXCEPTION WHEN check_violation THEN
    PERFORM assessment_private.fail('invalid_payload');
END
$$;

-- Public entry points -------------------------------------------------------

-- p_commands: the adapter's validated command array. p_digests: the adapter's
-- SHA-256 of each command's RFC 8785 form, in the same order. jsonb cannot
-- detect duplicate keys or produce RFC 8785, so both happen before this call.
CREATE FUNCTION assessment_api.ingest(
    p_principal uuid, p_enrollment uuid, p_commands jsonb, p_digests bytea[]
) RETURNS TABLE (command uuid, digest bytea, received_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    idx integer;
    entry jsonb;
    entry_digest bytea;
    prior record;
BEGIN
    IF p_principal IS NULL OR p_enrollment IS NULL
       OR jsonb_typeof(p_commands) IS DISTINCT FROM 'array'
       OR jsonb_array_length(p_commands) NOT BETWEEN 1 AND 64
       OR p_digests IS NULL OR cardinality(p_digests) <> jsonb_array_length(p_commands) THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    PERFORM assessment_private.require_collection(p_enrollment, p_principal);

    FOR idx IN 0 .. jsonb_array_length(p_commands) - 1 LOOP
        entry := p_commands -> idx;
        entry_digest := p_digests[idx + 1];
        IF jsonb_typeof(entry) IS DISTINCT FROM 'object'
           OR entry_digest IS NULL OR octet_length(entry_digest) <> 32 THEN
            PERFORM assessment_private.fail('invalid_payload');
        END IF;
        command := assessment_private.uuid_field(entry, 'id');

        SELECT r.digest, r.received_at INTO prior
        FROM assessment.receipt r
        WHERE r.enrollment = p_enrollment AND r.command = ingest.command;
        IF FOUND THEN
            IF prior.digest <> entry_digest THEN
                PERFORM assessment_private.fail('conflict');
            END IF;
            digest := prior.digest;
            received_at := prior.received_at;
            RETURN NEXT;
            CONTINUE;
        END IF;

        CASE entry ->> 'kind'
            WHEN 'submit', 'outcome' THEN
                PERFORM assessment_private.write_slot(p_enrollment, entry);
            WHEN 'exposure' THEN
                PERFORM assessment_private.write_exposure(p_enrollment, entry);
            ELSE
                PERFORM assessment_private.fail('invalid_payload');
        END CASE;

        INSERT INTO assessment.receipt AS r (enrollment, command, digest)
        VALUES (p_enrollment, ingest.command, entry_digest)
        RETURNING r.digest, r.received_at INTO digest, received_at;
        RETURN NEXT;
    END LOOP;
EXCEPTION WHEN integrity_constraint_violation THEN
    PERFORM assessment_private.fail('conflict');
END
$$;

CREATE FUNCTION assessment_api.assign_baseline(
    p_enrollment uuid, p_principal uuid, p_protocol text, p_sequence text,
    p_opens timestamptz, p_closes timestamptz
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
BEGIN
    IF p_enrollment IS NULL OR p_principal IS NULL THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    INSERT INTO assessment.enrollment (id, protocol, sequence)
    VALUES (p_enrollment, p_protocol, p_sequence);
    INSERT INTO assessment_private.enrollment_access (enrollment, principal)
    VALUES (p_enrollment, p_principal);
    INSERT INTO assessment_private.access_audit (enrollment, principal, action)
    VALUES (p_enrollment, p_principal, 'grant');
    RETURN assessment_private.create_visit(p_enrollment, 'baseline', p_opens, p_closes);
EXCEPTION WHEN integrity_constraint_violation THEN
    PERFORM assessment_private.fail('conflict');
END
$$;

-- p_windows: {"<phase>": ["<opens>", "<closes>"], ...} for every follow-up phase.
CREATE FUNCTION assessment_api.allocate(
    p_enrollment uuid, p_arm text, p_eligible boolean, p_windows jsonb
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    enrolled_protocol text;
    phases text[];
    phase_name text;
    created jsonb := '{}';
BEGIN
    PERFORM assessment_private.require_collection(p_enrollment, NULL);
    SELECT e.protocol INTO enrolled_protocol
    FROM assessment.enrollment e
    JOIN assessment.visit v ON v.enrollment = e.id AND v.phase = 'baseline'
    JOIN assessment.visit_close c ON c.visit = v.id AND c.status = 'completed'
    WHERE e.id = p_enrollment;
    IF enrolled_protocol IS NULL OR p_eligible IS NOT TRUE THEN
        PERFORM assessment_private.fail('ineligible_baseline');
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM assessment.protocol_arm WHERE protocol = enrolled_protocol AND arm = p_arm
    ) THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    SELECT coalesce(array_agg(p.phase ORDER BY p.phase), '{}') INTO phases
    FROM assessment.enrollment e
    JOIN assessment.protocol_visit p ON (p.protocol, p.sequence) = (e.protocol, e.sequence)
    WHERE e.id = p_enrollment AND p.phase <> 'baseline';
    IF jsonb_typeof(p_windows) IS DISTINCT FROM 'object'
       OR phases <> ARRAY(SELECT jsonb_object_keys(p_windows) ORDER BY 1) THEN
        PERFORM assessment_private.fail('invalid_windows');
    END IF;
    INSERT INTO assessment.allocation (enrollment, protocol, arm)
    VALUES (p_enrollment, enrolled_protocol, p_arm);
    FOREACH phase_name IN ARRAY phases LOOP
        IF jsonb_typeof(p_windows -> phase_name) IS DISTINCT FROM 'array'
           OR jsonb_array_length(p_windows -> phase_name) <> 2 THEN
            PERFORM assessment_private.fail('invalid_windows');
        END IF;
        created := created || jsonb_build_object(
            phase_name,
            assessment_private.create_visit(
                p_enrollment, phase_name,
                (p_windows -> phase_name ->> 0)::timestamptz,
                (p_windows -> phase_name ->> 1)::timestamptz
            )
        );
    END LOOP;
    RETURN created;
EXCEPTION
    WHEN integrity_constraint_violation THEN
        PERFORM assessment_private.fail('conflict');
    WHEN invalid_datetime_format OR datetime_field_overflow THEN
        PERFORM assessment_private.fail('invalid_windows');
END
$$;

CREATE FUNCTION assessment_api.start_visit(
    p_enrollment uuid, p_visit uuid, p_client_build text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
BEGIN
    PERFORM assessment_private.require_collection(p_enrollment, NULL);
    IF p_client_build IS NULL OR p_client_build = '' THEN
        PERFORM assessment_private.fail('invalid_payload');
    END IF;
    UPDATE assessment.visit v
    SET client_build = p_client_build, started_at = clock_timestamp()
    WHERE v.id = p_visit AND v.enrollment = p_enrollment AND v.started_at IS NULL
      AND NOT EXISTS (SELECT 1 FROM assessment.visit_close c WHERE c.visit = v.id);
    IF NOT FOUND THEN
        PERFORM assessment_private.fail('conflict');
    END IF;
END
$$;

CREATE FUNCTION assessment_api.mark_slot_presented(p_enrollment uuid, p_slot uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
BEGIN
    PERFORM assessment_private.require_collection(p_enrollment, NULL);
    UPDATE assessment.slot s
    SET presented_at = coalesce(s.presented_at, clock_timestamp())
    FROM assessment.visit v
    WHERE s.id = p_slot AND s.visit = v.id AND v.enrollment = p_enrollment
      AND v.started_at IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM assessment.visit_close c WHERE c.visit = v.id)
      AND NOT EXISTS (SELECT 1 FROM assessment.outcome o WHERE o.slot = s.id);
    IF NOT FOUND THEN
        PERFORM assessment_private.fail('conflict');
    END IF;
END
$$;

CREATE FUNCTION assessment_api.close_visit(p_enrollment uuid, p_visit uuid, p_status text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    state record;
BEGIN
    IF NOT assessment_private.lock_enrollment(p_enrollment) THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    IF p_status IS NULL OR p_status NOT IN ('completed', 'interrupted', 'expired') THEN
        PERFORM assessment_private.fail('invalid_status');
    END IF;
    SELECT v.started_at IS NOT NULL AS started,
           clock_timestamp() >= v.closes_at + make_interval(secs => p.offline_grace_seconds)
               AS grace_elapsed,
           (SELECT c.status FROM assessment.visit_close c WHERE c.visit = v.id) AS closed_status,
           EXISTS (SELECT 1 FROM assessment.slot s
                   WHERE s.visit = v.id AND s.presented_at IS NOT NULL) AS any_presented,
           NOT EXISTS (SELECT 1 FROM assessment.slot s
                       LEFT JOIN assessment.outcome o ON o.slot = s.id
                       WHERE s.visit = v.id AND o.slot IS NULL) AS all_resolved,
           NOT EXISTS (SELECT 1 FROM assessment.slot s
                       LEFT JOIN assessment.outcome o ON o.slot = s.id
                       WHERE s.visit = v.id
                         AND (o.status IS NULL OR o.status NOT IN ('submitted', 'invalid')))
               AS all_answered,
           NOT EXISTS (SELECT 1 FROM assessment.slot s
                       JOIN assessment.outcome o ON o.slot = s.id
                       WHERE s.visit = v.id AND o.status <> 'unpresented') AS none_answered
    INTO state
    FROM assessment.visit v JOIN assessment.protocol p ON p.ref = v.protocol
    WHERE v.id = p_visit AND v.enrollment = p_enrollment;
    IF NOT FOUND THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    IF state.closed_status IS NOT NULL THEN
        IF state.closed_status <> p_status THEN
            PERFORM assessment_private.fail('conflict');
        END IF;
        RETURN;
    END IF;

    IF p_status = 'completed' THEN
        IF NOT state.started OR NOT state.all_answered THEN
            PERFORM assessment_private.fail('incomplete_visit');
        END IF;
    ELSIF p_status = 'expired' THEN
        -- Expiry means nothing was ever shown; once a slot was presented the
        -- visit can only close as interrupted.
        IF state.any_presented OR NOT state.none_answered OR NOT state.grace_elapsed THEN
            PERFORM assessment_private.fail('invalid_expiry');
        END IF;
    ELSE
        IF NOT state.started THEN
            PERFORM assessment_private.fail('visit_not_started');
        END IF;
        -- Queued outcomes may still arrive until the offline grace period ends.
        IF NOT state.all_resolved AND NOT state.grace_elapsed THEN
            PERFORM assessment_private.fail('reconciliation_pending');
        END IF;
    END IF;
    PERFORM assessment_private.fill_open_slots(p_visit);
    INSERT INTO assessment.visit_close (visit, status) VALUES (p_visit, p_status);
END
$$;

-- Withdrawal stops collection at once, including offline reconciliation, and
-- closes every open visit as withdrawn so attrition stays reconstructible
-- from the study schema alone.
CREATE FUNCTION assessment_api.withdraw(p_enrollment uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    open_visit uuid;
BEGIN
    IF NOT assessment_private.lock_enrollment(p_enrollment) THEN
        PERFORM assessment_private.fail('missing_dependency');
    END IF;
    IF EXISTS (SELECT 1 FROM assessment.withdrawal WHERE enrollment = p_enrollment) THEN
        RETURN;
    END IF;
    INSERT INTO assessment.withdrawal (enrollment) VALUES (p_enrollment);
    WITH revoked AS (
        UPDATE assessment_private.enrollment_access
        SET revoked_at = clock_timestamp()
        WHERE enrollment = p_enrollment AND revoked_at IS NULL
        RETURNING enrollment, principal
    )
    INSERT INTO assessment_private.access_audit (enrollment, principal, action)
    SELECT enrollment, principal, 'revoke' FROM revoked;
    FOR open_visit IN
        SELECT v.id FROM assessment.visit v
        WHERE v.enrollment = p_enrollment
          AND NOT EXISTS (SELECT 1 FROM assessment.visit_close c WHERE c.visit = v.id)
        ORDER BY v.opens_at
    LOOP
        PERFORM assessment_private.fill_open_slots(open_visit);
        INSERT INTO assessment.visit_close (visit, status) VALUES (open_visit, 'withdrawn');
    END LOOP;
END
$$;

-- Privileges ----------------------------------------------------------------

REVOKE ALL ON ALL TABLES IN SCHEMA assessment, assessment_private FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA assessment_private, assessment_api FROM PUBLIC;

GRANT USAGE ON SCHEMA assessment TO research_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA assessment TO research_reader;

GRANT USAGE ON SCHEMA assessment_api TO assessment_ingest, assessment_operator;
GRANT EXECUTE ON FUNCTION assessment_api.ingest(uuid, uuid, jsonb, bytea[]) TO assessment_ingest;
GRANT EXECUTE ON FUNCTION
    assessment_api.assign_baseline(uuid, uuid, text, text, timestamptz, timestamptz),
    assessment_api.allocate(uuid, text, boolean, jsonb),
    assessment_api.start_visit(uuid, uuid, text),
    assessment_api.mark_slot_presented(uuid, uuid),
    assessment_api.close_visit(uuid, uuid, text),
    assessment_api.withdraw(uuid)
TO assessment_operator;

COMMIT;
