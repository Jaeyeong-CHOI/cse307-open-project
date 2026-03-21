#!/usr/bin/env python3
"""Shared run_context validation helpers for summary/snapshot payloads."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from run_context_schema import ALLOWED_EVENT_NAMES

SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")
RUN_ID_PATTERN = re.compile(r"^\d+$")
REPOSITORY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")
REF_PATTERN = re.compile(r"^refs/(heads|tags|pull)/.+$")
ACTOR_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
RUN_CONTEXT_TEXT_MAX_LEN = 128
ALLOWED_RUN_CONTEXT_KEYS = {
    "run_id",
    "run_url",
    "run_attempt",
    "event_name",
    "event_name_source",
    "repository",
    "sha",
    "ref",
    "workflow",
    "job",
    "actor",
}
GITHUB_RUN_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<repository>[^/\s]+/[^/\s]+)/actions/runs/(?P<run_id>\d+)(?:/attempts/(?P<attempt>\d+))?/?$"
)


def validate_run_context(
    payload: dict[str, Any],
    path: Path,
    errors: list[str],
    *,
    run_url_label: str = "run_context.run_url",
    run_url_suffix: str = " when present",
    actor_error_pattern_label: str = "pattern '^[A-Za-z0-9-]+$'",
) -> None:
    run_context = payload.get("run_context")
    if run_context is None:
        return
    if not isinstance(run_context, dict):
        errors.append(f"{path}: run_context must be an object when present")
        return

    unknown_keys = sorted(set(run_context.keys()) - ALLOWED_RUN_CONTEXT_KEYS)
    if unknown_keys:
        errors.append(
            f"{path}: run_context contains unknown key(s): {', '.join(unknown_keys)}"
        )

    for key in sorted(ALLOWED_RUN_CONTEXT_KEYS):
        if key in run_context and (
            not isinstance(run_context.get(key), str) or not run_context.get(key).strip()
        ):
            errors.append(f"{path}: run_context.{key} must be a non-empty string when present")

    run_id = run_context.get("run_id")
    run_url = run_context.get("run_url")
    has_run_id = isinstance(run_id, str) and bool(run_id.strip())
    has_run_url = isinstance(run_url, str) and bool(run_url.strip())

    if has_run_id != has_run_url:
        errors.append(f"{path}: run_context.run_id and run_context.run_url must be provided together")

    parsed_run_url = None
    if has_run_url:
        parsed_run_url = GITHUB_RUN_URL_PATTERN.match(str(run_url).strip())
        if not parsed_run_url:
            errors.append(
                f"{path}: {run_url_label} must match 'https://github.com/<owner>/<repo>/actions/runs/<run_id>[/attempts/<n>]{run_url_suffix}'"
            )

    if has_run_id and not RUN_ID_PATTERN.match(str(run_id).strip()):
        errors.append(f"{path}: run_context.run_id must be a numeric string when present")

    if has_run_id and parsed_run_url:
        parsed_run_id = parsed_run_url.group("run_id")
        if str(run_id).strip() != parsed_run_id:
            errors.append(f"{path}: run_context.run_url run_id segment must equal run_context.run_id")

    run_attempt = run_context.get("run_attempt")
    has_run_attempt = isinstance(run_attempt, str) and bool(run_attempt.strip())
    if has_run_attempt and not str(run_attempt).strip().isdigit():
        errors.append(f"{path}: run_context.run_attempt must be a numeric string when present")

    if parsed_run_url:
        parsed_attempt = parsed_run_url.group("attempt")
        if parsed_attempt and not has_run_attempt:
            errors.append(
                f"{path}: run_context.run_attempt must be provided when run_context.run_url contains '/attempts/<n>'"
            )
        if has_run_attempt and not parsed_attempt:
            errors.append(
                f"{path}: run_context.run_url must include '/attempts/<n>' when run_context.run_attempt is provided"
            )
        if parsed_attempt and has_run_attempt and str(run_attempt).strip() != parsed_attempt:
            errors.append(
                f"{path}: run_context.run_url attempt segment must equal run_context.run_attempt"
            )

    repository = run_context.get("repository")
    if isinstance(repository, str) and repository.strip() and not REPOSITORY_PATTERN.match(repository.strip()):
        errors.append(f"{path}: run_context.repository must match '<owner>/<repo>' when present")
    if parsed_run_url and isinstance(repository, str) and repository.strip():
        parsed_repository = parsed_run_url.group("repository")
        if repository.strip() != parsed_repository:
            errors.append(
                f"{path}: run_context.repository must match run_context.run_url repository segment"
            )

    sha = run_context.get("sha")
    if isinstance(sha, str) and sha.strip() and not SHA_PATTERN.match(sha.strip()):
        errors.append(f"{path}: run_context.sha must be a 7~40 hex string when present")

    ref = run_context.get("ref")
    if isinstance(ref, str) and ref.strip() and not REF_PATTERN.match(ref.strip()):
        errors.append(
            f"{path}: run_context.ref must match 'refs/heads/*', 'refs/tags/*', or 'refs/pull/*' when present"
        )

    event_name = run_context.get("event_name")
    if isinstance(event_name, str) and event_name.strip() and event_name.strip() not in ALLOWED_EVENT_NAMES:
        errors.append(
            f"{path}: run_context.event_name must be one of {sorted(ALLOWED_EVENT_NAMES)} when present"
        )

    event_name_source = run_context.get("event_name_source")
    if isinstance(event_name_source, str) and event_name_source.strip() and event_name_source.strip() not in {"provided", "derived"}:
        errors.append(
            f"{path}: run_context.event_name_source must be one of ['derived', 'provided'] when present"
        )
    if isinstance(event_name_source, str) and event_name_source.strip() and not (
        isinstance(event_name, str) and event_name.strip()
    ):
        errors.append(
            f"{path}: run_context.event_name_source requires run_context.event_name when present"
        )
    if isinstance(event_name, str) and event_name.strip() and not (
        isinstance(event_name_source, str) and event_name_source.strip()
    ):
        errors.append(
            f"{path}: run_context.event_name_source is required when run_context.event_name is present"
        )

    for key in ["workflow", "job"]:
        value = run_context.get(key)
        if isinstance(value, str) and value.strip() and len(value.strip()) > RUN_CONTEXT_TEXT_MAX_LEN:
            errors.append(
                f"{path}: run_context.{key} length must be <= {RUN_CONTEXT_TEXT_MAX_LEN} when present"
            )

    actor = run_context.get("actor")
    if isinstance(actor, str) and actor.strip() and not ACTOR_PATTERN.match(actor.strip()):
        errors.append(
            f"{path}: run_context.actor must match {actor_error_pattern_label} when present"
        )
