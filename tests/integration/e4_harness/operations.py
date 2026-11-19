"""Trusted study operations, called as assessment_operator."""

import json
from uuid import UUID

import psycopg

from .edge import connect, map_database_error


def _call(conninfo, sql, *params):
    try:
        with connect(conninfo, "assessment_operator") as connection:
            return connection.execute(sql, params).fetchone()[0]
    except psycopg.Error as error:
        mapped = map_database_error(error)
        if mapped is None:
            raise
        raise mapped from None


def assign_baseline(conninfo, enrollment, principal, protocol, sequence, window):
    return _call(
        conninfo,
        "SELECT assessment_api.assign_baseline(%s, %s, %s, %s, %s, %s)",
        enrollment,
        principal,
        protocol,
        sequence,
        *window,
    )


def allocate(conninfo, enrollment, arm, *, eligible, follow_up_windows):
    windows = {
        phase: [opens.isoformat(), closes.isoformat()]
        for phase, (opens, closes) in follow_up_windows.items()
    }
    created = _call(
        conninfo,
        "SELECT assessment_api.allocate(%s, %s, %s, %s::jsonb)",
        enrollment,
        arm,
        eligible,
        json.dumps(windows),
    )
    return {phase: UUID(visit) for phase, visit in created.items()}


def start_visit(conninfo, enrollment, visit, client_build):
    _call(
        conninfo,
        "SELECT assessment_api.start_visit(%s, %s, %s)",
        enrollment,
        visit,
        client_build,
    )


def mark_slot_presented(conninfo, enrollment, slot):
    _call(
        conninfo, "SELECT assessment_api.mark_slot_presented(%s, %s)", enrollment, slot
    )


def close_visit(conninfo, enrollment, visit, status):
    _call(
        conninfo,
        "SELECT assessment_api.close_visit(%s, %s, %s)",
        enrollment,
        visit,
        status,
    )


def withdraw(conninfo, enrollment):
    _call(conninfo, "SELECT assessment_api.withdraw(%s)", enrollment)
