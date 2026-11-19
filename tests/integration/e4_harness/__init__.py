"""Test-only edge adapter for the E4 PostgreSQL functions.

The write logic lives in `migration/participant_data/001_assessment.sql`.
This package stands in for the future Edge Function: it parses bytes, rejects
duplicate keys, computes RFC 8785 digests and maps SQLSTATEs to error codes.
"""
