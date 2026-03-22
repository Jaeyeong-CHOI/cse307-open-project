#!/usr/bin/env python3
"""Build a deterministic batch-evaluation run plan from a task set.

This is an offline planning utility (no model/API calls).
It exists to keep evaluation batches cheap-first and avoid redundant calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from error_utils import emit_error


DEFAULT_PRESET_FILE = Path(__file__).resolve().parent.parent / "examples" / "batch-plan-presets.v1.json"
PRESET_SUMMARY_TSV_BASE_COLUMNS = [
    "preset",
    "models",
    "prompt_conditions",
    "repeats",
    "cheap_first",
    "fair_model_allocation",
    "max_total_runs",
    "max_total_runs_mode",
    "max_runs_per_model",
    "max_runs_per_prompt_condition",
    "max_runs_per_task",
    "max_runs_per_task_model",
    "max_runs_per_task_prompt_condition",
    "tags",
    "description_length",
]
PRESET_SUMMARY_TSV_SCHEMA = "planner_preset_summary_tsv.v2"
PRESET_SUMMARY_TSV_SCHEMA_PATTERN = re.compile(r"^planner_preset_summary_tsv\.v[1-9][0-9]*$")
PRESET_LIST_TEXT_META_SCHEMA = "planner_preset_list_meta.v1"
PRESET_LIST_TEXT_META_SCHEMA_PATTERN = re.compile(r"^planner_preset_list_meta\.v[1-9][0-9]*$")
PRESET_SHOW_TEXT_META_SCHEMA = "planner_preset_show_meta.v1"
PRESET_SHOW_TEXT_META_SCHEMA_PATTERN = re.compile(r"^planner_preset_show_meta\.v[1-9][0-9]*$")
PRESET_TEXT_META_JSON_SCHEMA_VERSION = "v1"
PRESET_TEXT_META_JSON_SCHEMA_VERSION_PATTERN = re.compile(r"^v[1-9][0-9]*$")
SORT_ALIASES_TSV_META_SCHEMA = "planner_sort_aliases_tsv_meta.v1"
SORT_ALIASES_TSV_META_JSON_SCHEMA_VERSION = "v1"
SORT_ALIASES_TSV_META_JSON_SCHEMA_VERSION_PATTERN = re.compile(r"^v[1-9][0-9]*$")
SORT_ALIASES_OUTPUT_SHAPE_SCHEMA = "planner_sort_alias_output_shape.v1"
PRESET_OUTPUT_SHAPE_SCHEMA = "planner_preset_output_shape.v1"


PRESET_SORT_ALIAS_MAP: dict[str, str] = {
    "total-cap": "max-total-runs",
    "total-cap-desc": "max-total-runs-desc",
    "per-model-cap": "max-runs-per-model",
    "per-model-cap-desc": "max-runs-per-model-desc",
    "per-prompt-cap": "max-runs-per-prompt-condition",
    "per-prompt-cap-desc": "max-runs-per-prompt-condition-desc",
    "per-condition-cap": "max-runs-per-prompt-condition",
    "per-condition-cap-desc": "max-runs-per-prompt-condition-desc",
    "per-task-cap": "max-runs-per-task",
    "per-task-cap-desc": "max-runs-per-task-desc",
    "task-cap": "max-runs-per-task",
    "task-cap-desc": "max-runs-per-task-desc",
    "per-task-model-cap": "max-runs-per-task-model",
    "per-task-model-cap-desc": "max-runs-per-task-model-desc",
    "task-model-cap": "max-runs-per-task-model",
    "task-model-cap-desc": "max-runs-per-task-model-desc",
    "per-task-prompt-cap": "max-runs-per-task-prompt-condition",
    "per-task-prompt-cap-desc": "max-runs-per-task-prompt-condition-desc",
    "per-task-condition-cap": "max-runs-per-task-prompt-condition",
    "per-task-condition-cap-desc": "max-runs-per-task-prompt-condition-desc",
    "task-prompt-cap": "max-runs-per-task-prompt-condition",
    "task-prompt-cap-desc": "max-runs-per-task-prompt-condition-desc",
    "task-condition-cap": "max-runs-per-task-prompt-condition",
    "task-condition-cap-desc": "max-runs-per-task-prompt-condition-desc",
    "cheap-first": "cheap-first-tag",
    "cheap-first-desc": "cheap-first-tag-desc",
    "cheap-total-cap": "cheap-first-total-cap",
    "cheap-total-cap-desc": "cheap-first-total-cap-desc",
    "fair-total-cap": "fair-allocation-total-cap",
    "fair-total-cap-desc": "fair-allocation-total-cap-desc",
    "fair-cap": "fair-allocation-total-cap",
    "fair-cap-desc": "fair-allocation-total-cap-desc",
    "cost": "cost-priority",
    "cost-desc": "cost-priority-desc",
    "cost-prompt": "cost-priority-prompt",
    "cost-prompt-desc": "cost-priority-prompt-desc",
    "cost-condition": "cost-priority-prompt",
    "cost-condition-desc": "cost-priority-prompt-desc",
    "cc": "cost-priority-prompt",
    "ccd": "cost-priority-prompt-desc",
    "fair-allocation": "fair-model-allocation",
    "fair-allocation-desc": "fair-model-allocation-desc",
}

LIST_SORT_ALIASES_SORT_ALIAS_MAP: dict[str, str] = {
    "skew": "group-share-delta-abs-desc",
    "skew-desc": "group-share-delta-abs-desc",
    "skew-asc": "group-share-delta-abs",
    "skew-share": "group-share-delta-abs-desc",
    "skew-share-desc": "group-share-delta-abs-desc",
    "skew-share-asc": "group-share-delta-abs",
    "skew-count": "group-size-delta-abs-desc",
    "skew-count-desc": "group-size-delta-abs-desc",
    "skew-count-asc": "group-size-delta-abs",
    "skew-size": "group-size-delta-abs-desc",
    "skew-size-desc": "group-size-delta-abs-desc",
    "skew-size-asc": "group-size-delta-abs",
    "skew-pct": "group-size-delta-pct-abs-desc",
    "skew-pct-desc": "group-size-delta-pct-abs-desc",
    "skew-pct-asc": "group-size-delta-pct-abs",
    "skew-size-pct": "group-size-delta-pct-abs-desc",
    "skew-size-pct-desc": "group-size-delta-pct-abs-desc",
    "skew-size-pct-asc": "group-size-delta-pct-abs",
}


FILTER_MODE_ALIAS_MAP: dict[str, str] = {
    "c": "contains",
    "p": "prefix",
    "e": "exact",
}

MATCH_FIELD_ALIAS_MAP: dict[str, str] = {
    "b": "both",
    "a": "alias",
    "c": "canonical",
}

TAG_MATCH_MODE_ALIAS_MAP: dict[str, str] = {
    "a": "all",
    "o": "any",
}

LIST_SORT_ALIASES_FORMAT_ALIAS_MAP: dict[str, str] = {
    "aj": "aliases-json",
    "gj": "grouped-json",
    "at": "aliases-tsv",
    "gt": "grouped-tsv",
    "atr": "aliases-tsv-rows",
    "gtr": "grouped-tsv-rows",
    "n": "names",
    "cn": "canonical-names",
    "nj": "names-json",
    "cnj": "canonical-names-json",
}


def _resolve_filter_mode(mode: str) -> str:
    return FILTER_MODE_ALIAS_MAP.get(mode, mode)


def _resolve_match_field(match_field: str) -> str:
    return MATCH_FIELD_ALIAS_MAP.get(match_field, match_field)


def _resolve_tag_match_mode(match_mode: str) -> str:
    return TAG_MATCH_MODE_ALIAS_MAP.get(match_mode, match_mode)


def _resolve_list_sort_aliases_sort(sort_mode: str) -> str:
    return LIST_SORT_ALIASES_SORT_ALIAS_MAP.get(sort_mode, sort_mode)


def _resolve_list_sort_aliases_format(output_format: str) -> str:
    return LIST_SORT_ALIASES_FORMAT_ALIAS_MAP.get(output_format, output_format)


def _normalize_sort_alias_name_filter_value(value: str | None, *, case_sensitive: bool) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not case_sensitive:
        normalized = normalized.lower()
    return normalized


def _describe_list_sort_aliases_sort_mode(sort_mode: str) -> dict[str, Any]:
    descending = sort_mode.endswith("-desc")
    sort_key = sort_mode[: -len("-desc")] if descending else sort_mode
    return {
        "sort_family": "builtin",
        "sort_key": sort_key,
        "sort_direction": "desc" if descending else "asc",
        "sort_is_desc": descending,
    }


def _resolve_list_presets_sort_mode(sort_mode: str) -> str:
    if sort_mode.startswith("t:"):
        return f"tag:{sort_mode[len('t:') :]}"
    return sort_mode


def _describe_list_presets_sort_mode(sort_mode: str) -> dict[str, Any]:
    descending = sort_mode.endswith("-desc")
    if sort_mode.startswith("tag:"):
        tag = sort_mode[len("tag:") :]
        if descending:
            tag = tag[: -len("-desc")]
        return {
            "sort_family": "tag",
            "sort_tag": tag,
            "sort_direction": "desc" if descending else "asc",
            "sort_is_desc": descending,
        }
    return {
        "sort_family": "builtin",
        "sort_tag": None,
        "sort_direction": "desc" if descending else "asc",
        "sort_is_desc": descending,
    }


def _build_sort_alias_groups(alias_map: dict[str, str] | None = None) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    source_map = PRESET_SORT_ALIAS_MAP if alias_map is None else alias_map
    for alias, canonical in source_map.items():
        groups.setdefault(canonical, []).append(alias)
    for aliases in groups.values():
        aliases.sort()
    return dict(sorted(groups.items(), key=lambda item: item[0]))


def _compute_group_sizes_and_share_pct(alias_map: dict[str, str]) -> tuple[dict[str, int], int, dict[str, float]]:
    group_sizes: dict[str, int] = {}
    for canonical in alias_map.values():
        group_sizes[canonical] = group_sizes.get(canonical, 0) + 1

    total_aliases = sum(group_sizes.values())
    group_share_pct = {
        canonical: (0.0 if total_aliases == 0 else round((count / total_aliases) * 100.0, 2))
        for canonical, count in group_sizes.items()
    }
    return group_sizes, total_aliases, group_share_pct


def _format_sort_aliases_tsv(
    alias_map: dict[str, str],
    *,
    global_group_share_pct: dict[str, float] | None = None,
    global_group_sizes: dict[str, int] | None = None,
    include_header: bool = True,
) -> str:
    group_sizes, _, group_share_pct = _compute_group_sizes_and_share_pct(alias_map)

    lines: list[str] = []
    if include_header:
        lines.append(
            "alias\tcanonical\tcanonical_group_count\tcanonical_group_count_global\tcanonical_group_share_pct\tcanonical_group_share_pct_global"
        )
    for alias, canonical in alias_map.items():
        global_count = 0 if global_group_sizes is None else global_group_sizes.get(canonical, 0)
        global_share = 0.0 if global_group_share_pct is None else global_group_share_pct.get(canonical, 0.0)
        lines.append(
            f"{alias}\t{canonical}\t{group_sizes[canonical]}\t{global_count}\t{group_share_pct[canonical]:.2f}\t{global_share:.2f}"
        )
    return "\n".join(lines)


def _format_sort_alias_groups_tsv(
    groups: dict[str, list[str]],
    *,
    global_group_share_pct: dict[str, float] | None = None,
    global_group_sizes: dict[str, int] | None = None,
    include_header: bool = True,
) -> str:
    total_aliases = sum(len(aliases) for aliases in groups.values())
    lines: list[str] = []
    if include_header:
        lines.append(
            "canonical\talias_count\talias_count_global\talias_share_pct\talias_share_pct_global\taliases"
        )
    for canonical, aliases in groups.items():
        alias_count = len(aliases)
        global_count = 0 if global_group_sizes is None else global_group_sizes.get(canonical, 0)
        alias_share_pct = 0.0 if total_aliases == 0 else round((alias_count / total_aliases) * 100.0, 2)
        global_share = 0.0 if global_group_share_pct is None else global_group_share_pct.get(canonical, 0.0)
        lines.append(
            f"{canonical}\t{alias_count}\t{global_count}\t{alias_share_pct:.2f}\t{global_share:.2f}\t{','.join(aliases)}"
        )
    return "\n".join(lines)




def _resolve_sort_aliases_output_transport(output_format: str) -> str:
    if output_format.endswith("-json"):
        return "json"
    if output_format.endswith("-tsv") or output_format.endswith("-tsv-rows"):
        return "tsv"
    return "text"


def _resolve_sort_aliases_output_is_rows(output_format: str) -> bool:
    return output_format.endswith("-rows")


def _resolve_sort_aliases_output_has_header(output_format: str) -> bool:
    return _resolve_sort_aliases_output_transport(output_format) == "tsv" and not _resolve_sort_aliases_output_is_rows(
        output_format
    )


def _resolve_sort_aliases_output_delimiter(output_format: str) -> str:
    transport = _resolve_sort_aliases_output_transport(output_format)
    if transport == "tsv":
        return "tab"
    if transport == "text":
        return "newline"
    return "none"


def _resolve_sort_aliases_output_field_count(output_format: str) -> int:
    transport = _resolve_sort_aliases_output_transport(output_format)
    if transport == "json":
        return 0

    output_kind = _resolve_sort_aliases_output_kind(output_format)
    if output_kind in {"aliases", "grouped"}:
        return 6
    if output_kind in {"names", "canonical-names"}:
        return 1
    return 0


def _resolve_sort_aliases_output_column_count(output_format: str) -> int:
    return len(_resolve_sort_aliases_output_columns(output_format))


def _resolve_sort_aliases_output_kind(output_format: str) -> str:
    if output_format in {"aliases-json", "aliases-tsv", "aliases-tsv-rows"}:
        return "aliases"
    if output_format in {"grouped-json", "grouped-tsv", "grouped-tsv-rows"}:
        return "grouped"
    if output_format in {"names", "names-json"}:
        return "names"
    if output_format in {"canonical-names", "canonical-names-json"}:
        return "canonical-names"
    return output_format


def _resolve_sort_aliases_output_columns(output_format: str) -> list[str]:
    output_kind = _resolve_sort_aliases_output_kind(output_format)
    if output_kind == "aliases":
        return [
            "alias",
            "canonical",
            "canonical_group_count",
            "canonical_group_count_global",
            "canonical_group_share_pct",
            "canonical_group_share_pct_global",
        ]
    if output_kind == "grouped":
        return [
            "canonical",
            "alias_count",
            "alias_count_global",
            "alias_share_pct",
            "alias_share_pct_global",
            "aliases",
        ]
    if output_kind == "names":
        return ["name"]
    if output_kind == "canonical-names":
        return ["canonical_name"]
    return []


def _resolve_sort_aliases_output_columns_sha256(output_format: str) -> str:
    columns = _resolve_sort_aliases_output_columns(output_format)
    payload = "\n".join(columns)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_sort_aliases_output_shape_schema(output_format: str) -> str:
    _ = output_format
    return SORT_ALIASES_OUTPUT_SHAPE_SCHEMA


def _resolve_sort_aliases_output_shape_fields(output_format: str) -> list[str]:
    _ = output_format
    return [
        "output",
        "output_transport",
        "output_is_rows",
        "output_has_header",
        "output_delimiter",
        "output_field_count",
        "output_column_count",
        "output_columns",
    ]


def _resolve_sort_aliases_output_shape_tuple(output_format: str) -> str:
    output_columns = _resolve_sort_aliases_output_columns(output_format)
    return (
        f"output={_resolve_sort_aliases_output_kind(output_format)}|"
        f"output_transport={_resolve_sort_aliases_output_transport(output_format)}|"
        f"output_is_rows={str(_resolve_sort_aliases_output_is_rows(output_format)).lower()}|"
        f"output_has_header={str(_resolve_sort_aliases_output_has_header(output_format)).lower()}|"
        f"output_delimiter={_resolve_sort_aliases_output_delimiter(output_format)}|"
        f"output_field_count={_resolve_sort_aliases_output_field_count(output_format)}|"
        f"output_column_count={_resolve_sort_aliases_output_column_count(output_format)}|"
        f"output_columns={','.join(output_columns) if output_columns else 'none'}"
    )


def _resolve_sort_aliases_output_shape_payload(output_format: str) -> dict[str, str | bool | int | list[str]]:
    return {
        "output": _resolve_sort_aliases_output_kind(output_format),
        "output_transport": _resolve_sort_aliases_output_transport(output_format),
        "output_is_rows": _resolve_sort_aliases_output_is_rows(output_format),
        "output_has_header": _resolve_sort_aliases_output_has_header(output_format),
        "output_delimiter": _resolve_sort_aliases_output_delimiter(output_format),
        "output_field_count": _resolve_sort_aliases_output_field_count(output_format),
        "output_column_count": _resolve_sort_aliases_output_column_count(output_format),
        "output_columns": _resolve_sort_aliases_output_columns(output_format),
    }


def _resolve_sort_aliases_output_shape_payload_json(output_format: str) -> str:
    return json.dumps(
        _resolve_sort_aliases_output_shape_payload(output_format),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _resolve_sort_aliases_output_shape_sha256(output_format: str) -> str:
    payload = _resolve_sort_aliases_output_shape_payload_json(output_format)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_sort_aliases_output_shape_payload_json_sha256(output_format: str) -> str:
    payload = _resolve_sort_aliases_output_shape_payload_json(output_format)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_sort_aliases_output_shape_payload_json_bytes(output_format: str) -> int:
    payload = _resolve_sort_aliases_output_shape_payload_json(output_format)
    return len(payload.encode("utf-8"))


def _resolve_sort_aliases_output_shape_tuple_bytes(output_format: str) -> int:
    payload = _resolve_sort_aliases_output_shape_tuple(output_format)
    return len(payload.encode("utf-8"))


def _resolve_sort_aliases_output_shape_payload_json_sha256_algo(output_format: str) -> str:
    _ = output_format
    return "sha256"


def _resolve_sort_aliases_output_shape_sha256_algo(output_format: str) -> str:
    _ = output_format
    return "sha256"


def _format_sort_aliases_tsv_meta(
    *,
    output_format: str,
    output_format_requested: str,
    output_format_alias_resolved: bool,
    filtered_count: int,
    emitted_count: int,
    truncated: bool,
    name_contains: str | None,
    name_not_contains: str | None,
    name_values: list[str],
    name_not_values: list[str],
    filter_mode: str,
    filter_mode_requested: str,
    filter_mode_alias_resolved: bool,
    name_not_filter_mode: str,
    name_not_filter_mode_requested: str,
    name_not_filter_mode_alias_resolved: bool,
    match_field: str,
    match_field_requested: str,
    match_field_alias_resolved: bool,
    case_sensitive: bool,
    limit: int | None,
    sort_mode: str,
    sort_requested: str,
    sort_alias_resolved: bool,
    sort_family: str,
    sort_key: str,
    sort_direction: str,
    sort_is_desc: bool,
    group_count: int,
    min_group_size: int,
    max_group_size: int | None,
    min_group_size_global: int,
    max_group_size_global: int | None,
    min_group_share_pct_global: float,
    max_group_share_pct_global: float,
    min_group_share_pct: float,
    max_group_share_pct: float,
    min_group_share_delta_pct: float,
    max_group_share_delta_pct: float,
    min_group_share_delta_abs_pct: float,
    max_group_share_delta_abs_pct: float,
    min_group_size_delta: int,
    max_group_size_delta: int,
    min_group_size_delta_abs: int,
    max_group_size_delta_abs: int,
    min_group_size_delta_pct: float,
    max_group_size_delta_pct: float,
    min_group_size_delta_abs_pct: float,
    max_group_size_delta_abs_pct: float,
    meta_format: str = "text",
    json_schema_version: str = SORT_ALIASES_TSV_META_JSON_SCHEMA_VERSION,
) -> str:
    output = _resolve_sort_aliases_output_kind(output_format)
    output_transport = _resolve_sort_aliases_output_transport(output_format)
    output_is_rows = _resolve_sort_aliases_output_is_rows(output_format)
    output_has_header = _resolve_sort_aliases_output_has_header(output_format)
    output_delimiter = _resolve_sort_aliases_output_delimiter(output_format)
    output_field_count = _resolve_sort_aliases_output_field_count(output_format)
    output_columns = _resolve_sort_aliases_output_columns(output_format)
    output_column_count = _resolve_sort_aliases_output_column_count(output_format)
    output_columns_sha256 = _resolve_sort_aliases_output_columns_sha256(output_format)
    output_shape_schema = _resolve_sort_aliases_output_shape_schema(output_format)
    output_shape_fields = _resolve_sort_aliases_output_shape_fields(output_format)
    output_shape_tuple = _resolve_sort_aliases_output_shape_tuple(output_format)
    output_shape_sha256 = _resolve_sort_aliases_output_shape_sha256(output_format)
    output_shape_sha256_algo = _resolve_sort_aliases_output_shape_sha256_algo(output_format)

    if meta_format == "json":
        return json.dumps(
            {
                "meta": True,
                "schema_version": json_schema_version,
                "schema": SORT_ALIASES_TSV_META_SCHEMA,
                "output": output,
                "output_transport": output_transport,
                "output_is_rows": output_is_rows,
                "output_has_header": output_has_header,
                "output_delimiter": output_delimiter,
                "output_field_count": output_field_count,
                "output_column_count": output_column_count,
                "output_columns": output_columns,
                "output_columns_sha256": output_columns_sha256,
                "output_shape_schema": output_shape_schema,
                "output_shape_fields": output_shape_fields,
                "output_shape_payload": _resolve_sort_aliases_output_shape_payload(output_format),
                "output_shape_payload_json": _resolve_sort_aliases_output_shape_payload_json(output_format),
                "output_shape_payload_json_bytes": _resolve_sort_aliases_output_shape_payload_json_bytes(output_format),
                "output_shape_payload_json_sha256": _resolve_sort_aliases_output_shape_payload_json_sha256(output_format),
                "output_shape_payload_json_sha256_algo": _resolve_sort_aliases_output_shape_payload_json_sha256_algo(output_format),
                "output_shape_tuple": output_shape_tuple,
                "output_shape_tuple_bytes": _resolve_sort_aliases_output_shape_tuple_bytes(output_format),
                "output_shape_sha256": output_shape_sha256,
                "output_shape_sha256_algo": output_shape_sha256_algo,
                "output_format": output_format,
                "output_format_requested": output_format_requested,
                "output_format_alias_resolved": output_format_alias_resolved,
                "filtered_count": filtered_count,
                "emitted_count": emitted_count,
                "output_record_count": emitted_count,
                "output_is_empty": emitted_count == 0,
                "output_is_single_record": emitted_count == 1,
                "output_has_multiple_records": emitted_count > 1,
                "truncated": truncated,
                "name_contains": name_contains,
                "name_not_contains": name_not_contains,
                "name_values": name_values,
                "name_not_values": name_not_values,
                "filter_mode": filter_mode,
                "filter_mode_requested": filter_mode_requested,
                "filter_mode_alias_resolved": filter_mode_alias_resolved,
                "name_not_filter_mode": name_not_filter_mode,
                "name_not_filter_mode_requested": name_not_filter_mode_requested,
                "name_not_filter_mode_alias_resolved": name_not_filter_mode_alias_resolved,
                "match_field": match_field,
                "match_field_requested": match_field_requested,
                "match_field_alias_resolved": match_field_alias_resolved,
                "case_sensitive": case_sensitive,
                "limit": limit,
                "sort": sort_mode,
                "sort_requested": sort_requested,
                "sort_alias_resolved": sort_alias_resolved,
                "sort_family": sort_family,
                "sort_key": sort_key,
                "sort_direction": sort_direction,
                "sort_is_desc": sort_is_desc,
                "group_count": group_count,
                "min_group_size": min_group_size,
                "max_group_size": max_group_size,
                "min_group_size_global": min_group_size_global,
                "max_group_size_global": max_group_size_global,
                "min_group_share_pct_global": min_group_share_pct_global,
                "max_group_share_pct_global": max_group_share_pct_global,
                "min_group_share_pct": min_group_share_pct,
                "max_group_share_pct": max_group_share_pct,
                "min_group_share_delta_pct": min_group_share_delta_pct,
                "max_group_share_delta_pct": max_group_share_delta_pct,
                "min_group_share_delta_abs_pct": min_group_share_delta_abs_pct,
                "max_group_share_delta_abs_pct": max_group_share_delta_abs_pct,
                "min_group_size_delta": min_group_size_delta,
                "max_group_size_delta": max_group_size_delta,
                "min_group_size_delta_abs": min_group_size_delta_abs,
                "max_group_size_delta_abs": max_group_size_delta_abs,
                "min_group_size_delta_pct": min_group_size_delta_pct,
                "max_group_size_delta_pct": max_group_size_delta_pct,
                "min_group_size_delta_abs_pct": min_group_size_delta_abs_pct,
                "max_group_size_delta_abs_pct": max_group_size_delta_abs_pct,
            },
            ensure_ascii=False,
        )
    return (
        "# meta\t"
        f"schema={SORT_ALIASES_TSV_META_SCHEMA}\t"
        f"output={output}\t"
        f"output_transport={output_transport}\t"
        f"output_is_rows={str(output_is_rows).lower()}\t"
        f"output_has_header={str(output_has_header).lower()}\t"
        f"output_delimiter={output_delimiter}\t"
        f"output_field_count={output_field_count}\t"
        f"output_column_count={output_column_count}\t"
        f"output_columns={','.join(output_columns) if output_columns else 'none'}\t"
        f"output_columns_sha256={output_columns_sha256}\t"
        f"output_shape_schema={output_shape_schema}\t"
        f"output_shape_fields={','.join(output_shape_fields) if output_shape_fields else 'none'}\t"
        f"output_shape_tuple={output_shape_tuple}\t"
        f"output_shape_tuple_bytes={_resolve_sort_aliases_output_shape_tuple_bytes(output_format)}\t"
        f"output_shape_sha256={output_shape_sha256}\t"
        f"output_shape_sha256_algo={output_shape_sha256_algo}\t"
        f"output_shape_payload_json_bytes={_resolve_sort_aliases_output_shape_payload_json_bytes(output_format)}\t"
        f"output_shape_payload_json_sha256={_resolve_sort_aliases_output_shape_payload_json_sha256(output_format)}\t"
        f"output_shape_payload_json_sha256_algo={_resolve_sort_aliases_output_shape_payload_json_sha256_algo(output_format)}\t"
        f"output_format={output_format}\t"
        f"output_format_requested={output_format_requested}\t"
        f"output_format_alias_resolved={str(output_format_alias_resolved).lower()}\t"
        f"filtered_count={filtered_count}\t"
        f"emitted_count={emitted_count}\t"
        f"output_record_count={emitted_count}\t"
        f"output_is_empty={str(emitted_count == 0).lower()}\t"
        f"output_is_single_record={str(emitted_count == 1).lower()}\t"
        f"output_has_multiple_records={str(emitted_count > 1).lower()}\t"
        f"truncated={str(truncated).lower()}\t"
        f"name_contains={name_contains or 'none'}\t"
        f"name_not_contains={name_not_contains or 'none'}\t"
        f"name_values={','.join(name_values) if name_values else 'none'}\t"
        f"name_not_values={','.join(name_not_values) if name_not_values else 'none'}\t"
        f"filter_mode={filter_mode}\t"
        f"filter_mode_requested={filter_mode_requested}\t"
        f"filter_mode_alias_resolved={str(filter_mode_alias_resolved).lower()}\t"
        f"name_not_filter_mode={name_not_filter_mode}\t"
        f"name_not_filter_mode_requested={name_not_filter_mode_requested}\t"
        f"name_not_filter_mode_alias_resolved={str(name_not_filter_mode_alias_resolved).lower()}\t"
        f"match_field={match_field}\t"
        f"match_field_requested={match_field_requested}\t"
        f"match_field_alias_resolved={str(match_field_alias_resolved).lower()}\t"
        f"case_sensitive={str(case_sensitive).lower()}\t"
        f"limit={limit if limit is not None else 'none'}\t"
        f"sort={sort_mode}\t"
        f"sort_requested={sort_requested}\t"
        f"sort_alias_resolved={str(sort_alias_resolved).lower()}\t"
        f"sort_family={sort_family}\t"
        f"sort_key={sort_key}\t"
        f"sort_direction={sort_direction}\t"
        f"sort_is_desc={str(sort_is_desc).lower()}\t"
        f"group_count={group_count}\t"
        f"min_group_size={min_group_size}\t"
        f"max_group_size={max_group_size if max_group_size is not None else 'none'}\t"
        f"min_group_size_global={min_group_size_global}\t"
        f"max_group_size_global={max_group_size_global if max_group_size_global is not None else 'none'}\t"
        f"min_group_share_pct_global={min_group_share_pct_global:.2f}\t"
        f"max_group_share_pct_global={max_group_share_pct_global:.2f}\t"
        f"min_group_share_pct={min_group_share_pct:.2f}\t"
        f"max_group_share_pct={max_group_share_pct:.2f}\t"
        f"min_group_share_delta_pct={min_group_share_delta_pct:.2f}\t"
        f"max_group_share_delta_pct={max_group_share_delta_pct:.2f}\t"
        f"min_group_share_delta_abs_pct={min_group_share_delta_abs_pct:.2f}\t"
        f"max_group_share_delta_abs_pct={max_group_share_delta_abs_pct:.2f}\t"
        f"min_group_size_delta={min_group_size_delta}\t"
        f"max_group_size_delta={max_group_size_delta}\t"
        f"min_group_size_delta_abs={min_group_size_delta_abs}\t"
        f"max_group_size_delta_abs={max_group_size_delta_abs}\t"
        f"min_group_size_delta_pct={min_group_size_delta_pct:.2f}\t"
        f"max_group_size_delta_pct={max_group_size_delta_pct:.2f}\t"
        f"min_group_size_delta_abs_pct={min_group_size_delta_abs_pct:.2f}\t"
        f"max_group_size_delta_abs_pct={max_group_size_delta_abs_pct:.2f}"
    )


def _filter_sort_alias_map(
    alias_name_contains: str | None,
    alias_name_not_contains: str | None,
    limit: int | None,
    sort_mode: str = "alias",
    filter_mode: str = "contains",
    name_not_filter_mode: str = "contains",
    match_field: str = "both",
    min_group_size: int = 1,
    max_group_size: int | None = None,
    min_group_size_global: int = 1,
    max_group_size_global: int | None = None,
    min_group_share_pct_global: float = 0.0,
    max_group_share_pct_global: float = 100.0,
    min_group_share_pct: float = 0.0,
    max_group_share_pct: float = 100.0,
    min_group_share_delta_pct: float = -100.0,
    max_group_share_delta_pct: float = 100.0,
    min_group_share_delta_abs_pct: float = 0.0,
    max_group_share_delta_abs_pct: float = 100.0,
    min_group_size_delta: int = -999_999,
    max_group_size_delta: int = 999_999,
    min_group_size_delta_abs: int = 0,
    max_group_size_delta_abs: int = 999_999,
    min_group_size_delta_pct: float = -100.0,
    max_group_size_delta_pct: float = 100.0,
    min_group_size_delta_abs_pct: float = 0.0,
    max_group_size_delta_abs_pct: float = 100.0,
    case_sensitive: bool = False,
) -> tuple[dict[str, str], int, bool]:
    normalized_filter = alias_name_contains.strip() if alias_name_contains is not None else None
    if normalized_filter is not None and not case_sensitive:
        normalized_filter = normalized_filter.lower()
    if alias_name_contains is not None and not normalized_filter:
        raise ValueError("--list-sort-aliases-name-contains must include at least one non-empty character")

    normalized_exclude_filter = alias_name_not_contains.strip() if alias_name_not_contains is not None else None
    if normalized_exclude_filter is not None and not case_sensitive:
        normalized_exclude_filter = normalized_exclude_filter.lower()
    if alias_name_not_contains is not None and not normalized_exclude_filter:
        raise ValueError("--list-sort-aliases-name-not-contains must include at least one non-empty character")
    if limit is not None and limit < 1:
        raise ValueError("--list-sort-aliases-limit must be >= 1")
    filter_mode = _resolve_filter_mode(filter_mode)
    name_not_filter_mode = _resolve_filter_mode(name_not_filter_mode)
    match_field = _resolve_match_field(match_field)
    if filter_mode not in {"contains", "prefix", "exact"}:
        raise ValueError(f"unsupported list-sort-aliases filter mode: {filter_mode}")
    if name_not_filter_mode not in {"contains", "prefix", "exact"}:
        raise ValueError(f"unsupported list-sort-aliases exclusion filter mode: {name_not_filter_mode}")
    if match_field not in {"both", "alias", "canonical"}:
        raise ValueError(f"unsupported list-sort-aliases match field: {match_field}")
    if min_group_size < 1:
        raise ValueError("--list-sort-aliases-min-group-size must be >= 1")
    if max_group_size is not None and max_group_size < 1:
        raise ValueError("--list-sort-aliases-max-group-size must be >= 1")
    if max_group_size is not None and max_group_size < min_group_size:
        raise ValueError("--list-sort-aliases-max-group-size must be >= --list-sort-aliases-min-group-size")
    if min_group_size_global < 1:
        raise ValueError("--list-sort-aliases-min-group-size-global must be >= 1")
    if max_group_size_global is not None and max_group_size_global < 1:
        raise ValueError("--list-sort-aliases-max-group-size-global must be >= 1")
    if max_group_size_global is not None and max_group_size_global < min_group_size_global:
        raise ValueError(
            "--list-sort-aliases-max-group-size-global must be >= --list-sort-aliases-min-group-size-global"
        )
    if not 0.0 <= min_group_share_pct_global <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-share-pct-global must be between 0 and 100")
    if not 0.0 <= max_group_share_pct_global <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-share-pct-global must be between 0 and 100")
    if max_group_share_pct_global < min_group_share_pct_global:
        raise ValueError(
            "--list-sort-aliases-max-group-share-pct-global must be >= --list-sort-aliases-min-group-share-pct-global"
        )
    if not 0.0 <= min_group_share_pct <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-share-pct must be between 0 and 100")
    if not 0.0 <= max_group_share_pct <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-share-pct must be between 0 and 100")
    if max_group_share_pct < min_group_share_pct:
        raise ValueError("--list-sort-aliases-max-group-share-pct must be >= --list-sort-aliases-min-group-share-pct")
    if not -100.0 <= min_group_share_delta_pct <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-share-delta-pct must be between -100 and 100")
    if not -100.0 <= max_group_share_delta_pct <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-share-delta-pct must be between -100 and 100")
    if max_group_share_delta_pct < min_group_share_delta_pct:
        raise ValueError(
            "--list-sort-aliases-max-group-share-delta-pct must be >= --list-sort-aliases-min-group-share-delta-pct"
        )
    if not 0.0 <= min_group_share_delta_abs_pct <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-share-delta-abs-pct must be between 0 and 100")
    if not 0.0 <= max_group_share_delta_abs_pct <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-share-delta-abs-pct must be between 0 and 100")
    if max_group_share_delta_abs_pct < min_group_share_delta_abs_pct:
        raise ValueError(
            "--list-sort-aliases-max-group-share-delta-abs-pct must be >= --list-sort-aliases-min-group-share-delta-abs-pct"
        )
    if max_group_size_delta < min_group_size_delta:
        raise ValueError(
            "--list-sort-aliases-max-group-size-delta must be >= --list-sort-aliases-min-group-size-delta"
        )
    if min_group_size_delta_abs < 0:
        raise ValueError("--list-sort-aliases-min-group-size-delta-abs must be >= 0")
    if max_group_size_delta_abs < 0:
        raise ValueError("--list-sort-aliases-max-group-size-delta-abs must be >= 0")
    if max_group_size_delta_abs < min_group_size_delta_abs:
        raise ValueError(
            "--list-sort-aliases-max-group-size-delta-abs must be >= --list-sort-aliases-min-group-size-delta-abs"
        )
    if not -100.0 <= min_group_size_delta_pct <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-size-delta-pct must be between -100 and 100")
    if not -100.0 <= max_group_size_delta_pct <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-size-delta-pct must be between -100 and 100")
    if max_group_size_delta_pct < min_group_size_delta_pct:
        raise ValueError(
            "--list-sort-aliases-max-group-size-delta-pct must be >= --list-sort-aliases-min-group-size-delta-pct"
        )
    if not 0.0 <= min_group_size_delta_abs_pct <= 100.0:
        raise ValueError("--list-sort-aliases-min-group-size-delta-abs-pct must be between 0 and 100")
    if not 0.0 <= max_group_size_delta_abs_pct <= 100.0:
        raise ValueError("--list-sort-aliases-max-group-size-delta-abs-pct must be between 0 and 100")
    if max_group_size_delta_abs_pct < min_group_size_delta_abs_pct:
        raise ValueError(
            "--list-sort-aliases-max-group-size-delta-abs-pct must be >= --list-sort-aliases-min-group-size-delta-abs-pct"
        )

    def _match_value(candidate: str) -> bool:
        if filter_mode == "contains":
            return normalized_filter in candidate
        if filter_mode == "prefix":
            return candidate.startswith(normalized_filter)
        return candidate == normalized_filter

    def _matches_filter(alias: str, canonical: str) -> bool:
        if not normalized_filter:
            return True
        alias_key = alias if case_sensitive else alias.lower()
        canonical_key = canonical if case_sensitive else canonical.lower()
        if match_field == "alias":
            return _match_value(alias_key)
        if match_field == "canonical":
            return _match_value(canonical_key)
        return _match_value(alias_key) or _match_value(canonical_key)

    def _matches_exclude_filter_value(candidate: str) -> bool:
        if name_not_filter_mode == "contains":
            return normalized_exclude_filter in candidate
        if name_not_filter_mode == "prefix":
            return candidate.startswith(normalized_exclude_filter)
        return candidate == normalized_exclude_filter

    def _matches_exclude_filter(alias: str, canonical: str) -> bool:
        if not normalized_exclude_filter:
            return False
        alias_key = alias if case_sensitive else alias.lower()
        canonical_key = canonical if case_sensitive else canonical.lower()
        if match_field == "alias":
            return _matches_exclude_filter_value(alias_key)
        if match_field == "canonical":
            return _matches_exclude_filter_value(canonical_key)
        return _matches_exclude_filter_value(alias_key) or _matches_exclude_filter_value(canonical_key)

    filtered_items: list[tuple[str, str]] = []
    for alias, canonical in PRESET_SORT_ALIAS_MAP.items():
        if not _matches_filter(alias, canonical):
            continue
        if _matches_exclude_filter(alias, canonical):
            continue
        filtered_items.append((alias, canonical))

    if min_group_size_global > 1 or max_group_size_global is not None:
        global_group_sizes, _, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)
        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if min_group_size_global <= global_group_sizes.get(canonical, 0)
            and (max_group_size_global is None or global_group_sizes.get(canonical, 0) <= max_group_size_global)
        ]

    if min_group_share_pct_global > 0.0 or max_group_share_pct_global < 100.0:
        global_group_sizes, global_alias_count, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)

        def _global_share_pct(canonical: str) -> float:
            if global_alias_count == 0:
                return 0.0
            return round((global_group_sizes.get(canonical, 0) / global_alias_count) * 100.0, 2)

        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if min_group_share_pct_global <= _global_share_pct(canonical) <= max_group_share_pct_global
        ]

    if min_group_size > 1 or max_group_size is not None:
        group_sizes_before_sort: dict[str, int] = {}
        for _, canonical in filtered_items:
            group_sizes_before_sort[canonical] = group_sizes_before_sort.get(canonical, 0) + 1

        def _group_size_ok(canonical: str) -> bool:
            size = group_sizes_before_sort[canonical]
            if size < min_group_size:
                return False
            if max_group_size is not None and size > max_group_size:
                return False
            return True

        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if _group_size_ok(canonical)
        ]

    if min_group_share_pct > 0.0 or max_group_share_pct < 100.0:
        local_group_sizes: dict[str, int] = {}
        for _, canonical in filtered_items:
            local_group_sizes[canonical] = local_group_sizes.get(canonical, 0) + 1
        local_alias_count = len(filtered_items)

        def _local_share_pct(canonical: str) -> float:
            if local_alias_count == 0:
                return 0.0
            return round((local_group_sizes.get(canonical, 0) / local_alias_count) * 100.0, 2)

        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if min_group_share_pct <= _local_share_pct(canonical) <= max_group_share_pct
        ]

    if (
        min_group_share_delta_pct > -100.0
        or max_group_share_delta_pct < 100.0
        or min_group_share_delta_abs_pct > 0.0
        or max_group_share_delta_abs_pct < 100.0
    ):
        local_group_sizes: dict[str, int] = {}
        for _, canonical in filtered_items:
            local_group_sizes[canonical] = local_group_sizes.get(canonical, 0) + 1
        local_alias_count = len(filtered_items)
        global_group_sizes, global_alias_count, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)

        def _local_share_pct(canonical: str) -> float:
            if local_alias_count == 0:
                return 0.0
            return round((local_group_sizes.get(canonical, 0) / local_alias_count) * 100.0, 2)

        def _global_share_pct(canonical: str) -> float:
            if global_alias_count == 0:
                return 0.0
            return round((global_group_sizes.get(canonical, 0) / global_alias_count) * 100.0, 2)

        def _share_delta_pct(canonical: str) -> float:
            return round(_local_share_pct(canonical) - _global_share_pct(canonical), 2)

        def _share_delta_abs_pct(canonical: str) -> float:
            return round(abs(_share_delta_pct(canonical)), 2)

        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if min_group_share_delta_pct <= _share_delta_pct(canonical) <= max_group_share_delta_pct
            and min_group_share_delta_abs_pct <= _share_delta_abs_pct(canonical) <= max_group_share_delta_abs_pct
        ]

    if (
        min_group_size_delta > -999_999
        or max_group_size_delta < 999_999
        or min_group_size_delta_abs > 0
        or max_group_size_delta_abs < 999_999
        or min_group_size_delta_pct > -100.0
        or max_group_size_delta_pct < 100.0
        or min_group_size_delta_abs_pct > 0.0
        or max_group_size_delta_abs_pct < 100.0
    ):
        local_group_sizes: dict[str, int] = {}
        for _, canonical in filtered_items:
            local_group_sizes[canonical] = local_group_sizes.get(canonical, 0) + 1
        global_group_sizes, _, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)

        def _size_delta(canonical: str) -> int:
            return local_group_sizes.get(canonical, 0) - global_group_sizes.get(canonical, 0)

        def _size_delta_abs(canonical: str) -> int:
            return abs(_size_delta(canonical))

        def _size_delta_pct(canonical: str) -> float:
            global_size = global_group_sizes.get(canonical, 0)
            if global_size == 0:
                return 0.0
            return round((_size_delta(canonical) / global_size) * 100.0, 2)

        def _size_delta_abs_pct(canonical: str) -> float:
            return round(abs(_size_delta_pct(canonical)), 2)

        filtered_items = [
            (alias, canonical)
            for alias, canonical in filtered_items
            if min_group_size_delta <= _size_delta(canonical) <= max_group_size_delta
            and min_group_size_delta_abs <= _size_delta_abs(canonical) <= max_group_size_delta_abs
            and min_group_size_delta_pct <= _size_delta_pct(canonical) <= max_group_size_delta_pct
            and min_group_size_delta_abs_pct <= _size_delta_abs_pct(canonical) <= max_group_size_delta_abs_pct
        ]

    if sort_mode == "alias":
        filtered_items.sort(key=lambda item: item[0])
    elif sort_mode == "alias-desc":
        filtered_items.sort(key=lambda item: item[0], reverse=True)
    elif sort_mode == "canonical":
        filtered_items.sort(key=lambda item: (item[1], item[0]))
    elif sort_mode == "canonical-desc":
        filtered_items.sort(key=lambda item: (item[1], item[0]), reverse=True)
    elif sort_mode == "group-size":
        group_sizes: dict[str, int] = {}
        for _, canonical in filtered_items:
            group_sizes[canonical] = group_sizes.get(canonical, 0) + 1
        filtered_items.sort(key=lambda item: (group_sizes[item[1]], item[1], item[0]))
    elif sort_mode == "group-size-desc":
        group_sizes = {}
        for _, canonical in filtered_items:
            group_sizes[canonical] = group_sizes.get(canonical, 0) + 1
        filtered_items.sort(key=lambda item: (-group_sizes[item[1]], item[1], item[0]))
    elif sort_mode in ("group-share-pct", "group-share-pct-desc"):
        group_sizes = {}
        for _, canonical in filtered_items:
            group_sizes[canonical] = group_sizes.get(canonical, 0) + 1
        total_aliases = len(filtered_items)

        def _local_share(canonical: str) -> float:
            if total_aliases == 0:
                return 0.0
            return round((group_sizes[canonical] / total_aliases) * 100.0, 2)

        if sort_mode == "group-share-pct":
            filtered_items.sort(key=lambda item: (_local_share(item[1]), item[1], item[0]))
        else:
            filtered_items.sort(key=lambda item: (-_local_share(item[1]), item[1], item[0]))
    elif sort_mode in ("group-size-global", "group-size-global-desc"):
        global_group_sizes, _, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)
        if sort_mode == "group-size-global":
            filtered_items.sort(key=lambda item: (global_group_sizes.get(item[1], 0), item[1], item[0]))
        else:
            filtered_items.sort(key=lambda item: (-global_group_sizes.get(item[1], 0), item[1], item[0]))
    elif sort_mode in ("group-share-pct-global", "group-share-pct-global-desc"):
        global_group_sizes, global_alias_count, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)

        def _global_share(canonical: str) -> float:
            if global_alias_count == 0:
                return 0.0
            return round((global_group_sizes.get(canonical, 0) / global_alias_count) * 100.0, 2)

        if sort_mode == "group-share-pct-global":
            filtered_items.sort(key=lambda item: (_global_share(item[1]), item[1], item[0]))
        else:
            filtered_items.sort(key=lambda item: (-_global_share(item[1]), item[1], item[0]))
    elif sort_mode in (
        "group-share-delta",
        "group-share-delta-desc",
        "group-share-delta-abs",
        "group-share-delta-abs-desc",
        "group-size-delta",
        "group-size-delta-desc",
        "group-size-delta-abs",
        "group-size-delta-abs-desc",
        "group-size-delta-pct",
        "group-size-delta-pct-desc",
        "group-size-delta-pct-abs",
        "group-size-delta-pct-abs-desc",
    ):
        local_group_sizes = {}
        for _, canonical in filtered_items:
            local_group_sizes[canonical] = local_group_sizes.get(canonical, 0) + 1
        local_alias_count = len(filtered_items)
        global_group_sizes, global_alias_count, _ = _compute_group_sizes_and_share_pct(PRESET_SORT_ALIAS_MAP)

        def _local_share(canonical: str) -> float:
            if local_alias_count == 0:
                return 0.0
            return round((local_group_sizes.get(canonical, 0) / local_alias_count) * 100.0, 2)

        def _global_share(canonical: str) -> float:
            if global_alias_count == 0:
                return 0.0
            return round((global_group_sizes.get(canonical, 0) / global_alias_count) * 100.0, 2)

        def _share_delta(canonical: str) -> float:
            return round(_local_share(canonical) - _global_share(canonical), 2)

        def _abs_share_delta(canonical: str) -> float:
            return round(abs(_share_delta(canonical)), 2)

        def _size_delta(canonical: str) -> int:
            return local_group_sizes.get(canonical, 0) - global_group_sizes.get(canonical, 0)

        def _abs_size_delta(canonical: str) -> int:
            return abs(_size_delta(canonical))

        def _size_delta_pct(canonical: str) -> float:
            global_size = global_group_sizes.get(canonical, 0)
            local_size = local_group_sizes.get(canonical, 0)
            if global_size <= 0:
                return 0.0 if local_size <= 0 else 100.0
            return round(((local_size - global_size) / global_size) * 100.0, 2)

        def _abs_size_delta_pct(canonical: str) -> float:
            return round(abs(_size_delta_pct(canonical)), 2)

        if sort_mode == "group-share-delta":
            filtered_items.sort(key=lambda item: (_share_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-share-delta-desc":
            filtered_items.sort(key=lambda item: (-_share_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-share-delta-abs":
            filtered_items.sort(key=lambda item: (_abs_share_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-share-delta-abs-desc":
            filtered_items.sort(key=lambda item: (-_abs_share_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta":
            filtered_items.sort(key=lambda item: (_size_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-desc":
            filtered_items.sort(key=lambda item: (-_size_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-abs":
            filtered_items.sort(key=lambda item: (_abs_size_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-abs-desc":
            filtered_items.sort(key=lambda item: (-_abs_size_delta(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-pct":
            filtered_items.sort(key=lambda item: (_size_delta_pct(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-pct-desc":
            filtered_items.sort(key=lambda item: (-_size_delta_pct(item[1]), item[1], item[0]))
        elif sort_mode == "group-size-delta-pct-abs":
            filtered_items.sort(key=lambda item: (_abs_size_delta_pct(item[1]), item[1], item[0]))
        else:
            filtered_items.sort(key=lambda item: (-_abs_size_delta_pct(item[1]), item[1], item[0]))
    else:
        raise ValueError(f"unsupported list-sort-aliases sort mode: {sort_mode}")

    filtered_count = len(filtered_items)
    truncated = False
    if limit is not None and filtered_count > limit:
        filtered_items = filtered_items[:limit]
        truncated = True
    return dict(filtered_items), filtered_count, truncated


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_head_short(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_branch_name(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_remote_origin_url(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_dirty_state(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return "dirty" if completed.stdout.strip() else "clean"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_head_commit_date_utc(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%cI", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_head_subject(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%s", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip().replace("\t", " ")
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_toplevel(cwd: str | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_repo_name(cwd: str | None = None) -> str:
    top = _git_toplevel(cwd=cwd)
    if top in ("", "unknown"):
        return "unknown"
    name = Path(top).name.strip()
    return name or "unknown"


def _git_worktree_name(cwd: str | None = None) -> str:
    try:
        base = Path(cwd or os.getcwd()).resolve().name.strip()
    except OSError:
        return "unknown"
    return base or "unknown"


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "unknown"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return payload


def parse_csv_list(raw: str, field_name: str) -> list[str]:
    values = [v.strip() for v in raw.split(",") if v.strip()]
    if not values:
        raise ValueError(f"{field_name} must include at least one non-empty value")
    return values


def _validate_preset(name: str, preset: Any, preset_file: Path) -> dict[str, Any]:
    if not isinstance(preset, dict):
        raise ValueError(f"{preset_file}: presets.{name} must be an object")

    allowed_keys = {
        "models",
        "prompt_conditions",
        "repeats",
        "cheap_first",
        "fair_model_allocation",
        "max_total_runs",
        "max_total_runs_mode",
        "max_runs_per_model",
        "max_runs_per_prompt_condition",
        "max_runs_per_task",
        "max_runs_per_task_model",
        "max_runs_per_task_prompt_condition",
        "description",
        "tags",
    }
    unknown_keys = sorted(k for k in preset if k not in allowed_keys)
    if unknown_keys:
        raise ValueError(
            f"{preset_file}: presets.{name} contains unknown key(s): {', '.join(unknown_keys)}"
        )

    if "models" in preset and (not isinstance(preset["models"], str) or not preset["models"].strip()):
        raise ValueError(f"{preset_file}: presets.{name}.models must be a non-empty string")
    if "prompt_conditions" in preset and (
        not isinstance(preset["prompt_conditions"], str) or not preset["prompt_conditions"].strip()
    ):
        raise ValueError(f"{preset_file}: presets.{name}.prompt_conditions must be a non-empty string")

    int_keys = [
        "repeats",
        "max_total_runs",
        "max_runs_per_model",
        "max_runs_per_prompt_condition",
        "max_runs_per_task",
        "max_runs_per_task_model",
        "max_runs_per_task_prompt_condition",
    ]
    for key in int_keys:
        if key not in preset:
            continue
        value = preset[key]
        if not isinstance(value, int):
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be an integer")
        if key == "repeats" and value < 1:
            raise ValueError(f"{preset_file}: presets.{name}.repeats must be >= 1")
        if key != "repeats" and value < 0:
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be >= 0")

    bool_keys = ["cheap_first", "fair_model_allocation"]
    for key in bool_keys:
        if key in preset and not isinstance(preset[key], bool):
            raise ValueError(f"{preset_file}: presets.{name}.{key} must be a boolean")

    if "description" in preset and (
        not isinstance(preset["description"], str) or not preset["description"].strip()
    ):
        raise ValueError(f"{preset_file}: presets.{name}.description must be a non-empty string")

    if "tags" in preset:
        tags = preset["tags"]
        if not isinstance(tags, list) or not tags:
            raise ValueError(f"{preset_file}: presets.{name}.tags must be a non-empty array")
        for idx, tag in enumerate(tags):
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(
                    f"{preset_file}: presets.{name}.tags[{idx}] must be a non-empty string"
                )

    if "max_total_runs_mode" in preset:
        mode = preset["max_total_runs_mode"]
        if mode not in {"fail", "cap"}:
            raise ValueError(
                f"{preset_file}: presets.{name}.max_total_runs_mode must be one of: fail, cap"
            )

    return preset


def load_preset_file(preset_file: Path) -> dict[str, Any]:
    payload = load_json(preset_file)
    schema_version = payload.get("schema_version")
    if schema_version != "v1":
        raise ValueError(f"{preset_file}: schema_version must be 'v1' (got '{schema_version}')")
    presets_raw = payload.get("presets")
    if not isinstance(presets_raw, dict):
        raise ValueError(f"{preset_file}: presets must be an object")

    return {name: _validate_preset(name, preset, preset_file) for name, preset in presets_raw.items()}


def load_preset_config(preset_file: Path, preset_name: str) -> dict[str, Any]:
    presets_raw = load_preset_file(preset_file)
    preset = presets_raw.get(preset_name)
    if not isinstance(preset, dict):
        available = ", ".join(sorted(presets_raw.keys())) or "<none>"
        raise ValueError(
            f"{preset_file}: unknown preset '{preset_name}' (available: {available})"
        )
    return preset


def resolve_preset_with_defaults(preset: dict[str, Any]) -> dict[str, Any]:
    raw_tags = preset.get("tags", [])
    tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()] if isinstance(raw_tags, list) else []
    return {
        "models": str(preset.get("models", "")),
        "prompt_conditions": str(preset.get("prompt_conditions", "")),
        "repeats": int(preset.get("repeats", 1)),
        "cheap_first": bool(preset.get("cheap_first", False)),
        "fair_model_allocation": bool(preset.get("fair_model_allocation", False)),
        "max_total_runs": int(preset.get("max_total_runs", 0)),
        "max_total_runs_mode": str(preset.get("max_total_runs_mode", "fail")),
        "max_runs_per_model": int(preset.get("max_runs_per_model", 0)),
        "max_runs_per_prompt_condition": int(preset.get("max_runs_per_prompt_condition", 0)),
        "max_runs_per_task": int(preset.get("max_runs_per_task", 0)),
        "max_runs_per_task_model": int(preset.get("max_runs_per_task_model", 0)),
        "max_runs_per_task_prompt_condition": int(preset.get("max_runs_per_task_prompt_condition", 0)),
        "description": str(preset.get("description", "")),
        "tags": tags,
    }


def _matches_preset_tags(
    preset: dict[str, Any],
    required_tags: set[str],
    match_mode: str = "all",
    filter_mode: str = "exact",
    case_sensitive: bool = False,
) -> bool:
    if not required_tags:
        return True
    raw_tags = preset.get("tags", [])
    if not isinstance(raw_tags, list):
        return False
    mode = _resolve_filter_mode(filter_mode)
    if case_sensitive:
        preset_tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
        required = [tag for tag in required_tags if tag]
    else:
        preset_tags = [str(tag).strip().lower() for tag in raw_tags if str(tag).strip()]
        required = [tag.lower() for tag in required_tags if tag]

    def _tag_match(required_tag: str) -> bool:
        if mode == "prefix":
            return any(tag.startswith(required_tag) for tag in preset_tags)
        if mode == "contains":
            return any(required_tag in tag for tag in preset_tags)
        return required_tag in preset_tags

    if match_mode == "any":
        return any(_tag_match(tag) for tag in required)
    return all(_tag_match(tag) for tag in required)


def _matches_preset_name(
    name: str,
    name_filter: str | None,
    filter_mode: str = "contains",
    case_sensitive: bool = False,
) -> bool:
    if not name_filter:
        return True
    mode = _resolve_filter_mode(filter_mode)
    target_name = name if case_sensitive else name.lower()
    target_filter = name_filter if case_sensitive else name_filter.lower()
    if mode == "prefix":
        return target_name.startswith(target_filter)
    if mode == "exact":
        return target_name == target_filter
    return target_filter in target_name


def _preset_description_text(raw_description: str) -> str:
    normalized = " ".join(str(raw_description).replace("\t", " ").split())
    if not normalized:
        return "-"
    return normalized


def _preset_description_preview(raw_description: str, max_len: int = 60) -> str:
    normalized = _preset_description_text(raw_description)
    if normalized == "-":
        return normalized
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[: max_len - 3].rstrip()}..."


def _parse_tag_sort_mode(sort_mode: str) -> tuple[str, bool] | None:
    if not sort_mode.startswith("tag:"):
        return None
    tag_expr = sort_mode[len("tag:") :].strip().lower()
    descending = False
    if tag_expr.endswith("-desc"):
        descending = True
        tag_expr = tag_expr[: -len("-desc")].strip()
    if not tag_expr:
        raise ValueError(
            "--list-presets-sort tag mode must be tag:<name>/t:<name> or tag:<name>-desc/t:<name>-desc with a non-empty tag"
        )
    return (tag_expr, descending)


def _sort_preset_names(
    preset_names: list[str],
    presets: dict[str, dict[str, Any]],
    sort_mode: str,
) -> list[str]:
    if sort_mode == "name":
        return sorted(preset_names)

    if sort_mode == "name-desc":
        return sorted(preset_names, reverse=True)

    custom_tag_sort = _parse_tag_sort_mode(sort_mode)
    custom_tag_name = custom_tag_sort[0] if custom_tag_sort else None
    custom_tag_descending = custom_tag_sort[1] if custom_tag_sort else False

    if sort_mode in (
        "max-total-runs",
        "max-total-runs-desc",
        "total-cap",
        "total-cap-desc",
        "repeats",
        "repeats-desc",
        "model-count",
        "model-count-desc",
        "prompt-condition-count",
        "prompt-condition-count-desc",
        "max-runs-per-model",
        "max-runs-per-model-desc",
        "per-model-cap",
        "per-model-cap-desc",
        "max-runs-per-prompt-condition",
        "max-runs-per-prompt-condition-desc",
        "per-prompt-cap",
        "per-prompt-cap-desc",
        "per-condition-cap",
        "per-condition-cap-desc",
        "max-runs-per-task",
        "max-runs-per-task-desc",
        "per-task-cap",
        "per-task-cap-desc",
        "task-cap",
        "task-cap-desc",
        "max-runs-per-task-model",
        "max-runs-per-task-model-desc",
        "per-task-model-cap",
        "per-task-model-cap-desc",
        "task-model-cap",
        "task-model-cap-desc",
        "max-runs-per-task-prompt-condition",
        "max-runs-per-task-prompt-condition-desc",
        "per-task-prompt-cap",
        "per-task-prompt-cap-desc",
        "per-task-condition-cap",
        "per-task-condition-cap-desc",
        "task-prompt-cap",
        "task-prompt-cap-desc",
        "task-condition-cap",
        "task-condition-cap-desc",
        "description-length",
        "description-length-desc",
        "tag-count",
        "tag-count-desc",
        "cheap-first-tag",
        "cheap-first-tag-desc",
        "cheap-first",
        "cheap-first-desc",
        "cheap-first-total-cap",
        "cheap-first-total-cap-desc",
        "cheap-total-cap",
        "cheap-total-cap-desc",
        "fair-allocation-total-cap",
        "fair-allocation-total-cap-desc",
        "fair-total-cap",
        "fair-total-cap-desc",
        "fair-cap",
        "fair-cap-desc",
        "cost-priority",
        "cost-priority-desc",
        "cost-priority-prompt",
        "cost-priority-prompt-desc",
        "cost",
        "cost-desc",
        "cost-prompt",
        "cost-prompt-desc",
        "cost-condition",
        "cost-condition-desc",
        "cc",
        "ccd",
        "fair-model-allocation",
        "fair-model-allocation-desc",
        "fair-allocation",
        "fair-allocation-desc",
    ) or custom_tag_sort:
        resolved_caps: dict[str, int] = {}
        resolved_repeats: dict[str, int] = {}
        resolved_model_counts: dict[str, int] = {}
        resolved_prompt_condition_counts: dict[str, int] = {}
        resolved_description_lengths: dict[str, int] = {}
        resolved_max_runs_per_model: dict[str, int] = {}
        resolved_max_runs_per_prompt_condition: dict[str, int] = {}
        resolved_max_runs_per_task: dict[str, int] = {}
        resolved_max_runs_per_task_model: dict[str, int] = {}
        resolved_max_runs_per_task_prompt_condition: dict[str, int] = {}
        resolved_cheap_first_tag_flags: dict[str, int] = {}
        resolved_fair_model_allocation_flags: dict[str, int] = {}
        resolved_custom_tag_flags: dict[str, int] = {}
        resolved_tag_counts: dict[str, int] = {}
        for name in preset_names:
            preset = presets.get(name, {})
            resolved = resolve_preset_with_defaults(preset)
            resolved_caps[name] = int(resolved.get("max_total_runs", 0))
            resolved_repeats[name] = int(resolved.get("repeats", 1))
            models = resolved.get("models", [])
            if isinstance(models, list):
                resolved_model_counts[name] = len(models)
            elif isinstance(models, str):
                resolved_model_counts[name] = len([token for token in models.split(",") if token.strip()])
            else:
                resolved_model_counts[name] = 0
            prompt_conditions = resolved.get("prompt_conditions", [])
            if isinstance(prompt_conditions, list):
                resolved_prompt_condition_counts[name] = len(prompt_conditions)
            elif isinstance(prompt_conditions, str):
                resolved_prompt_condition_counts[name] = len(
                    [token for token in prompt_conditions.split(",") if token.strip()]
                )
            else:
                resolved_prompt_condition_counts[name] = 0
            resolved_max_runs_per_model[name] = int(resolved.get("max_runs_per_model", 0))
            resolved_max_runs_per_prompt_condition[name] = int(
                resolved.get("max_runs_per_prompt_condition", 0)
            )
            resolved_max_runs_per_task[name] = int(resolved.get("max_runs_per_task", 0))
            resolved_max_runs_per_task_model[name] = int(resolved.get("max_runs_per_task_model", 0))
            resolved_max_runs_per_task_prompt_condition[name] = int(
                resolved.get("max_runs_per_task_prompt_condition", 0)
            )
            description_text = _preset_description_text(resolved.get("description", ""))
            resolved_description_lengths[name] = 0 if description_text == "-" else len(description_text)
            tags = resolved.get("tags", [])
            normalized_tags = (
                {str(tag).strip().lower() for tag in tags if str(tag).strip()} if isinstance(tags, list) else set()
            )
            resolved_cheap_first_tag_flags[name] = 1 if "cheap-first" in normalized_tags else 0
            resolved_fair_model_allocation_flags[name] = 1 if resolved.get("fair_model_allocation") else 0
            resolved_custom_tag_flags[name] = 1 if custom_tag_name and custom_tag_name in normalized_tags else 0
            resolved_tag_counts[name] = len(normalized_tags)

        if sort_mode in ("max-total-runs", "total-cap"):
            def asc_sort_key(name: str) -> tuple[int, int, str]:
                max_total_runs = resolved_caps[name]
                is_uncapped = 1 if max_total_runs == 0 else 0
                normalized_cap = max_total_runs if max_total_runs > 0 else sys.maxsize
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=asc_sort_key)

        if sort_mode in ("max-total-runs-desc", "total-cap-desc"):
            def desc_sort_key(name: str) -> tuple[int, int, str]:
                max_total_runs = resolved_caps[name]
                is_uncapped = 0 if max_total_runs == 0 else 1
                normalized_cap = -max_total_runs if max_total_runs > 0 else 0
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=desc_sort_key)

        if sort_mode == "repeats":
            return sorted(preset_names, key=lambda name: (resolved_repeats[name], name))

        if sort_mode == "repeats-desc":
            return sorted(preset_names, key=lambda name: (-resolved_repeats[name], name))

        if sort_mode == "model-count":
            return sorted(preset_names, key=lambda name: (resolved_model_counts[name], name))

        if sort_mode == "model-count-desc":
            return sorted(preset_names, key=lambda name: (-resolved_model_counts[name], name))

        if sort_mode == "prompt-condition-count":
            return sorted(preset_names, key=lambda name: (resolved_prompt_condition_counts[name], name))

        if sort_mode == "prompt-condition-count-desc":
            return sorted(preset_names, key=lambda name: (-resolved_prompt_condition_counts[name], name))

        if sort_mode in ("max-runs-per-model", "per-model-cap"):
            def max_runs_per_model_asc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_model = resolved_max_runs_per_model[name]
                is_uncapped = 1 if max_runs_per_model == 0 else 0
                normalized_cap = max_runs_per_model if max_runs_per_model > 0 else sys.maxsize
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_model_asc_sort_key)

        if sort_mode in ("max-runs-per-model-desc", "per-model-cap-desc"):
            def max_runs_per_model_desc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_model = resolved_max_runs_per_model[name]
                is_uncapped = 0 if max_runs_per_model == 0 else 1
                normalized_cap = -max_runs_per_model if max_runs_per_model > 0 else 0
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_model_desc_sort_key)

        if sort_mode in ("max-runs-per-prompt-condition", "per-prompt-cap", "per-condition-cap"):
            def max_runs_per_prompt_condition_asc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_prompt_condition = resolved_max_runs_per_prompt_condition[name]
                is_uncapped = 1 if max_runs_per_prompt_condition == 0 else 0
                normalized_cap = (
                    max_runs_per_prompt_condition
                    if max_runs_per_prompt_condition > 0
                    else sys.maxsize
                )
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_prompt_condition_asc_sort_key)

        if sort_mode in (
            "max-runs-per-prompt-condition-desc",
            "per-prompt-cap-desc",
            "per-condition-cap-desc",
        ):
            def max_runs_per_prompt_condition_desc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_prompt_condition = resolved_max_runs_per_prompt_condition[name]
                is_uncapped = 0 if max_runs_per_prompt_condition == 0 else 1
                normalized_cap = -max_runs_per_prompt_condition if max_runs_per_prompt_condition > 0 else 0
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_prompt_condition_desc_sort_key)

        if sort_mode in ("max-runs-per-task", "per-task-cap", "task-cap"):
            def max_runs_per_task_asc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task = resolved_max_runs_per_task[name]
                is_uncapped = 1 if max_runs_per_task == 0 else 0
                normalized_cap = max_runs_per_task if max_runs_per_task > 0 else sys.maxsize
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_asc_sort_key)

        if sort_mode in ("max-runs-per-task-desc", "per-task-cap-desc", "task-cap-desc"):
            def max_runs_per_task_desc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task = resolved_max_runs_per_task[name]
                is_uncapped = 0 if max_runs_per_task == 0 else 1
                normalized_cap = -max_runs_per_task if max_runs_per_task > 0 else 0
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_desc_sort_key)

        if sort_mode in ("max-runs-per-task-model", "per-task-model-cap", "task-model-cap"):
            def max_runs_per_task_model_asc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task_model = resolved_max_runs_per_task_model[name]
                is_uncapped = 1 if max_runs_per_task_model == 0 else 0
                normalized_cap = max_runs_per_task_model if max_runs_per_task_model > 0 else sys.maxsize
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_model_asc_sort_key)

        if sort_mode in ("max-runs-per-task-model-desc", "per-task-model-cap-desc", "task-model-cap-desc"):
            def max_runs_per_task_model_desc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task_model = resolved_max_runs_per_task_model[name]
                is_uncapped = 0 if max_runs_per_task_model == 0 else 1
                normalized_cap = -max_runs_per_task_model if max_runs_per_task_model > 0 else 0
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_model_desc_sort_key)

        if sort_mode in (
            "max-runs-per-task-prompt-condition",
            "per-task-prompt-cap",
            "per-task-condition-cap",
            "task-prompt-cap",
            "task-condition-cap",
        ):
            def max_runs_per_task_prompt_condition_asc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task_prompt_condition = resolved_max_runs_per_task_prompt_condition[name]
                is_uncapped = 1 if max_runs_per_task_prompt_condition == 0 else 0
                normalized_cap = (
                    max_runs_per_task_prompt_condition
                    if max_runs_per_task_prompt_condition > 0
                    else sys.maxsize
                )
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_prompt_condition_asc_sort_key)

        if sort_mode in (
            "max-runs-per-task-prompt-condition-desc",
            "per-task-prompt-cap-desc",
            "per-task-condition-cap-desc",
            "task-prompt-cap-desc",
            "task-condition-cap-desc",
        ):
            def max_runs_per_task_prompt_condition_desc_sort_key(name: str) -> tuple[int, int, str]:
                max_runs_per_task_prompt_condition = resolved_max_runs_per_task_prompt_condition[name]
                is_uncapped = 0 if max_runs_per_task_prompt_condition == 0 else 1
                normalized_cap = (
                    -max_runs_per_task_prompt_condition
                    if max_runs_per_task_prompt_condition > 0
                    else 0
                )
                return (is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=max_runs_per_task_prompt_condition_desc_sort_key)

        if sort_mode == "description-length":
            return sorted(preset_names, key=lambda name: (resolved_description_lengths[name], name))

        if sort_mode == "description-length-desc":
            return sorted(preset_names, key=lambda name: (-resolved_description_lengths[name], name))

        if sort_mode == "tag-count":
            return sorted(preset_names, key=lambda name: (resolved_tag_counts[name], name))

        if sort_mode == "tag-count-desc":
            return sorted(preset_names, key=lambda name: (-resolved_tag_counts[name], name))

        if custom_tag_sort:
            if custom_tag_descending:
                return sorted(preset_names, key=lambda name: (resolved_custom_tag_flags[name], name))
            return sorted(preset_names, key=lambda name: (-resolved_custom_tag_flags[name], name))

        if sort_mode in ("cheap-first-tag", "cheap-first"):
            return sorted(preset_names, key=lambda name: (-resolved_cheap_first_tag_flags[name], name))

        if sort_mode in ("cheap-first-total-cap", "cheap-total-cap"):
            def cheap_first_total_cap_sort_key(name: str) -> tuple[int, int, int, str]:
                cheap_first_rank = -resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                is_uncapped = 1 if max_total_runs == 0 else 0
                normalized_cap = max_total_runs if max_total_runs > 0 else sys.maxsize
                return (cheap_first_rank, is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=cheap_first_total_cap_sort_key)

        if sort_mode in ("cheap-first-total-cap-desc", "cheap-total-cap-desc"):
            def cheap_first_total_cap_desc_sort_key(name: str) -> tuple[int, int, int, str]:
                cheap_first_rank = resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                is_uncapped = 0 if max_total_runs == 0 else 1
                normalized_cap = -max_total_runs if max_total_runs > 0 else 0
                return (cheap_first_rank, is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=cheap_first_total_cap_desc_sort_key)

        if sort_mode in ("fair-allocation-total-cap", "fair-total-cap", "fair-cap"):
            def fair_allocation_total_cap_sort_key(name: str) -> tuple[int, int, int, str]:
                fair_rank = -resolved_fair_model_allocation_flags[name]
                max_total_runs = resolved_caps[name]
                is_uncapped = 1 if max_total_runs == 0 else 0
                normalized_cap = max_total_runs if max_total_runs > 0 else sys.maxsize
                return (fair_rank, is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=fair_allocation_total_cap_sort_key)

        if sort_mode in ("fair-allocation-total-cap-desc", "fair-total-cap-desc", "fair-cap-desc"):
            def fair_allocation_total_cap_desc_sort_key(name: str) -> tuple[int, int, int, str]:
                fair_rank = resolved_fair_model_allocation_flags[name]
                max_total_runs = resolved_caps[name]
                is_uncapped = 0 if max_total_runs == 0 else 1
                normalized_cap = -max_total_runs if max_total_runs > 0 else 0
                return (fair_rank, is_uncapped, normalized_cap, name)

            return sorted(preset_names, key=fair_allocation_total_cap_desc_sort_key)

        if sort_mode in ("cost-priority", "cost"):
            def cost_priority_sort_key(name: str) -> tuple[int, int, int, int, str]:
                cheap_first_rank = -resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                total_is_uncapped = 1 if max_total_runs == 0 else 0
                normalized_total_cap = max_total_runs if max_total_runs > 0 else sys.maxsize
                max_runs_per_model = resolved_max_runs_per_model[name]
                model_is_uncapped = 1 if max_runs_per_model == 0 else 0
                normalized_model_cap = max_runs_per_model if max_runs_per_model > 0 else sys.maxsize
                return (
                    cheap_first_rank,
                    total_is_uncapped,
                    normalized_total_cap,
                    model_is_uncapped,
                    normalized_model_cap,
                    name,
                )

            return sorted(preset_names, key=cost_priority_sort_key)

        if sort_mode in ("cost-priority-desc", "cost-desc"):
            def cost_priority_desc_sort_key(name: str) -> tuple[int, int, int, int, str]:
                cheap_first_rank = resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                total_is_uncapped = 0 if max_total_runs == 0 else 1
                normalized_total_cap = -max_total_runs if max_total_runs > 0 else 0
                max_runs_per_model = resolved_max_runs_per_model[name]
                model_is_uncapped = 0 if max_runs_per_model == 0 else 1
                normalized_model_cap = -max_runs_per_model if max_runs_per_model > 0 else 0
                return (
                    cheap_first_rank,
                    total_is_uncapped,
                    normalized_total_cap,
                    model_is_uncapped,
                    normalized_model_cap,
                    name,
                )

            return sorted(preset_names, key=cost_priority_desc_sort_key)

        if sort_mode in ("cost-priority-prompt", "cost-prompt", "cost-condition", "cc"):
            def cost_priority_prompt_sort_key(name: str) -> tuple[int, int, int, int, int, str]:
                cheap_first_rank = -resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                total_is_uncapped = 1 if max_total_runs == 0 else 0
                normalized_total_cap = max_total_runs if max_total_runs > 0 else sys.maxsize
                max_runs_per_prompt_condition = resolved_max_runs_per_prompt_condition[name]
                prompt_is_uncapped = 1 if max_runs_per_prompt_condition == 0 else 0
                normalized_prompt_cap = (
                    max_runs_per_prompt_condition if max_runs_per_prompt_condition > 0 else sys.maxsize
                )
                return (
                    cheap_first_rank,
                    total_is_uncapped,
                    normalized_total_cap,
                    prompt_is_uncapped,
                    normalized_prompt_cap,
                    name,
                )

            return sorted(preset_names, key=cost_priority_prompt_sort_key)

        if sort_mode in ("cost-priority-prompt-desc", "cost-prompt-desc", "cost-condition-desc", "ccd"):
            def cost_priority_prompt_desc_sort_key(name: str) -> tuple[int, int, int, int, int, str]:
                cheap_first_rank = resolved_cheap_first_tag_flags[name]
                max_total_runs = resolved_caps[name]
                total_is_uncapped = 0 if max_total_runs == 0 else 1
                normalized_total_cap = -max_total_runs if max_total_runs > 0 else 0
                max_runs_per_prompt_condition = resolved_max_runs_per_prompt_condition[name]
                prompt_is_uncapped = 0 if max_runs_per_prompt_condition == 0 else 1
                normalized_prompt_cap = (
                    -max_runs_per_prompt_condition if max_runs_per_prompt_condition > 0 else 0
                )
                return (
                    cheap_first_rank,
                    total_is_uncapped,
                    normalized_total_cap,
                    prompt_is_uncapped,
                    normalized_prompt_cap,
                    name,
                )

            return sorted(preset_names, key=cost_priority_prompt_desc_sort_key)

        if sort_mode in ("cheap-first-tag-desc", "cheap-first-desc"):
            return sorted(preset_names, key=lambda name: (resolved_cheap_first_tag_flags[name], name))

        if sort_mode in ("fair-model-allocation", "fair-allocation"):
            return sorted(preset_names, key=lambda name: (-resolved_fair_model_allocation_flags[name], name))

        if sort_mode in ("fair-model-allocation-desc", "fair-allocation-desc"):
            return sorted(preset_names, key=lambda name: (resolved_fair_model_allocation_flags[name], name))

        return sorted(preset_names, key=lambda name: (resolved_cheap_first_tag_flags[name], name))

    raise ValueError(f"unsupported --list-presets-sort mode: {sort_mode}")


def _format_preset_summary_line(name: str, resolved: dict[str, Any]) -> str:
    tags = resolved.get("tags", [])
    tag_value = ",".join(tags) if isinstance(tags, list) and tags else "-"
    description_preview = _preset_description_preview(resolved.get("description", ""))
    return (
        f"{name}\tmodels={resolved['models']}\tprompt_conditions={resolved['prompt_conditions']}\t"
        f"repeats={resolved['repeats']}\tcheap_first={str(resolved['cheap_first']).lower()}\t"
        f"fair_model_allocation={str(resolved['fair_model_allocation']).lower()}\t"
        f"max_total_runs={resolved['max_total_runs']}\tmax_total_runs_mode={resolved['max_total_runs_mode']}\t"
        f"max_runs_per_model={resolved['max_runs_per_model']}\t"
        f"max_runs_per_prompt_condition={resolved['max_runs_per_prompt_condition']}\t"
        f"max_runs_per_task={resolved['max_runs_per_task']}\t"
        f"max_runs_per_task_model={resolved['max_runs_per_task_model']}\t"
        f"max_runs_per_task_prompt_condition={resolved['max_runs_per_task_prompt_condition']}\t"
        f"tags={tag_value}\tdescription={description_preview}"
    )


def _emit_preset_summary_tsv_header(
    with_schema_header: bool,
    description_mode: str,
    with_schema_column: bool,
    schema_id: str,
) -> None:
    if with_schema_header:
        print(f"# schema={schema_id}")
    description_column = "description_full" if description_mode == "full" else "description_preview"
    columns = [*PRESET_SUMMARY_TSV_BASE_COLUMNS, "description_mode", "description_truncated", description_column]
    if with_schema_column:
        columns.append("schema")
    print("\t".join(columns))


def _format_preset_summary_tsv_row(
    name: str,
    resolved: dict[str, Any],
    description_mode: str = "preview",
    with_schema_column: bool = False,
    schema_id: str = PRESET_SUMMARY_TSV_SCHEMA,
    description_max_len: int | None = None,
) -> str:
    tags = resolved.get("tags", [])
    tag_value = ",".join(tags) if isinstance(tags, list) and tags else "-"
    raw_description = str(resolved.get("description", ""))
    normalized_full_description = _preset_description_text(raw_description)
    description_length = 0 if normalized_full_description == "-" else len(normalized_full_description)
    if description_mode == "full":
        description_value = normalized_full_description
        if description_max_len:
            description_value = _preset_description_preview(description_value, description_max_len)
        description_truncated = description_value != normalized_full_description
    else:
        description_value = _preset_description_preview(raw_description)
        description_truncated = description_value != normalized_full_description
    row = [
        name,
        str(resolved["models"]),
        str(resolved["prompt_conditions"]),
        str(resolved["repeats"]),
        str(resolved["cheap_first"]).lower(),
        str(resolved["fair_model_allocation"]).lower(),
        str(resolved["max_total_runs"]),
        str(resolved["max_total_runs_mode"]),
        str(resolved["max_runs_per_model"]),
        str(resolved["max_runs_per_prompt_condition"]),
        str(resolved["max_runs_per_task"]),
        str(resolved["max_runs_per_task_model"]),
        str(resolved["max_runs_per_task_prompt_condition"]),
        tag_value,
        str(description_length),
        description_mode,
        str(description_truncated).lower(),
        description_value,
    ]
    if with_schema_column:
        row.append(schema_id)
    return "\t".join(item.replace("\t", " ") for item in row)


def _emit_text_or_json_meta(
    fields: dict[str, Any],
    meta_format: str = "text",
    json_schema_version: str = PRESET_TEXT_META_JSON_SCHEMA_VERSION,
) -> None:
    if meta_format == "json":
        payload: dict[str, Any] = {
            "meta": True,
            "schema_version": json_schema_version,
        }
        payload.update(fields)
        print(json.dumps(payload, ensure_ascii=False))
        return
    text_fields = [f"{key}={value}" for key, value in fields.items()]
    print("# meta\t" + "\t".join(text_fields))


def _resolve_preset_output_delimiter(output_format: str) -> str:
    if output_format == "summary-tsv":
        return "tab"
    if output_format in {"json", "resolved-json"}:
        return "none"
    return "newline"


def _resolve_preset_output_transport(output_format: str) -> str:
    if output_format in {"json", "resolved-json"}:
        return "json"
    if output_format == "summary-tsv":
        return "tsv"
    return "text"


def _resolve_preset_output_has_header(output_format: str) -> bool:
    return output_format == "summary-tsv"


def _resolve_preset_output_columns(output_format: str, with_schema_column: bool) -> list[str]:
    if output_format in {"json", "resolved-json"}:
        return []
    if output_format == "summary-tsv":
        columns = [
            *PRESET_SUMMARY_TSV_BASE_COLUMNS,
            "description_mode",
            "description_truncated",
            "description",
        ]
        if with_schema_column:
            columns.append("schema")
        return columns
    return ["line"]


def _resolve_preset_output_column_count(output_format: str, with_schema_column: bool) -> int:
    return len(_resolve_preset_output_columns(output_format, with_schema_column=with_schema_column))


def _resolve_preset_output_columns_sha256(output_format: str, with_schema_column: bool) -> str:
    columns = _resolve_preset_output_columns(output_format, with_schema_column=with_schema_column)
    return hashlib.sha256("\n".join(columns).encode("utf-8")).hexdigest()


def _resolve_preset_output_shape_fields() -> list[str]:
    return [
        "output",
        "output_transport",
        "output_has_header",
        "output_delimiter",
        "output_field_count",
        "output_column_count",
        "output_columns",
    ]


def _resolve_preset_output_shape_payload(
    output_format: str,
    with_schema_column: bool,
) -> dict[str, str | bool | int | list[str]]:
    return {
        "output": output_format,
        "output_transport": _resolve_preset_output_transport(output_format),
        "output_has_header": _resolve_preset_output_has_header(output_format),
        "output_delimiter": _resolve_preset_output_delimiter(output_format),
        "output_field_count": _resolve_preset_output_column_count(
            output_format,
            with_schema_column=with_schema_column,
        ),
        "output_column_count": _resolve_preset_output_column_count(
            output_format,
            with_schema_column=with_schema_column,
        ),
        "output_columns": _resolve_preset_output_columns(
            output_format,
            with_schema_column=with_schema_column,
        ),
    }


def _resolve_preset_output_shape_payload_json(output_format: str, with_schema_column: bool) -> str:
    return json.dumps(
        _resolve_preset_output_shape_payload(
            output_format,
            with_schema_column=with_schema_column,
        ),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _resolve_preset_output_shape_tuple(output_format: str, with_schema_column: bool) -> str:
    output_columns = _resolve_preset_output_columns(
        output_format,
        with_schema_column=with_schema_column,
    )
    return (
        f"output={output_format}|"
        f"output_transport={_resolve_preset_output_transport(output_format)}|"
        f"output_has_header={str(_resolve_preset_output_has_header(output_format)).lower()}|"
        f"output_delimiter={_resolve_preset_output_delimiter(output_format)}|"
        f"output_field_count={_resolve_preset_output_column_count(output_format, with_schema_column=with_schema_column)}|"
        f"output_column_count={_resolve_preset_output_column_count(output_format, with_schema_column=with_schema_column)}|"
        f"output_columns={','.join(output_columns) if output_columns else 'none'}"
    )


def _resolve_preset_output_shape_sha256(output_format: str, with_schema_column: bool) -> str:
    return hashlib.sha256(
        _resolve_preset_output_shape_payload_json(
            output_format,
            with_schema_column=with_schema_column,
        ).encode("utf-8")
    ).hexdigest()


def _resolve_preset_output_shape_payload_json_sha256(output_format: str, with_schema_column: bool) -> str:
    payload = _resolve_preset_output_shape_payload_json(
        output_format,
        with_schema_column=with_schema_column,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_preset_output_shape_payload_json_bytes(output_format: str, with_schema_column: bool) -> int:
    payload = _resolve_preset_output_shape_payload_json(
        output_format,
        with_schema_column=with_schema_column,
    )
    return len(payload.encode("utf-8"))


def _resolve_preset_output_shape_tuple_bytes(output_format: str, with_schema_column: bool) -> int:
    payload = _resolve_preset_output_shape_tuple(
        output_format,
        with_schema_column=with_schema_column,
    )
    return len(payload.encode("utf-8"))


def _resolve_preset_output_shape_payload_json_sha256_algo(output_format: str, with_schema_column: bool) -> str:
    _ = (output_format, with_schema_column)
    return "sha256"


def _resolve_preset_output_shape_sha256_algo(output_format: str, with_schema_column: bool) -> str:
    _ = (output_format, with_schema_column)
    return "sha256"


def _emit_list_presets_text_meta(
    filtered_count: int,
    emitted_count: int,
    truncated: bool,
    schema_id: str,
    output_format: str,
    extra_fields: dict[str, Any] | None = None,
    meta_format: str = "text",
    json_schema_version: str = PRESET_TEXT_META_JSON_SCHEMA_VERSION,
) -> None:
    fields: dict[str, str] = {
        "schema": schema_id,
        "filtered_count": str(filtered_count),
        "emitted_count": str(emitted_count),
        "output_record_count": str(emitted_count),
        "output_is_empty": str(emitted_count == 0).lower(),
        "output_is_single_record": str(emitted_count == 1).lower(),
        "output_has_multiple_records": str(emitted_count > 1).lower(),
        "output_truncated_count": str(max(filtered_count - emitted_count, 0)),
        "truncated": str(truncated).lower(),
        "output_format": output_format,
    }
    if extra_fields:
        fields.update(extra_fields)
    _emit_text_or_json_meta(
        fields,
        meta_format=meta_format,
        json_schema_version=json_schema_version,
    )


def _emit_show_preset_text_meta(
    preset_name: str,
    output_format: str,
    preset_file: Path,
    schema_id: str,
    extra_fields: dict[str, Any] | None = None,
    meta_format: str = "text",
    json_schema_version: str = PRESET_TEXT_META_JSON_SCHEMA_VERSION,
) -> None:
    fields: dict[str, str] = {
        "schema": schema_id,
        "filtered_count": "1",
        "emitted_count": "1",
        "output_record_count": "1",
        "output_is_empty": "false",
        "output_is_single_record": "true",
        "output_has_multiple_records": "false",
        "output_truncated_count": "0",
        "truncated": "false",
        "preset": preset_name,
        "format": output_format,
        "output_format": output_format,
        "preset_file": str(preset_file),
    }
    if extra_fields:
        fields.update(extra_fields)
    _emit_text_or_json_meta(
        fields,
        meta_format=meta_format,
        json_schema_version=json_schema_version,
    )


def _compose_meta_payload(
    base_fields: dict[str, Any],
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(base_fields)
    if extra_fields:
        payload.update(extra_fields)
    return payload


def _apply_show_meta_profile(args: argparse.Namespace) -> None:
    if args.show_preset_meta_profile in (None, "minimal"):
        return
    if args.show_preset_meta_profile in ("debug", "safe-debug", "ci-safe", "privacy-safe"):
        args.show_preset_meta_include_overrides = True
        args.show_preset_meta_include_python_version = True
        args.show_preset_meta_include_git_head = True
        args.show_preset_meta_include_git_branch = True
        args.show_preset_meta_include_git_dirty = True
        args.show_preset_meta_include_git_toplevel = True
        args.show_preset_meta_include_git_repo_name = True
        args.show_preset_meta_include_git_worktree_name = True
        args.show_preset_meta_include_argv_sha256 = True
        args.show_preset_meta_include_argv_count = True
        args.show_preset_meta_include_preset_file_sha256 = True
    if args.show_preset_meta_profile in ("debug", "safe-debug", "ci-safe"):
        args.show_preset_meta_include_cwd = True
    if args.show_preset_meta_profile in ("debug", "safe-debug"):
        args.show_preset_meta_include_generated_at = True
        args.show_preset_meta_include_pid = True
        args.show_preset_meta_include_hostname = True
        args.show_preset_meta_include_git_head_date_utc = True
        args.show_preset_meta_include_git_head_subject = True
        args.show_preset_meta_include_git_remote = True
    if args.show_preset_meta_profile == "debug":
        args.show_preset_meta_include_argv = True
        args.show_preset_meta_include_argv_tokens = True


def _apply_list_meta_profile(args: argparse.Namespace) -> None:
    if args.list_presets_meta_profile in (None, "minimal"):
        return
    if args.list_presets_meta_profile in ("debug", "safe-debug", "ci-safe", "privacy-safe"):
        args.list_presets_meta_include_filters = True
        args.list_presets_meta_include_python_version = True
        args.list_presets_meta_include_git_head = True
        args.list_presets_meta_include_git_branch = True
        args.list_presets_meta_include_git_dirty = True
        args.list_presets_meta_include_git_toplevel = True
        args.list_presets_meta_include_git_repo_name = True
        args.list_presets_meta_include_git_worktree_name = True
        args.list_presets_meta_include_argv_sha256 = True
        args.list_presets_meta_include_argv_count = True
        args.list_presets_meta_include_preset_file_sha256 = True
    if args.list_presets_meta_profile in ("debug", "safe-debug", "ci-safe"):
        args.list_presets_meta_include_cwd = True
    if args.list_presets_meta_profile in ("debug", "safe-debug"):
        args.list_presets_meta_include_generated_at = True
        args.list_presets_meta_include_pid = True
        args.list_presets_meta_include_hostname = True
        args.list_presets_meta_include_git_head_date_utc = True
        args.list_presets_meta_include_git_head_subject = True
        args.list_presets_meta_include_git_remote = True
    if args.list_presets_meta_profile == "debug":
        args.list_presets_meta_include_argv = True
        args.list_presets_meta_include_argv_tokens = True


def _resolve_profile_schema_id(profile: str | None, schema_id: str, default_schema_id: str) -> str:
    """Auto-upgrade default schema id for non-minimal meta profiles.

    If callers use a richer profile but keep the default v1 schema id, bump to v2 so
    downstream parsers can branch by schema id instead of probing optional keys.
    """
    if profile in (None, "minimal"):
        return schema_id
    if schema_id == default_schema_id:
        return default_schema_id.rsplit(".v", 1)[0] + ".v2"
    return schema_id


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _cheap_first_rank(model: str) -> tuple[int, str]:
    name = model.lower()
    cheap_hints = ("nano", "mini", "flash", "haiku", "small", "lite")
    expensive_hints = ("pro", "opus", "sonnet", "large", "ultra")
    if any(h in name for h in cheap_hints):
        return (0, name)
    if any(h in name for h in expensive_hints):
        return (2, name)
    return (1, name)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _ratio_map_1d(planned: dict[str, int], potential: dict[str, int]) -> dict[str, float]:
    return {key: _safe_ratio(planned[key], potential[key]) for key in planned}


def _ratio_map_2d(
    planned: dict[str, dict[str, int]], potential: dict[str, dict[str, int]]
) -> dict[str, dict[str, float]]:
    return {
        outer_key: {
            inner_key: _safe_ratio(planned[outer_key][inner_key], potential[outer_key][inner_key])
            for inner_key in planned[outer_key]
        }
        for outer_key in planned
    }


def validate_task_set(payload: dict[str, Any], path: Path) -> tuple[str, list[dict[str, str]]]:
    schema_version = payload.get("schema_version")
    if schema_version != "v1":
        raise ValueError(f"{path}: schema_version must be 'v1' (got '{schema_version}')")

    task_set_id = payload.get("task_set_id")
    if not isinstance(task_set_id, str) or not task_set_id.strip():
        raise ValueError(f"{path}: task_set_id must be a non-empty string")

    tasks_raw = payload.get("tasks")
    if not isinstance(tasks_raw, list) or not tasks_raw:
        raise ValueError(f"{path}: tasks must be a non-empty array")

    tasks: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(tasks_raw):
        where = f"{path}: tasks[{idx}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be an object")

        task_id = item.get("task_id")
        source = item.get("source")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"{where}: task_id must be a non-empty string")
        if task_id in seen_ids:
            raise ValueError(f"{where}: duplicate task_id '{task_id}'")
        seen_ids.add(task_id)

        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"{where}: source must be a non-empty string")

        tasks.append({"task_id": task_id, "source": source})

    return task_set_id, tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a batch evaluation plan JSON")
    parser.add_argument("task_set_json", nargs="?", type=Path, help="Path to task-set v1 JSON")
    parser.add_argument("--preset", default=None, help="Preset name from --preset-file")
    parser.add_argument(
        "--show-preset",
        default=None,
        help="Show one preset resolved with planner defaults and exit",
    )
    parser.add_argument(
        "--show-preset-format",
        choices=("json", "summary", "summary-tsv"),
        default="json",
        help="Output format for --show-preset (default: json)",
    )
    parser.add_argument(
        "--show-preset-with-meta",
        action="store_true",
        help=(
            "Emit preset/format/preset_file metadata for show-preset outputs; "
            "text formats append a footer and json adds a top-level meta object."
        ),
    )
    parser.add_argument(
        "--show-preset-meta-schema-id",
        default=PRESET_SHOW_TEXT_META_SCHEMA,
        help=(
            "Schema id for --show-preset text meta footer "
            "(default: planner_preset_show_meta.v1)"
        ),
    )
    parser.add_argument(
        "--show-preset-meta-include-overrides",
        action="store_true",
        help=(
            "Include CLI override context in --show-preset text meta footer "
            "(override_count/overrides)."
        ),
    )
    parser.add_argument(
        "--show-preset-meta-format",
        choices=("text", "json"),
        default="text",
        help="Meta footer format for --show-preset-with-meta (default: text)",
    )
    parser.add_argument(
        "--show-preset-meta-profile",
        choices=("minimal", "privacy-safe", "ci-safe", "safe-debug", "debug"),
        default=None,
        help=(
            "Optional profile for --show-preset meta footer fields: "
            "minimal (default behavior), privacy-safe (hash-first provenance without cwd/raw argv), "
            "ci-safe (stable CI/repro fields without volatile host/time metadata), "
            "safe-debug (debug fields without raw argv/tokens), or debug (full debug fields including raw argv/tokens)."
        ),
    )
    parser.add_argument(
        "--show-preset-meta-json-schema-version",
        default=PRESET_TEXT_META_JSON_SCHEMA_VERSION,
        help=(
            "Schema version for --show-preset meta JSON envelope "
            "(default: v1; only used when --show-preset-meta-format=json)"
        ),
    )
    parser.add_argument(
        "--show-preset-meta-include-generated-at",
        action="store_true",
        help="Include generated_at_utc in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-cwd",
        action="store_true",
        help="Include cwd in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-python-version",
        action="store_true",
        help="Include python_version in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-pid",
        action="store_true",
        help="Include pid in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-hostname",
        action="store_true",
        help="Include hostname in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-head",
        action="store_true",
        help="Include git_head (short HEAD commit) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-head-date-utc",
        action="store_true",
        help="Include git_head_date_utc (HEAD commit date, ISO-8601 UTC offset) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-head-subject",
        action="store_true",
        help="Include git_head_subject (HEAD commit subject line) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-branch",
        action="store_true",
        help="Include git_branch (current branch name) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-remote",
        action="store_true",
        help="Include git_remote (origin URL) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-dirty",
        action="store_true",
        help="Include git_dirty (clean|dirty|unknown) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-toplevel",
        action="store_true",
        help="Include git_toplevel (git --show-toplevel path) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-repo-name",
        action="store_true",
        help="Include git_repo_name (basename of git_toplevel) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-git-worktree-name",
        action="store_true",
        help="Include git_worktree_name (basename of current working directory) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-argv",
        action="store_true",
        help="Include argv (CLI invocation) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-argv-tokens",
        action="store_true",
        help="Include argv_tokens (CLI invocation token array) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-argv-sha256",
        action="store_true",
        help="Include argv_sha256 (hash of CLI invocation tokens) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-argv-count",
        action="store_true",
        help="Include argv_count (number of CLI invocation tokens) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--show-preset-meta-include-preset-file-sha256",
        action="store_true",
        help="Include preset_file_sha256 (hash of resolved --preset-file bytes) in --show-preset text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets from --preset-file and exit",
    )
    parser.add_argument(
        "--list-sort-aliases",
        action="store_true",
        help="List canonical/alias mappings for --list-presets-sort and exit",
    )
    parser.add_argument(
        "--list-sort-aliases-format",
        choices=(
            "aliases-json",
            "grouped-json",
            "aliases-tsv",
            "grouped-tsv",
            "aliases-tsv-rows",
            "grouped-tsv-rows",
            "names",
            "canonical-names",
            "names-json",
            "canonical-names-json",
            "aj",
            "gj",
            "at",
            "gt",
            "atr",
            "gtr",
            "n",
            "cn",
            "nj",
            "cnj",
        ),
        default="aliases-json",
        help=(
            "Output format for --list-sort-aliases: aliases-json (default, alias->canonical), "
            "grouped-json (canonical->[aliases]), aliases-tsv/grouped-tsv (with header), "
            "aliases-tsv-rows/grouped-tsv-rows (headerless rows), names (alias-only list), "
            "canonical-names (canonical-key-only list), names-json, or canonical-names-json. "
            "Shorthand aliases: aj|gj|at|gt|atr|gtr|n|cn|nj|cnj."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-name-contains",
        default=None,
        help=(
            "Optional substring filter for --list-sort-aliases; "
            "matches either alias name or canonical sort key."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-name-not-contains",
        default=None,
        help=(
            "Optional exclusion substring filter for --list-sort-aliases; "
            "drops aliases/canonical keys containing this value after include filtering."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-case-sensitive",
        action="store_true",
        help=(
            "Treat --list-sort-aliases-name-contains and --list-sort-aliases-name-not-contains matching as case-sensitive "
            "(default: case-insensitive)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-name-not-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="contains",
        help=(
            "Match mode for --list-sort-aliases-name-not-contains: contains|prefix|exact "
            "(or shorthand c|p|e; default: contains; case-insensitive unless --list-sort-aliases-case-sensitive)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-limit",
        type=int,
        default=None,
        help="Optional max number of alias mappings to emit after filtering",
    )
    parser.add_argument(
        "--list-sort-aliases-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="contains",
        help=(
            "Match mode for --list-sort-aliases-name-contains: contains|prefix|exact "
            "(or shorthand c|p|e; default: contains; case-insensitive unless --list-sort-aliases-case-sensitive)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-match-field",
        choices=("both", "alias", "canonical", "b", "a", "c"),
        default="both",
        help=(
            "Field scope for --list-sort-aliases-name-contains matching: both (default), "
            "alias only, or canonical only (or shorthand b|a|c)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size",
        type=int,
        default=1,
        help=(
            "Optional canonical family-size floor applied after text filtering; "
            "keeps only aliases whose canonical group has at least N aliases (default: 1)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size",
        type=int,
        default=None,
        help=(
            "Optional canonical family-size ceiling applied after text filtering; "
            "keeps only aliases whose canonical group has at most N aliases (default: no ceiling)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size-global",
        type=int,
        default=1,
        help=(
            "Optional global canonical family-size floor based on the full alias universe; "
            "keeps only aliases whose canonical family has at least N total aliases globally (default: 1)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size-global",
        type=int,
        default=None,
        help=(
            "Optional global canonical family-size ceiling based on the full alias universe; "
            "keeps only aliases whose canonical family has at most N total aliases globally (default: no ceiling)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-share-pct-global",
        type=float,
        default=0.0,
        help=(
            "Optional global canonical family share floor (0~100). "
            "Filters aliases whose canonical family share of the full alias universe is below this threshold."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-share-pct-global",
        type=float,
        default=100.0,
        help=(
            "Optional global canonical family share ceiling (0~100). "
            "Filters aliases whose canonical family share of the full alias universe is above this threshold."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-share-pct",
        type=float,
        default=0.0,
        help=(
            "Optional local canonical family share floor (0~100). "
            "Applied after text/global/group-size filtering, based on the currently filtered alias subset."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-share-pct",
        type=float,
        default=100.0,
        help=(
            "Optional local canonical family share ceiling (0~100). "
            "Applied after text/global/group-size filtering, based on the currently filtered alias subset."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-share-delta-pct",
        type=float,
        default=-100.0,
        help=(
            "Optional signed local-global canonical family share delta floor (-100~100). "
            "Applied after local share filtering using (local_share_pct - global_share_pct)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-share-delta-pct",
        type=float,
        default=100.0,
        help=(
            "Optional signed local-global canonical family share delta ceiling (-100~100). "
            "Applied after local share filtering using (local_share_pct - global_share_pct)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-share-delta-abs-pct",
        type=float,
        default=0.0,
        help=(
            "Optional absolute local-global canonical family share delta floor (0~100). "
            "Applied after signed delta filtering using abs(local_share_pct - global_share_pct)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-share-delta-abs-pct",
        type=float,
        default=100.0,
        help=(
            "Optional absolute local-global canonical family share delta ceiling (0~100). "
            "Applied after signed delta filtering using abs(local_share_pct - global_share_pct)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size-delta",
        type=int,
        default=-999999,
        help=(
            "Optional signed local-global canonical family size delta floor. "
            "Applied after share-delta filtering using (local_group_size - global_group_size)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size-delta",
        type=int,
        default=999999,
        help=(
            "Optional signed local-global canonical family size delta ceiling. "
            "Applied after share-delta filtering using (local_group_size - global_group_size)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size-delta-abs",
        type=int,
        default=0,
        help=(
            "Optional absolute local-global canonical family size delta floor (>=0). "
            "Applied after signed size-delta filtering using abs(local_group_size - global_group_size)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size-delta-abs",
        type=int,
        default=999999,
        help=(
            "Optional absolute local-global canonical family size delta ceiling (>=0). "
            "Applied after signed size-delta filtering using abs(local_group_size - global_group_size)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size-delta-pct",
        type=float,
        default=-100.0,
        help=(
            "Optional signed local-global canonical family size delta %% floor (-100~100). "
            "Applied after absolute size-delta filtering using ((local_group_size-global_group_size)/global_group_size)*100."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size-delta-pct",
        type=float,
        default=100.0,
        help=(
            "Optional signed local-global canonical family size delta %% ceiling (-100~100). "
            "Applied after absolute size-delta filtering using ((local_group_size-global_group_size)/global_group_size)*100."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-min-group-size-delta-abs-pct",
        type=float,
        default=0.0,
        help=(
            "Optional absolute local-global canonical family size delta %% floor (0~100). "
            "Applied after signed size-delta%% filtering using abs((local_group_size-global_group_size)/global_group_size*100)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-max-group-size-delta-abs-pct",
        type=float,
        default=100.0,
        help=(
            "Optional absolute local-global canonical family size delta %% ceiling (0~100). "
            "Applied after signed size-delta%% filtering using abs((local_group_size-global_group_size)/global_group_size*100)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-sort",
        choices=(
            "alias",
            "alias-desc",
            "canonical",
            "canonical-desc",
            "group-size",
            "group-size-desc",
            "group-share-pct",
            "group-share-pct-desc",
            "group-size-global",
            "group-size-global-desc",
            "group-share-pct-global",
            "group-share-pct-global-desc",
            "group-share-delta",
            "group-share-delta-desc",
            "group-share-delta-abs",
            "group-share-delta-abs-desc",
            "group-size-delta",
            "group-size-delta-desc",
            "group-size-delta-abs",
            "group-size-delta-abs-desc",
            "group-size-delta-pct",
            "group-size-delta-pct-desc",
            "group-size-delta-pct-abs",
            "group-size-delta-pct-abs-desc",
            "skew",
            "skew-desc",
            "skew-asc",
            "skew-share",
            "skew-share-desc",
            "skew-share-asc",
            "skew-count",
            "skew-count-desc",
            "skew-count-asc",
            "skew-size",
            "skew-size-desc",
            "skew-size-asc",
            "skew-pct",
            "skew-pct-desc",
            "skew-pct-asc",
            "skew-size-pct",
            "skew-size-pct-desc",
            "skew-size-pct-asc",
        ),
        default="alias",
        help=(
            "Sort mode for --list-sort-aliases output: alias/alias-desc (by alias key), "
            "canonical/canonical-desc (by canonical key, tie-breaking by alias), "
            "group-size/group-size-desc (by local canonical family size), "
            "group-share-pct/group-share-pct-desc (by local canonical family share %% values), "
            "group-size-global/group-size-global-desc (by global canonical family size), "
            "group-share-pct-global/group-share-pct-global-desc (by global canonical family share %% values), "
            "group-share-delta/group-share-delta-desc (by signed local-global canonical family share %% delta), "
            "group-share-delta-abs/group-share-delta-abs-desc (by absolute local-global canonical family share %% delta), "
            "group-size-delta/group-size-delta-desc (by signed local-global canonical family size delta), "
            "group-size-delta-abs/group-size-delta-abs-desc (by absolute local-global canonical family size delta), "
            "group-size-delta-pct/group-size-delta-pct-desc (by signed local-global canonical family size delta %% relative to global family size), or "
            "group-size-delta-pct-abs/group-size-delta-pct-abs-desc (by absolute local-global canonical family size delta %% relative to global family size). "
            "Shorthand aliases: skew[/desc|/asc] (=skew-share), skew-count[/desc|/asc] (=skew-size), "
            "skew-pct[/desc|/asc] (=skew-size-pct), plus skew-share/skew-size/skew-size-pct families."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-tsv-with-meta",
        action="store_true",
        help=(
            "Append meta footer with filter/sort counters to aliases-tsv/grouped-tsv output "
            "(including headerless aliases-tsv-rows/grouped-tsv-rows)."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-names-with-meta",
        action="store_true",
        help=(
            "Append the same meta footer to names/canonical-names output for parser-friendly "
            "count/filter/sort provenance tracking."
        ),
    )
    parser.add_argument(
        "--list-sort-aliases-tsv-meta-format",
        choices=("text", "json"),
        default="text",
        help="Meta footer format for --list-sort-aliases-tsv-with-meta (default: text)",
    )
    parser.add_argument(
        "--list-sort-aliases-tsv-meta-json-schema-version",
        default=SORT_ALIASES_TSV_META_JSON_SCHEMA_VERSION,
        help=(
            "Wrapper schema_version for JSON meta footer in --list-sort-aliases TSV output "
            "(must match ^v[1-9][0-9]*$, default: v1)."
        ),
    )
    parser.add_argument(
        "--list-presets-format",
        choices=("names", "json", "resolved-json", "summary", "summary-tsv"),
        default="names",
        help="Output format for --list-presets (default: names)",
    )
    parser.add_argument(
        "--list-presets-tag",
        default=None,
        help="Optional tag filter for --list-presets (comma-separated, case-insensitive by default)",
    )
    parser.add_argument(
        "--list-presets-tag-case-sensitive",
        action="store_true",
        help=(
            "Enable case-sensitive matching for --list-presets-tag and "
            "--list-presets-tag-not-contains (default: case-insensitive)."
        ),
    )
    parser.add_argument(
        "--list-presets-tag-match",
        choices=("all", "any", "a", "o"),
        default="all",
        help=(
            "Tag match mode for --list-presets-tag: all (default, AND) or any (OR); "
            "shorthand aliases: a=all, o=any"
        ),
    )
    parser.add_argument(
        "--list-presets-tag-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="exact",
        help=(
            "Match mode for --list-presets-tag: exact (default), contains, prefix; "
            "shorthand aliases: c=contains, p=prefix, e=exact"
        ),
    )
    parser.add_argument(
        "--list-presets-tag-not-contains",
        default=None,
        help=(
            "Optional exclusion tag filter for --list-presets (comma-separated, case-insensitive by default; "
            "combine with --list-presets-tag-not-match)."
        ),
    )
    parser.add_argument(
        "--list-presets-tag-not-match",
        choices=("all", "any", "a", "o"),
        default="any",
        help=(
            "Tag exclusion match mode for --list-presets-tag-not-contains: any (default) or all; "
            "shorthand aliases: a=all, o=any"
        ),
    )
    parser.add_argument(
        "--list-presets-tag-not-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="exact",
        help=(
            "Match mode for --list-presets-tag-not-contains: exact (default), contains, prefix; "
            "shorthand aliases: c=contains, p=prefix, e=exact"
        ),
    )
    parser.add_argument(
        "--list-presets-name-contains",
        default=None,
        help="Optional case-insensitive substring filter for preset names in --list-presets",
    )
    parser.add_argument(
        "--list-presets-name-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="contains",
        help=(
            "Match mode for --list-presets-name-contains: contains (default), prefix, exact; "
            "shorthand aliases: c=contains, p=prefix, e=exact"
        ),
    )
    parser.add_argument(
        "--list-presets-name-not-contains",
        default=None,
        help=(
            "Optional exclusion filter for preset names in --list-presets "
            "(case-insensitive by default; combine with --list-presets-name-not-filter-mode)."
        ),
    )
    parser.add_argument(
        "--list-presets-name-not-filter-mode",
        choices=("contains", "prefix", "exact", "c", "p", "e"),
        default="contains",
        help=(
            "Match mode for --list-presets-name-not-contains: contains (default), prefix, exact; "
            "shorthand aliases: c=contains, p=prefix, e=exact"
        ),
    )
    parser.add_argument(
        "--list-presets-name-case-sensitive",
        action="store_true",
        help=(
            "Enable case-sensitive matching for --list-presets-name-contains and "
            "--list-presets-name-not-contains (default: case-insensitive)."
        ),
    )
    parser.add_argument(
        "--list-presets-limit",
        type=int,
        default=None,
        help="Optional max number of presets to emit after filtering",
    )
    parser.add_argument(
        "--list-presets-sort",
        default="name",
        help=(
            "Sort mode for filtered preset emission: "
            "name (default), name-desc (descending), max-total-runs (ascending; capped presets first, 0/uncapped last), "
            "max-total-runs-desc (descending; 0/uncapped first), total-cap (alias of max-total-runs), "
            "total-cap-desc (alias of max-total-runs-desc), repeats (ascending), "
            "repeats-desc (descending), model-count (ascending), model-count-desc (descending), "
            "prompt-condition-count (ascending), prompt-condition-count-desc (descending), "
            "max-runs-per-model (ascending; capped presets first, 0/uncapped last), "
            "max-runs-per-model-desc (descending; 0/uncapped first), "
            "per-model-cap (alias of max-runs-per-model), "
            "per-model-cap-desc (alias of max-runs-per-model-desc), "
            "max-runs-per-prompt-condition (ascending; capped presets first, 0/uncapped last), "
            "max-runs-per-prompt-condition-desc (descending; 0/uncapped first), "
            "per-prompt-cap (alias of max-runs-per-prompt-condition), "
            "per-prompt-cap-desc (alias of max-runs-per-prompt-condition-desc), "
            "max-runs-per-task (ascending; capped presets first, 0/uncapped last), "
            "max-runs-per-task-desc (descending; 0/uncapped first), "
            "per-task-cap (alias of max-runs-per-task), "
            "per-task-cap-desc (alias of max-runs-per-task-desc), "
            "task-cap (alias of max-runs-per-task), "
            "task-cap-desc (alias of max-runs-per-task-desc), "
            "max-runs-per-task-model (ascending; capped presets first, 0/uncapped last), "
            "max-runs-per-task-model-desc (descending; 0/uncapped first), "
            "per-task-model-cap (alias of max-runs-per-task-model), "
            "per-task-model-cap-desc (alias of max-runs-per-task-model-desc), "
            "task-model-cap (alias of max-runs-per-task-model), "
            "task-model-cap-desc (alias of max-runs-per-task-model-desc), "
            "max-runs-per-task-prompt-condition (ascending; capped presets first, 0/uncapped last), "
            "max-runs-per-task-prompt-condition-desc (descending; 0/uncapped first), "
            "per-task-prompt-cap (alias of max-runs-per-task-prompt-condition), "
            "per-task-prompt-cap-desc (alias of max-runs-per-task-prompt-condition-desc), "
            "per-task-condition-cap (alias of max-runs-per-task-prompt-condition), "
            "per-task-condition-cap-desc (alias of max-runs-per-task-prompt-condition-desc), "
            "task-prompt-cap (alias of max-runs-per-task-prompt-condition), "
            "task-prompt-cap-desc (alias of max-runs-per-task-prompt-condition-desc), "
            "task-condition-cap (alias of max-runs-per-task-prompt-condition), "
            "task-condition-cap-desc (alias of max-runs-per-task-prompt-condition-desc), "
            "description-length (ascending normalized description length), description-length-desc (descending), "
            "tag-count (ascending normalized unique tag count), tag-count-desc (descending), "
            "cheap-first-tag (presets tagged cheap-first first), cheap-first-tag-desc "
            "(presets without cheap-first tag first), cheap-first (alias of cheap-first-tag), "
            "cheap-first-desc (alias of cheap-first-tag-desc), cheap-first-total-cap "
            "(cheap-first tagged presets first, then max_total_runs ascending with uncapped last), "
            "cheap-total-cap (alias of cheap-first-total-cap), "
            "cheap-first-total-cap-desc (cheap-first-untagged presets first, then max_total_runs descending with uncapped first), "
            "cheap-total-cap-desc (alias of cheap-first-total-cap-desc), "
            "fair-allocation-total-cap (fair_model_allocation=true presets first, then max_total_runs ascending with uncapped last), "
            "fair-total-cap (alias of fair-allocation-total-cap), "
            "fair-cap (alias of fair-allocation-total-cap), "
            "fair-allocation-total-cap-desc (fair_model_allocation=false presets first, then max_total_runs descending with uncapped first), "
            "fair-total-cap-desc (alias of fair-allocation-total-cap-desc), "
            "fair-cap-desc (alias of fair-allocation-total-cap-desc), "
            "cost-priority (cheap-first tag first, then max_total_runs asc with uncapped last, then max_runs_per_model asc with uncapped last), "
            "cost (alias of cost-priority), "
            "cost-priority-desc (cheap-first-untagged first, then max_total_runs desc with uncapped first, then max_runs_per_model desc with uncapped first), "
            "cost-desc (alias of cost-priority-desc), "
            "cost-priority-prompt (cheap-first tag first, then max_total_runs asc with uncapped last, then max_runs_per_prompt_condition asc with uncapped last), "
            "cost-prompt (alias of cost-priority-prompt), "
            "cost-condition (alias of cost-priority-prompt), "
            "cc (alias of cost-priority-prompt), "
            "cost-priority-prompt-desc (cheap-first-untagged first, then max_total_runs desc with uncapped first, then max_runs_per_prompt_condition desc with uncapped first), "
            "cost-prompt-desc (alias of cost-priority-prompt-desc), "
            "cost-condition-desc (alias of cost-priority-prompt-desc), "
            "ccd (alias of cost-priority-prompt-desc), "
            "fair-model-allocation (presets with fair_model_allocation=true first), "
            "fair-model-allocation-desc (presets with fair_model_allocation=false first), "
            "fair-allocation (alias of fair-model-allocation), fair-allocation-desc (alias of fair-model-allocation-desc), "
            "tag:<name> (presets containing that tag first), tag:<name>-desc (presets without that tag first), "
            "or shorthand t:<name>/t:<name>-desc."
        ),
    )
    parser.add_argument(
        "--list-presets-with-meta",
        action="store_true",
        help=(
            "Emit filtered/emitted/truncated metadata for list-presets outputs; "
            "text formats append a footer and json/resolved-json add a top-level meta object."
        ),
    )
    parser.add_argument(
        "--list-presets-meta-schema-id",
        default=PRESET_LIST_TEXT_META_SCHEMA,
        help=(
            "Schema id for --list-presets text meta footer (default: planner_preset_list_meta.v1)"
        ),
    )
    parser.add_argument(
        "--list-presets-meta-include-filters",
        action="store_true",
        help=(
            "Include active filter context in --list-presets text meta footer "
            "(tag/tag_not/name_contains/name_not_contains/limit/tag_match/tag_not_match/"
            "tag_filter_mode/tag_not_filter_mode)."
        ),
    )
    parser.add_argument(
        "--list-presets-meta-format",
        choices=("text", "json"),
        default="text",
        help="Meta footer format for --list-presets-with-meta (default: text)",
    )
    parser.add_argument(
        "--list-presets-meta-profile",
        choices=("minimal", "privacy-safe", "ci-safe", "safe-debug", "debug"),
        default=None,
        help=(
            "Optional profile for --list-presets meta footer fields: "
            "minimal (default behavior), privacy-safe (hash-first provenance without cwd/raw argv), "
            "ci-safe (stable CI/repro fields without volatile host/time metadata), "
            "safe-debug (debug fields without raw argv/tokens), or debug (full debug fields including raw argv/tokens)."
        ),
    )
    parser.add_argument(
        "--list-presets-meta-json-schema-version",
        default=PRESET_TEXT_META_JSON_SCHEMA_VERSION,
        help=(
            "Schema version for --list-presets meta JSON envelope "
            "(default: v1; only used when --list-presets-meta-format=json)"
        ),
    )
    parser.add_argument(
        "--list-presets-meta-include-generated-at",
        action="store_true",
        help="Include generated_at_utc in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-cwd",
        action="store_true",
        help="Include cwd in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-python-version",
        action="store_true",
        help="Include python_version in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-pid",
        action="store_true",
        help="Include pid in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-hostname",
        action="store_true",
        help="Include hostname in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-head",
        action="store_true",
        help="Include git_head (short HEAD commit) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-head-date-utc",
        action="store_true",
        help="Include git_head_date_utc (HEAD commit date, ISO-8601 UTC offset) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-head-subject",
        action="store_true",
        help="Include git_head_subject (HEAD commit subject line) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-branch",
        action="store_true",
        help="Include git_branch (current branch name) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-remote",
        action="store_true",
        help="Include git_remote (origin URL) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-dirty",
        action="store_true",
        help="Include git_dirty (clean|dirty|unknown) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-toplevel",
        action="store_true",
        help="Include git_toplevel (git --show-toplevel path) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-repo-name",
        action="store_true",
        help="Include git_repo_name (basename of git_toplevel) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-git-worktree-name",
        action="store_true",
        help="Include git_worktree_name (basename of current working directory) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-argv",
        action="store_true",
        help="Include argv (CLI invocation) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-argv-tokens",
        action="store_true",
        help="Include argv_tokens (CLI invocation token array) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-argv-sha256",
        action="store_true",
        help="Include argv_sha256 (hash of CLI invocation tokens) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-argv-count",
        action="store_true",
        help="Include argv_count (number of CLI invocation tokens) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--list-presets-meta-include-preset-file-sha256",
        action="store_true",
        help="Include preset_file_sha256 (hash of resolved --preset-file bytes) in --list-presets text/json meta footer.",
    )
    parser.add_argument(
        "--summary-tsv-with-schema-header",
        action="store_true",
        help=(
            "Prefix summary-tsv output with '# schema=<id>' comment for parser-friendly format versioning"
        ),
    )
    parser.add_argument(
        "--summary-tsv-description",
        choices=("preview", "full"),
        default="preview",
        help="summary-tsv description column mode: preview (default) or full",
    )
    parser.add_argument(
        "--summary-tsv-description-max-len",
        type=int,
        default=None,
        help=(
            "Optional soft cap for summary-tsv full description length (>=4). "
            "Ignored in preview mode."
        ),
    )
    parser.add_argument(
        "--summary-tsv-with-schema-column",
        action="store_true",
        help=(
            "Append 'schema' column to each summary-tsv row for parser-friendly inline format versioning"
        ),
    )
    parser.add_argument(
        "--summary-tsv-schema-id",
        default=PRESET_SUMMARY_TSV_SCHEMA,
        help=(
            "Schema id for summary-tsv outputs (default: planner_preset_summary_tsv.v2)"
        ),
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        default=DEFAULT_PRESET_FILE,
        help=f"Preset file path (default: {DEFAULT_PRESET_FILE})",
    )
    parser.add_argument("--models", default=None, help="Comma-separated model ids")
    parser.add_argument(
        "--prompt-conditions",
        default=None,
        help="Comma-separated prompt condition labels (e.g. base,strict,few-shot)",
    )
    parser.add_argument("--repeats", type=int, default=None, help="Repeat count per task/condition/model")
    parser.add_argument("--max-total-runs", type=int, default=None, help="Optional hard cap for total planned runs (0 disables cap)")
    parser.add_argument(
        "--max-total-runs-mode",
        choices=("fail", "cap"),
        default=None,
        help="Behavior when --max-total-runs is set: fail (default) or cap plan length",
    )
    parser.add_argument("--max-runs-per-model", type=int, default=None, help="Optional per-model cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-prompt-condition", type=int, default=None, help="Optional per-prompt-condition cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task", type=int, default=None, help="Optional per-task cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task-model", type=int, default=None, help="Optional per-task×model cap for planned runs (0 disables cap)")
    parser.add_argument("--max-runs-per-task-prompt-condition", type=int, default=None, help="Optional per-task×prompt-condition cap for planned runs (0 disables cap)")
    parser.add_argument(
        "--cheap-first",
        action="store_true",
        default=None,
        help="Order model runs using a cheap-first heuristic before expanding matrix",
    )
    parser.add_argument(
        "--fair-model-allocation",
        action="store_true",
        default=None,
        help="Rotate model iteration order per expansion step to reduce cap-induced model skew",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <task_set>.batch-plan.json)",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()

        schema_id = str(args.summary_tsv_schema_id).strip()
        if not PRESET_SUMMARY_TSV_SCHEMA_PATTERN.match(schema_id):
            raise ValueError(
                "--summary-tsv-schema-id must match planner_preset_summary_tsv.vN (N>=1)"
            )
        list_meta_schema_id = str(args.list_presets_meta_schema_id).strip()
        show_meta_schema_id = str(args.show_preset_meta_schema_id).strip()
        list_meta_json_schema_version = str(args.list_presets_meta_json_schema_version).strip()
        if not PRESET_TEXT_META_JSON_SCHEMA_VERSION_PATTERN.match(list_meta_json_schema_version):
            raise ValueError("--list-presets-meta-json-schema-version must match vN (N>=1)")
        show_meta_json_schema_version = str(args.show_preset_meta_json_schema_version).strip()
        if not PRESET_TEXT_META_JSON_SCHEMA_VERSION_PATTERN.match(show_meta_json_schema_version):
            raise ValueError("--show-preset-meta-json-schema-version must match vN (N>=1)")
        sort_aliases_meta_json_schema_version = str(args.list_sort_aliases_tsv_meta_json_schema_version).strip()
        if not SORT_ALIASES_TSV_META_JSON_SCHEMA_VERSION_PATTERN.match(sort_aliases_meta_json_schema_version):
            raise ValueError("--list-sort-aliases-tsv-meta-json-schema-version must match vN (N>=1)")
        if args.summary_tsv_description_max_len is not None and args.summary_tsv_description_max_len < 4:
            raise ValueError("--summary-tsv-description-max-len must be >= 4")

        _apply_show_meta_profile(args)
        _apply_list_meta_profile(args)

        list_meta_schema_id = _resolve_profile_schema_id(
            args.list_presets_meta_profile,
            list_meta_schema_id,
            PRESET_LIST_TEXT_META_SCHEMA,
        )
        show_meta_schema_id = _resolve_profile_schema_id(
            args.show_preset_meta_profile,
            show_meta_schema_id,
            PRESET_SHOW_TEXT_META_SCHEMA,
        )
        if not PRESET_LIST_TEXT_META_SCHEMA_PATTERN.match(list_meta_schema_id):
            raise ValueError(
                "--list-presets-meta-schema-id must match planner_preset_list_meta.vN (N>=1)"
            )
        if not PRESET_SHOW_TEXT_META_SCHEMA_PATTERN.match(show_meta_schema_id):
            raise ValueError(
                "--show-preset-meta-schema-id must match planner_preset_show_meta.vN (N>=1)"
            )

        if args.show_preset:
            preset = load_preset_config(args.preset_file, args.show_preset)
            resolved = resolve_preset_with_defaults(preset)
            # Preview final values after optional CLI overrides, mirroring plan-generation precedence.
            if args.models is not None:
                resolved["models"] = args.models
            if args.prompt_conditions is not None:
                resolved["prompt_conditions"] = args.prompt_conditions
            if args.repeats is not None:
                resolved["repeats"] = args.repeats
            if args.cheap_first is not None:
                resolved["cheap_first"] = bool(args.cheap_first)
            if args.fair_model_allocation is not None:
                resolved["fair_model_allocation"] = bool(args.fair_model_allocation)
            if args.max_total_runs is not None:
                resolved["max_total_runs"] = args.max_total_runs
            if args.max_total_runs_mode is not None:
                resolved["max_total_runs_mode"] = args.max_total_runs_mode
            if args.max_runs_per_model is not None:
                resolved["max_runs_per_model"] = args.max_runs_per_model
            if args.max_runs_per_prompt_condition is not None:
                resolved["max_runs_per_prompt_condition"] = args.max_runs_per_prompt_condition
            if args.max_runs_per_task is not None:
                resolved["max_runs_per_task"] = args.max_runs_per_task
            if args.max_runs_per_task_model is not None:
                resolved["max_runs_per_task_model"] = args.max_runs_per_task_model
            if args.max_runs_per_task_prompt_condition is not None:
                resolved["max_runs_per_task_prompt_condition"] = args.max_runs_per_task_prompt_condition

            active_overrides: list[str] = []
            override_checks = [
                ("models", args.models),
                ("prompt_conditions", args.prompt_conditions),
                ("repeats", args.repeats),
                ("cheap_first", args.cheap_first),
                ("fair_model_allocation", args.fair_model_allocation),
                ("max_total_runs", args.max_total_runs),
                ("max_total_runs_mode", args.max_total_runs_mode),
                ("max_runs_per_model", args.max_runs_per_model),
                ("max_runs_per_prompt_condition", args.max_runs_per_prompt_condition),
                ("max_runs_per_task", args.max_runs_per_task),
                ("max_runs_per_task_model", args.max_runs_per_task_model),
                ("max_runs_per_task_prompt_condition", args.max_runs_per_task_prompt_condition),
            ]
            for key, value in override_checks:
                if value is not None:
                    active_overrides.append(key)

            if resolved["repeats"] < 1:
                raise ValueError("--repeats must be >= 1")
            if resolved["max_total_runs"] < 0:
                raise ValueError("--max-total-runs must be >= 0")
            if resolved["max_total_runs_mode"] not in {"fail", "cap"}:
                raise ValueError("--max-total-runs-mode must be one of: fail, cap")
            if resolved["max_runs_per_model"] < 0:
                raise ValueError("--max-runs-per-model must be >= 0")
            if resolved["max_runs_per_prompt_condition"] < 0:
                raise ValueError("--max-runs-per-prompt-condition must be >= 0")
            if resolved["max_runs_per_task"] < 0:
                raise ValueError("--max-runs-per-task must be >= 0")
            if resolved["max_runs_per_task_model"] < 0:
                raise ValueError("--max-runs-per-task-model must be >= 0")
            if resolved["max_runs_per_task_prompt_condition"] < 0:
                raise ValueError("--max-runs-per-task-prompt-condition must be >= 0")

            show_output_columns = _resolve_preset_output_columns(
                args.show_preset_format,
                with_schema_column=args.summary_tsv_with_schema_column,
            )
            payload = {
                "schema_version": "v1",
                "preset_file": str(args.preset_file),
                "preset": args.show_preset,
                "output_format": args.show_preset_format,
                "output_transport": _resolve_preset_output_transport(args.show_preset_format),
                "output_has_header": _resolve_preset_output_has_header(args.show_preset_format),
                "output_delimiter": _resolve_preset_output_delimiter(args.show_preset_format),
                "output_field_count": len(show_output_columns),
                "output_column_count": _resolve_preset_output_column_count(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_columns": show_output_columns,
                "output_columns_sha256": _resolve_preset_output_columns_sha256(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_schema": PRESET_OUTPUT_SHAPE_SCHEMA,
                "output_shape_fields": _resolve_preset_output_shape_fields(),
                "output_shape_payload": _resolve_preset_output_shape_payload(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_payload_json": _resolve_preset_output_shape_payload_json(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_payload_json_bytes": _resolve_preset_output_shape_payload_json_bytes(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_payload_json_sha256": _resolve_preset_output_shape_payload_json_sha256(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_payload_json_sha256_algo": _resolve_preset_output_shape_payload_json_sha256_algo(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_tuple": _resolve_preset_output_shape_tuple(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_tuple_bytes": _resolve_preset_output_shape_tuple_bytes(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_sha256": _resolve_preset_output_shape_sha256(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "output_shape_sha256_algo": _resolve_preset_output_shape_sha256_algo(
                    args.show_preset_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                ),
                "resolved": resolved,
            }
            show_meta_extra_fields: dict[str, Any] | None = None
            if args.show_preset_meta_include_overrides:
                show_meta_extra_fields = {
                    "override_count": str(len(active_overrides)),
                    "overrides": ",".join(active_overrides) if active_overrides else "none",
                }
            if args.show_preset_meta_include_generated_at:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["generated_at_utc"] = _utc_now_iso()
            if args.show_preset_meta_include_cwd:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["cwd"] = os.getcwd()
            if args.show_preset_meta_include_python_version:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["python_version"] = sys.version.split()[0]
            if args.show_preset_meta_include_pid:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["pid"] = str(os.getpid())
            if args.show_preset_meta_include_hostname:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["hostname"] = socket.gethostname()
            if args.show_preset_meta_include_git_head:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_head"] = _git_head_short(cwd=os.getcwd())
            if args.show_preset_meta_include_git_head_date_utc:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_head_date_utc"] = _git_head_commit_date_utc(cwd=os.getcwd())
            if args.show_preset_meta_include_git_head_subject:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_head_subject"] = _git_head_subject(cwd=os.getcwd())
            if args.show_preset_meta_include_git_branch:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_branch"] = _git_branch_name(cwd=os.getcwd())
            if args.show_preset_meta_include_git_remote:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_remote"] = _git_remote_origin_url(cwd=os.getcwd())
            if args.show_preset_meta_include_git_dirty:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_dirty"] = _git_dirty_state(cwd=os.getcwd())
            if args.show_preset_meta_include_git_toplevel:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_toplevel"] = _git_toplevel(cwd=os.getcwd())
            if args.show_preset_meta_include_git_repo_name:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_repo_name"] = _git_repo_name(cwd=os.getcwd())
            if args.show_preset_meta_include_git_worktree_name:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["git_worktree_name"] = _git_worktree_name(cwd=os.getcwd())
            if args.show_preset_meta_include_argv:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["argv"] = " ".join(sys.argv)
            if args.show_preset_meta_include_argv_tokens:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                if args.show_preset_meta_format == "json":
                    show_meta_extra_fields["argv_tokens"] = list(sys.argv)
                else:
                    show_meta_extra_fields["argv_tokens"] = json.dumps(
                        list(sys.argv), ensure_ascii=False, separators=(",", ":")
                    )
            if args.show_preset_meta_include_argv_sha256:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["argv_sha256"] = hashlib.sha256(
                    "\0".join(sys.argv).encode("utf-8")
                ).hexdigest()
            if args.show_preset_meta_include_argv_count:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["argv_count"] = len(sys.argv)
            if args.show_preset_meta_include_preset_file_sha256:
                if show_meta_extra_fields is None:
                    show_meta_extra_fields = {}
                show_meta_extra_fields["preset_file_sha256"] = _file_sha256(args.preset_file)
            show_output_columns = _resolve_preset_output_columns(
                args.show_preset_format,
                with_schema_column=args.summary_tsv_with_schema_column,
            )
            show_meta_payload = _compose_meta_payload(
                {
                    "schema": show_meta_schema_id,
                    "filtered_count": 1,
                    "emitted_count": 1,
                    "output_record_count": 1,
                    "output_is_empty": False,
                    "output_is_single_record": True,
                    "output_has_multiple_records": False,
                    "output_truncated_count": 0,
                    "truncated": False,
                    "preset": args.show_preset,
                    "format": args.show_preset_format,
                    "output_format": args.show_preset_format,
                    "output_transport": _resolve_preset_output_transport(args.show_preset_format),
                    "output_has_header": _resolve_preset_output_has_header(args.show_preset_format),
                    "output_delimiter": _resolve_preset_output_delimiter(args.show_preset_format),
                    "output_field_count": len(show_output_columns),
                    "output_column_count": _resolve_preset_output_column_count(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_columns": show_output_columns,
                    "output_columns_sha256": _resolve_preset_output_columns_sha256(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_schema": PRESET_OUTPUT_SHAPE_SCHEMA,
                    "output_shape_fields": _resolve_preset_output_shape_fields(),
                    "output_shape_payload": _resolve_preset_output_shape_payload(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json": _resolve_preset_output_shape_payload_json(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_bytes": _resolve_preset_output_shape_payload_json_bytes(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256": _resolve_preset_output_shape_payload_json_sha256(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256_algo": _resolve_preset_output_shape_payload_json_sha256_algo(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple": _resolve_preset_output_shape_tuple(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple_bytes": _resolve_preset_output_shape_tuple_bytes(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256": _resolve_preset_output_shape_sha256(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256_algo": _resolve_preset_output_shape_sha256_algo(
                        args.show_preset_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "preset_file": str(args.preset_file),
                },
                show_meta_extra_fields,
            )

            if args.show_preset_format == "summary":
                print(_format_preset_summary_line(args.show_preset, resolved))
                if args.show_preset_with_meta:
                    _emit_show_preset_text_meta(
                        args.show_preset,
                        args.show_preset_format,
                        args.preset_file,
                        schema_id=show_meta_schema_id,
                        extra_fields=show_meta_extra_fields,
                        meta_format=args.show_preset_meta_format,
                        json_schema_version=show_meta_json_schema_version,
                    )
                return 0
            if args.show_preset_format == "summary-tsv":
                _emit_preset_summary_tsv_header(
                    args.summary_tsv_with_schema_header,
                    args.summary_tsv_description,
                    args.summary_tsv_with_schema_column,
                    schema_id,
                )
                print(
                    _format_preset_summary_tsv_row(
                        args.show_preset,
                        resolved,
                        description_mode=args.summary_tsv_description,
                        with_schema_column=args.summary_tsv_with_schema_column,
                        schema_id=schema_id,
                        description_max_len=args.summary_tsv_description_max_len,
                    )
                )
                if args.show_preset_with_meta:
                    _emit_show_preset_text_meta(
                        args.show_preset,
                        args.show_preset_format,
                        args.preset_file,
                        schema_id=show_meta_schema_id,
                        extra_fields=show_meta_extra_fields,
                        meta_format=args.show_preset_meta_format,
                        json_schema_version=show_meta_json_schema_version,
                    )
                return 0
            if args.show_preset_with_meta:
                payload["meta"] = show_meta_payload
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.list_sort_aliases:
            resolved_list_sort_aliases_format = _resolve_list_sort_aliases_format(args.list_sort_aliases_format)
            list_sort_aliases_format_requested = args.list_sort_aliases_format
            list_sort_aliases_format_alias_resolved = (
                resolved_list_sort_aliases_format != list_sort_aliases_format_requested
            )
            resolved_list_sort_aliases_sort = _resolve_list_sort_aliases_sort(args.list_sort_aliases_sort)
            list_sort_aliases_sort_requested = args.list_sort_aliases_sort
            list_sort_aliases_sort_alias_resolved = (
                resolved_list_sort_aliases_sort != list_sort_aliases_sort_requested
            )
            list_sort_aliases_sort_info = _describe_list_sort_aliases_sort_mode(
                resolved_list_sort_aliases_sort
            )
            resolved_list_sort_aliases_filter_mode = _resolve_filter_mode(args.list_sort_aliases_filter_mode)
            list_sort_aliases_filter_mode_requested = args.list_sort_aliases_filter_mode
            list_sort_aliases_filter_mode_alias_resolved = (
                resolved_list_sort_aliases_filter_mode != list_sort_aliases_filter_mode_requested
            )
            resolved_list_sort_aliases_name_not_filter_mode = _resolve_filter_mode(
                args.list_sort_aliases_name_not_filter_mode
            )
            list_sort_aliases_name_not_filter_mode_requested = args.list_sort_aliases_name_not_filter_mode
            list_sort_aliases_name_not_filter_mode_alias_resolved = (
                resolved_list_sort_aliases_name_not_filter_mode
                != list_sort_aliases_name_not_filter_mode_requested
            )
            resolved_list_sort_aliases_match_field = _resolve_match_field(args.list_sort_aliases_match_field)
            list_sort_aliases_match_field_requested = args.list_sort_aliases_match_field
            list_sort_aliases_match_field_alias_resolved = (
                resolved_list_sort_aliases_match_field != list_sort_aliases_match_field_requested
            )
            normalized_name_contains = _normalize_sort_alias_name_filter_value(
                args.list_sort_aliases_name_contains,
                case_sensitive=args.list_sort_aliases_case_sensitive,
            )
            normalized_name_not_contains = _normalize_sort_alias_name_filter_value(
                args.list_sort_aliases_name_not_contains,
                case_sensitive=args.list_sort_aliases_case_sensitive,
            )
            name_values = [] if normalized_name_contains is None else [normalized_name_contains]
            name_not_values = [] if normalized_name_not_contains is None else [normalized_name_not_contains]
            alias_map, filtered_count, truncated = _filter_sort_alias_map(
                args.list_sort_aliases_name_contains,
                args.list_sort_aliases_name_not_contains,
                args.list_sort_aliases_limit,
                resolved_list_sort_aliases_sort,
                resolved_list_sort_aliases_filter_mode,
                resolved_list_sort_aliases_name_not_filter_mode,
                resolved_list_sort_aliases_match_field,
                args.list_sort_aliases_min_group_size,
                args.list_sort_aliases_max_group_size,
                args.list_sort_aliases_min_group_size_global,
                args.list_sort_aliases_max_group_size_global,
                args.list_sort_aliases_min_group_share_pct_global,
                args.list_sort_aliases_max_group_share_pct_global,
                args.list_sort_aliases_min_group_share_pct,
                args.list_sort_aliases_max_group_share_pct,
                args.list_sort_aliases_min_group_share_delta_pct,
                args.list_sort_aliases_max_group_share_delta_pct,
                args.list_sort_aliases_min_group_share_delta_abs_pct,
                args.list_sort_aliases_max_group_share_delta_abs_pct,
                args.list_sort_aliases_min_group_size_delta,
                args.list_sort_aliases_max_group_size_delta,
                args.list_sort_aliases_min_group_size_delta_abs,
                args.list_sort_aliases_max_group_size_delta_abs,
                args.list_sort_aliases_min_group_size_delta_pct,
                args.list_sort_aliases_max_group_size_delta_pct,
                args.list_sort_aliases_min_group_size_delta_abs_pct,
                args.list_sort_aliases_max_group_size_delta_abs_pct,
                args.list_sort_aliases_case_sensitive,
            )
            grouped = _build_sort_alias_groups(alias_map)
            group_sizes, total_alias_count, group_share_pct = _compute_group_sizes_and_share_pct(alias_map)
            global_group_sizes, global_alias_count, global_group_share_pct = _compute_group_sizes_and_share_pct(
                PRESET_SORT_ALIAS_MAP
            )

            def build_sort_aliases_meta_footer() -> str:
                return _format_sort_aliases_tsv_meta(
                    output_format=resolved_list_sort_aliases_format,
                    output_format_requested=list_sort_aliases_format_requested,
                    output_format_alias_resolved=list_sort_aliases_format_alias_resolved,
                    filtered_count=filtered_count,
                    emitted_count=len(alias_map),
                    truncated=truncated,
                    name_contains=args.list_sort_aliases_name_contains,
                    name_not_contains=args.list_sort_aliases_name_not_contains,
                    name_values=name_values,
                    name_not_values=name_not_values,
                    filter_mode=resolved_list_sort_aliases_filter_mode,
                    filter_mode_requested=list_sort_aliases_filter_mode_requested,
                    filter_mode_alias_resolved=list_sort_aliases_filter_mode_alias_resolved,
                    name_not_filter_mode=resolved_list_sort_aliases_name_not_filter_mode,
                    name_not_filter_mode_requested=list_sort_aliases_name_not_filter_mode_requested,
                    name_not_filter_mode_alias_resolved=list_sort_aliases_name_not_filter_mode_alias_resolved,
                    match_field=resolved_list_sort_aliases_match_field,
                    match_field_requested=list_sort_aliases_match_field_requested,
                    match_field_alias_resolved=list_sort_aliases_match_field_alias_resolved,
                    case_sensitive=args.list_sort_aliases_case_sensitive,
                    limit=args.list_sort_aliases_limit,
                    sort_mode=resolved_list_sort_aliases_sort,
                    sort_requested=list_sort_aliases_sort_requested,
                    sort_alias_resolved=list_sort_aliases_sort_alias_resolved,
                    sort_family=list_sort_aliases_sort_info["sort_family"],
                    sort_key=list_sort_aliases_sort_info["sort_key"],
                    sort_direction=list_sort_aliases_sort_info["sort_direction"],
                    sort_is_desc=list_sort_aliases_sort_info["sort_is_desc"],
                    group_count=len(grouped),
                    min_group_size=args.list_sort_aliases_min_group_size,
                    max_group_size=args.list_sort_aliases_max_group_size,
                    min_group_size_global=args.list_sort_aliases_min_group_size_global,
                    max_group_size_global=args.list_sort_aliases_max_group_size_global,
                    min_group_share_pct_global=args.list_sort_aliases_min_group_share_pct_global,
                    max_group_share_pct_global=args.list_sort_aliases_max_group_share_pct_global,
                    min_group_share_pct=args.list_sort_aliases_min_group_share_pct,
                    max_group_share_pct=args.list_sort_aliases_max_group_share_pct,
                    min_group_share_delta_pct=args.list_sort_aliases_min_group_share_delta_pct,
                    max_group_share_delta_pct=args.list_sort_aliases_max_group_share_delta_pct,
                    min_group_share_delta_abs_pct=args.list_sort_aliases_min_group_share_delta_abs_pct,
                    max_group_share_delta_abs_pct=args.list_sort_aliases_max_group_share_delta_abs_pct,
                    min_group_size_delta=args.list_sort_aliases_min_group_size_delta,
                    max_group_size_delta=args.list_sort_aliases_max_group_size_delta,
                    min_group_size_delta_abs=args.list_sort_aliases_min_group_size_delta_abs,
                    max_group_size_delta_abs=args.list_sort_aliases_max_group_size_delta_abs,
                    min_group_size_delta_pct=args.list_sort_aliases_min_group_size_delta_pct,
                    max_group_size_delta_pct=args.list_sort_aliases_max_group_size_delta_pct,
                    min_group_size_delta_abs_pct=args.list_sort_aliases_min_group_size_delta_abs_pct,
                    max_group_size_delta_abs_pct=args.list_sort_aliases_max_group_size_delta_abs_pct,
                    meta_format=args.list_sort_aliases_tsv_meta_format,
                    json_schema_version=sort_aliases_meta_json_schema_version,
                )

            if resolved_list_sort_aliases_format == "grouped-json":
                print(
                    json.dumps(
                        {
                            "schema_version": "v2",
                            "schema": "planner_sort_aliases.v2",
                            "output": "grouped",
                            "output_transport": _resolve_sort_aliases_output_transport(resolved_list_sort_aliases_format),
                            "output_is_rows": _resolve_sort_aliases_output_is_rows(resolved_list_sort_aliases_format),
                            "output_has_header": _resolve_sort_aliases_output_has_header(resolved_list_sort_aliases_format),
                            "output_delimiter": _resolve_sort_aliases_output_delimiter(resolved_list_sort_aliases_format),
                            "output_field_count": _resolve_sort_aliases_output_field_count(resolved_list_sort_aliases_format),
                            "output_column_count": _resolve_sort_aliases_output_column_count(resolved_list_sort_aliases_format),
                            "output_columns": _resolve_sort_aliases_output_columns(resolved_list_sort_aliases_format),
                            "output_columns_sha256": _resolve_sort_aliases_output_columns_sha256(resolved_list_sort_aliases_format),
                            "output_shape_schema": _resolve_sort_aliases_output_shape_schema(resolved_list_sort_aliases_format),
                            "output_shape_fields": _resolve_sort_aliases_output_shape_fields(resolved_list_sort_aliases_format),
                            "output_shape_payload": _resolve_sort_aliases_output_shape_payload(resolved_list_sort_aliases_format),
                            "output_shape_payload_json": _resolve_sort_aliases_output_shape_payload_json(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_bytes": _resolve_sort_aliases_output_shape_payload_json_bytes(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256": _resolve_sort_aliases_output_shape_payload_json_sha256(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256_algo": _resolve_sort_aliases_output_shape_payload_json_sha256_algo(resolved_list_sort_aliases_format),
                            "output_shape_tuple": _resolve_sort_aliases_output_shape_tuple(resolved_list_sort_aliases_format),
                            "output_shape_tuple_bytes": _resolve_sort_aliases_output_shape_tuple_bytes(resolved_list_sort_aliases_format),
                            "output_shape_sha256": _resolve_sort_aliases_output_shape_sha256(resolved_list_sort_aliases_format),
                            "output_shape_sha256_algo": _resolve_sort_aliases_output_shape_sha256_algo(resolved_list_sort_aliases_format),
                            "group_schema_version": "v2",
                            "output_format": resolved_list_sort_aliases_format,
                            "output_format_requested": list_sort_aliases_format_requested,
                            "output_format_alias_resolved": list_sort_aliases_format_alias_resolved,
                            "filtered_count": filtered_count,
                            "emitted_count": len(alias_map),
                            "output_record_count": len(alias_map),
                            "output_is_empty": len(alias_map) == 0,
                            "output_is_single_record": len(alias_map) == 1,
                            "output_has_multiple_records": len(alias_map) > 1,
                            "truncated": truncated,
                            "name_contains": args.list_sort_aliases_name_contains,
                            "name_not_contains": args.list_sort_aliases_name_not_contains,
                            "name_values": name_values,
                            "name_not_values": name_not_values,
                            "filter_mode": resolved_list_sort_aliases_filter_mode,
                            "filter_mode_requested": list_sort_aliases_filter_mode_requested,
                            "filter_mode_alias_resolved": list_sort_aliases_filter_mode_alias_resolved,
                            "name_not_filter_mode": resolved_list_sort_aliases_name_not_filter_mode,
                            "name_not_filter_mode_requested": list_sort_aliases_name_not_filter_mode_requested,
                            "name_not_filter_mode_alias_resolved": list_sort_aliases_name_not_filter_mode_alias_resolved,
                            "match_field": resolved_list_sort_aliases_match_field,
                            "match_field_requested": list_sort_aliases_match_field_requested,
                            "match_field_alias_resolved": list_sort_aliases_match_field_alias_resolved,
                            "case_sensitive": args.list_sort_aliases_case_sensitive,
                            "min_group_size": args.list_sort_aliases_min_group_size,
                            "max_group_size": args.list_sort_aliases_max_group_size,
                            "min_group_size_global": args.list_sort_aliases_min_group_size_global,
                            "max_group_size_global": args.list_sort_aliases_max_group_size_global,
                            "min_group_share_pct_global": args.list_sort_aliases_min_group_share_pct_global,
                            "max_group_share_pct_global": args.list_sort_aliases_max_group_share_pct_global,
                            "min_group_share_pct": args.list_sort_aliases_min_group_share_pct,
                            "max_group_share_pct": args.list_sort_aliases_max_group_share_pct,
                            "min_group_share_delta_pct": args.list_sort_aliases_min_group_share_delta_pct,
                            "max_group_share_delta_pct": args.list_sort_aliases_max_group_share_delta_pct,
                            "min_group_share_delta_abs_pct": args.list_sort_aliases_min_group_share_delta_abs_pct,
                            "max_group_share_delta_abs_pct": args.list_sort_aliases_max_group_share_delta_abs_pct,
                            "min_group_size_delta": args.list_sort_aliases_min_group_size_delta,
                            "max_group_size_delta": args.list_sort_aliases_max_group_size_delta,
                            "min_group_size_delta_abs": args.list_sort_aliases_min_group_size_delta_abs,
                            "max_group_size_delta_abs": args.list_sort_aliases_max_group_size_delta_abs,
                            "min_group_size_delta_pct": args.list_sort_aliases_min_group_size_delta_pct,
                            "max_group_size_delta_pct": args.list_sort_aliases_max_group_size_delta_pct,
                            "min_group_size_delta_abs_pct": args.list_sort_aliases_min_group_size_delta_abs_pct,
                            "max_group_size_delta_abs_pct": args.list_sort_aliases_max_group_size_delta_abs_pct,
                            "limit": args.list_sort_aliases_limit,
                            "sort": resolved_list_sort_aliases_sort,
                            "sort_requested": list_sort_aliases_sort_requested,
                            "sort_alias_resolved": list_sort_aliases_sort_alias_resolved,
                            "sort_family": list_sort_aliases_sort_info["sort_family"],
                            "sort_key": list_sort_aliases_sort_info["sort_key"],
                            "sort_direction": list_sort_aliases_sort_info["sort_direction"],
                            "sort_is_desc": list_sort_aliases_sort_info["sort_is_desc"],
                            "group_count": len(grouped),
                            "group_sizes": group_sizes,
                            "group_share_pct": group_share_pct,
                            "global_alias_count": global_alias_count,
                            "group_sizes_global": global_group_sizes,
                            "group_share_pct_global": global_group_share_pct,
                            "groups": grouped,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            if resolved_list_sort_aliases_format == "names":
                print("\n".join(alias_map.keys()))
                if args.list_sort_aliases_names_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            if resolved_list_sort_aliases_format == "canonical-names":
                print("\n".join(grouped.keys()))
                if args.list_sort_aliases_names_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            if resolved_list_sort_aliases_format == "names-json":
                print(
                    json.dumps(
                        {
                            "schema_version": "v1",
                            "schema": "planner_sort_alias_names.v1",
                            "output": "names",
                            "output_transport": _resolve_sort_aliases_output_transport(resolved_list_sort_aliases_format),
                            "output_is_rows": _resolve_sort_aliases_output_is_rows(resolved_list_sort_aliases_format),
                            "output_has_header": _resolve_sort_aliases_output_has_header(resolved_list_sort_aliases_format),
                            "output_delimiter": _resolve_sort_aliases_output_delimiter(resolved_list_sort_aliases_format),
                            "output_field_count": _resolve_sort_aliases_output_field_count(resolved_list_sort_aliases_format),
                            "output_column_count": _resolve_sort_aliases_output_column_count(resolved_list_sort_aliases_format),
                            "output_columns": _resolve_sort_aliases_output_columns(resolved_list_sort_aliases_format),
                            "output_columns_sha256": _resolve_sort_aliases_output_columns_sha256(resolved_list_sort_aliases_format),
                            "output_shape_schema": _resolve_sort_aliases_output_shape_schema(resolved_list_sort_aliases_format),
                            "output_shape_fields": _resolve_sort_aliases_output_shape_fields(resolved_list_sort_aliases_format),
                            "output_shape_payload": _resolve_sort_aliases_output_shape_payload(resolved_list_sort_aliases_format),
                            "output_shape_payload_json": _resolve_sort_aliases_output_shape_payload_json(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_bytes": _resolve_sort_aliases_output_shape_payload_json_bytes(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256": _resolve_sort_aliases_output_shape_payload_json_sha256(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256_algo": _resolve_sort_aliases_output_shape_payload_json_sha256_algo(resolved_list_sort_aliases_format),
                            "output_shape_tuple": _resolve_sort_aliases_output_shape_tuple(resolved_list_sort_aliases_format),
                            "output_shape_tuple_bytes": _resolve_sort_aliases_output_shape_tuple_bytes(resolved_list_sort_aliases_format),
                            "output_shape_sha256": _resolve_sort_aliases_output_shape_sha256(resolved_list_sort_aliases_format),
                            "output_shape_sha256_algo": _resolve_sort_aliases_output_shape_sha256_algo(resolved_list_sort_aliases_format),
                            "output_format": resolved_list_sort_aliases_format,
                            "output_format_requested": list_sort_aliases_format_requested,
                            "output_format_alias_resolved": list_sort_aliases_format_alias_resolved,
                            "filtered_count": filtered_count,
                            "emitted_count": len(alias_map),
                            "output_record_count": len(alias_map),
                            "output_is_empty": len(alias_map) == 0,
                            "output_is_single_record": len(alias_map) == 1,
                            "output_has_multiple_records": len(alias_map) > 1,
                            "truncated": truncated,
                            "name_contains": args.list_sort_aliases_name_contains,
                            "name_not_contains": args.list_sort_aliases_name_not_contains,
                            "name_values": name_values,
                            "name_not_values": name_not_values,
                            "filter_mode": resolved_list_sort_aliases_filter_mode,
                            "filter_mode_requested": list_sort_aliases_filter_mode_requested,
                            "filter_mode_alias_resolved": list_sort_aliases_filter_mode_alias_resolved,
                            "name_not_filter_mode": resolved_list_sort_aliases_name_not_filter_mode,
                            "name_not_filter_mode_requested": list_sort_aliases_name_not_filter_mode_requested,
                            "name_not_filter_mode_alias_resolved": list_sort_aliases_name_not_filter_mode_alias_resolved,
                            "match_field": resolved_list_sort_aliases_match_field,
                            "match_field_requested": list_sort_aliases_match_field_requested,
                            "match_field_alias_resolved": list_sort_aliases_match_field_alias_resolved,
                            "case_sensitive": args.list_sort_aliases_case_sensitive,
                            "min_group_size": args.list_sort_aliases_min_group_size,
                            "max_group_size": args.list_sort_aliases_max_group_size,
                            "min_group_size_global": args.list_sort_aliases_min_group_size_global,
                            "max_group_size_global": args.list_sort_aliases_max_group_size_global,
                            "min_group_share_pct_global": args.list_sort_aliases_min_group_share_pct_global,
                            "max_group_share_pct_global": args.list_sort_aliases_max_group_share_pct_global,
                            "min_group_share_pct": args.list_sort_aliases_min_group_share_pct,
                            "max_group_share_pct": args.list_sort_aliases_max_group_share_pct,
                            "min_group_share_delta_pct": args.list_sort_aliases_min_group_share_delta_pct,
                            "max_group_share_delta_pct": args.list_sort_aliases_max_group_share_delta_pct,
                            "min_group_share_delta_abs_pct": args.list_sort_aliases_min_group_share_delta_abs_pct,
                            "max_group_share_delta_abs_pct": args.list_sort_aliases_max_group_share_delta_abs_pct,
                            "min_group_size_delta": args.list_sort_aliases_min_group_size_delta,
                            "max_group_size_delta": args.list_sort_aliases_max_group_size_delta,
                            "min_group_size_delta_abs": args.list_sort_aliases_min_group_size_delta_abs,
                            "max_group_size_delta_abs": args.list_sort_aliases_max_group_size_delta_abs,
                            "min_group_size_delta_pct": args.list_sort_aliases_min_group_size_delta_pct,
                            "max_group_size_delta_pct": args.list_sort_aliases_max_group_size_delta_pct,
                            "min_group_size_delta_abs_pct": args.list_sort_aliases_min_group_size_delta_abs_pct,
                            "max_group_size_delta_abs_pct": args.list_sort_aliases_max_group_size_delta_abs_pct,
                            "limit": args.list_sort_aliases_limit,
                            "sort": resolved_list_sort_aliases_sort,
                            "sort_requested": list_sort_aliases_sort_requested,
                            "sort_alias_resolved": list_sort_aliases_sort_alias_resolved,
                            "sort_family": list_sort_aliases_sort_info["sort_family"],
                            "sort_key": list_sort_aliases_sort_info["sort_key"],
                            "sort_direction": list_sort_aliases_sort_info["sort_direction"],
                            "sort_is_desc": list_sort_aliases_sort_info["sort_is_desc"],
                            "group_count": len(grouped),
                            "names": list(alias_map.keys()),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            if resolved_list_sort_aliases_format == "canonical-names-json":
                print(
                    json.dumps(
                        {
                            "schema_version": "v1",
                            "schema": "planner_sort_alias_names.v1",
                            "output": "canonical-names",
                            "output_transport": _resolve_sort_aliases_output_transport(resolved_list_sort_aliases_format),
                            "output_is_rows": _resolve_sort_aliases_output_is_rows(resolved_list_sort_aliases_format),
                            "output_has_header": _resolve_sort_aliases_output_has_header(resolved_list_sort_aliases_format),
                            "output_delimiter": _resolve_sort_aliases_output_delimiter(resolved_list_sort_aliases_format),
                            "output_field_count": _resolve_sort_aliases_output_field_count(resolved_list_sort_aliases_format),
                            "output_column_count": _resolve_sort_aliases_output_column_count(resolved_list_sort_aliases_format),
                            "output_columns": _resolve_sort_aliases_output_columns(resolved_list_sort_aliases_format),
                            "output_columns_sha256": _resolve_sort_aliases_output_columns_sha256(resolved_list_sort_aliases_format),
                            "output_shape_schema": _resolve_sort_aliases_output_shape_schema(resolved_list_sort_aliases_format),
                            "output_shape_fields": _resolve_sort_aliases_output_shape_fields(resolved_list_sort_aliases_format),
                            "output_shape_payload": _resolve_sort_aliases_output_shape_payload(resolved_list_sort_aliases_format),
                            "output_shape_payload_json": _resolve_sort_aliases_output_shape_payload_json(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_bytes": _resolve_sort_aliases_output_shape_payload_json_bytes(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256": _resolve_sort_aliases_output_shape_payload_json_sha256(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256_algo": _resolve_sort_aliases_output_shape_payload_json_sha256_algo(resolved_list_sort_aliases_format),
                            "output_shape_tuple": _resolve_sort_aliases_output_shape_tuple(resolved_list_sort_aliases_format),
                            "output_shape_tuple_bytes": _resolve_sort_aliases_output_shape_tuple_bytes(resolved_list_sort_aliases_format),
                            "output_shape_sha256": _resolve_sort_aliases_output_shape_sha256(resolved_list_sort_aliases_format),
                            "output_shape_sha256_algo": _resolve_sort_aliases_output_shape_sha256_algo(resolved_list_sort_aliases_format),
                            "output_format": resolved_list_sort_aliases_format,
                            "output_format_requested": list_sort_aliases_format_requested,
                            "output_format_alias_resolved": list_sort_aliases_format_alias_resolved,
                            "filtered_count": filtered_count,
                            "emitted_count": len(grouped),
                            "output_record_count": len(grouped),
                            "output_is_empty": len(grouped) == 0,
                            "output_is_single_record": len(grouped) == 1,
                            "output_has_multiple_records": len(grouped) > 1,
                            "truncated": truncated,
                            "name_contains": args.list_sort_aliases_name_contains,
                            "name_not_contains": args.list_sort_aliases_name_not_contains,
                            "name_values": name_values,
                            "name_not_values": name_not_values,
                            "filter_mode": resolved_list_sort_aliases_filter_mode,
                            "filter_mode_requested": list_sort_aliases_filter_mode_requested,
                            "filter_mode_alias_resolved": list_sort_aliases_filter_mode_alias_resolved,
                            "name_not_filter_mode": resolved_list_sort_aliases_name_not_filter_mode,
                            "name_not_filter_mode_requested": list_sort_aliases_name_not_filter_mode_requested,
                            "name_not_filter_mode_alias_resolved": list_sort_aliases_name_not_filter_mode_alias_resolved,
                            "match_field": resolved_list_sort_aliases_match_field,
                            "match_field_requested": list_sort_aliases_match_field_requested,
                            "match_field_alias_resolved": list_sort_aliases_match_field_alias_resolved,
                            "case_sensitive": args.list_sort_aliases_case_sensitive,
                            "min_group_size": args.list_sort_aliases_min_group_size,
                            "max_group_size": args.list_sort_aliases_max_group_size,
                            "min_group_size_global": args.list_sort_aliases_min_group_size_global,
                            "max_group_size_global": args.list_sort_aliases_max_group_size_global,
                            "min_group_share_pct_global": args.list_sort_aliases_min_group_share_pct_global,
                            "max_group_share_pct_global": args.list_sort_aliases_max_group_share_pct_global,
                            "min_group_share_pct": args.list_sort_aliases_min_group_share_pct,
                            "max_group_share_pct": args.list_sort_aliases_max_group_share_pct,
                            "min_group_share_delta_pct": args.list_sort_aliases_min_group_share_delta_pct,
                            "max_group_share_delta_pct": args.list_sort_aliases_max_group_share_delta_pct,
                            "min_group_share_delta_abs_pct": args.list_sort_aliases_min_group_share_delta_abs_pct,
                            "max_group_share_delta_abs_pct": args.list_sort_aliases_max_group_share_delta_abs_pct,
                            "min_group_size_delta": args.list_sort_aliases_min_group_size_delta,
                            "max_group_size_delta": args.list_sort_aliases_max_group_size_delta,
                            "min_group_size_delta_abs": args.list_sort_aliases_min_group_size_delta_abs,
                            "max_group_size_delta_abs": args.list_sort_aliases_max_group_size_delta_abs,
                            "min_group_size_delta_pct": args.list_sort_aliases_min_group_size_delta_pct,
                            "max_group_size_delta_pct": args.list_sort_aliases_max_group_size_delta_pct,
                            "min_group_size_delta_abs_pct": args.list_sort_aliases_min_group_size_delta_abs_pct,
                            "max_group_size_delta_abs_pct": args.list_sort_aliases_max_group_size_delta_abs_pct,
                            "limit": args.list_sort_aliases_limit,
                            "sort": resolved_list_sort_aliases_sort,
                            "sort_requested": list_sort_aliases_sort_requested,
                            "sort_alias_resolved": list_sort_aliases_sort_alias_resolved,
                            "sort_family": list_sort_aliases_sort_info["sort_family"],
                            "sort_key": list_sort_aliases_sort_info["sort_key"],
                            "sort_direction": list_sort_aliases_sort_info["sort_direction"],
                            "sort_is_desc": list_sort_aliases_sort_info["sort_is_desc"],
                            "group_count": len(grouped),
                            "canonical_names": list(grouped.keys()),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            if resolved_list_sort_aliases_format == "aliases-tsv":
                print(
                    _format_sort_aliases_tsv(
                        alias_map,
                        global_group_share_pct=global_group_share_pct,
                        global_group_sizes=global_group_sizes,
                    )
                )
                if args.list_sort_aliases_tsv_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            if resolved_list_sort_aliases_format == "grouped-tsv":
                print(
                    _format_sort_alias_groups_tsv(
                        grouped,
                        global_group_share_pct=global_group_share_pct,
                        global_group_sizes=global_group_sizes,
                    )
                )
                if args.list_sort_aliases_tsv_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            if resolved_list_sort_aliases_format == "aliases-tsv-rows":
                print(
                    _format_sort_aliases_tsv(
                        alias_map,
                        global_group_share_pct=global_group_share_pct,
                        global_group_sizes=global_group_sizes,
                        include_header=False,
                    )
                )
                if args.list_sort_aliases_tsv_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            if resolved_list_sort_aliases_format == "grouped-tsv-rows":
                print(
                    _format_sort_alias_groups_tsv(
                        grouped,
                        global_group_share_pct=global_group_share_pct,
                        global_group_sizes=global_group_sizes,
                        include_header=False,
                    )
                )
                if args.list_sort_aliases_tsv_with_meta:
                    print(build_sort_aliases_meta_footer())
                return 0
            print(
                json.dumps(
                    {
                        "schema_version": "v2",
                        "schema": "planner_sort_aliases.v2",
                        "output": "aliases",
                        "output_transport": _resolve_sort_aliases_output_transport(resolved_list_sort_aliases_format),
                        "output_is_rows": _resolve_sort_aliases_output_is_rows(resolved_list_sort_aliases_format),
                        "output_has_header": _resolve_sort_aliases_output_has_header(resolved_list_sort_aliases_format),
                        "output_delimiter": _resolve_sort_aliases_output_delimiter(resolved_list_sort_aliases_format),
                        "output_field_count": _resolve_sort_aliases_output_field_count(resolved_list_sort_aliases_format),
                            "output_column_count": _resolve_sort_aliases_output_column_count(resolved_list_sort_aliases_format),
                            "output_columns": _resolve_sort_aliases_output_columns(resolved_list_sort_aliases_format),
                            "output_columns_sha256": _resolve_sort_aliases_output_columns_sha256(resolved_list_sort_aliases_format),
                            "output_shape_schema": _resolve_sort_aliases_output_shape_schema(resolved_list_sort_aliases_format),
                            "output_shape_fields": _resolve_sort_aliases_output_shape_fields(resolved_list_sort_aliases_format),
                            "output_shape_payload": _resolve_sort_aliases_output_shape_payload(resolved_list_sort_aliases_format),
                            "output_shape_payload_json": _resolve_sort_aliases_output_shape_payload_json(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_bytes": _resolve_sort_aliases_output_shape_payload_json_bytes(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256": _resolve_sort_aliases_output_shape_payload_json_sha256(resolved_list_sort_aliases_format),
                            "output_shape_payload_json_sha256_algo": _resolve_sort_aliases_output_shape_payload_json_sha256_algo(resolved_list_sort_aliases_format),
                            "output_shape_tuple": _resolve_sort_aliases_output_shape_tuple(resolved_list_sort_aliases_format),
                            "output_shape_tuple_bytes": _resolve_sort_aliases_output_shape_tuple_bytes(resolved_list_sort_aliases_format),
                            "output_shape_sha256": _resolve_sort_aliases_output_shape_sha256(resolved_list_sort_aliases_format),
                            "output_shape_sha256_algo": _resolve_sort_aliases_output_shape_sha256_algo(resolved_list_sort_aliases_format),
                        "output_format": resolved_list_sort_aliases_format,
                        "output_format_requested": list_sort_aliases_format_requested,
                        "output_format_alias_resolved": list_sort_aliases_format_alias_resolved,
                        "filtered_count": filtered_count,
                        "emitted_count": len(alias_map),
                        "output_record_count": len(alias_map),
                        "truncated": truncated,
                        "name_contains": args.list_sort_aliases_name_contains,
                        "name_not_contains": args.list_sort_aliases_name_not_contains,
                        "name_values": name_values,
                        "name_not_values": name_not_values,
                        "filter_mode": resolved_list_sort_aliases_filter_mode,
                        "filter_mode_requested": list_sort_aliases_filter_mode_requested,
                        "filter_mode_alias_resolved": list_sort_aliases_filter_mode_alias_resolved,
                        "name_not_filter_mode": resolved_list_sort_aliases_name_not_filter_mode,
                        "name_not_filter_mode_requested": list_sort_aliases_name_not_filter_mode_requested,
                        "name_not_filter_mode_alias_resolved": list_sort_aliases_name_not_filter_mode_alias_resolved,
                        "match_field": resolved_list_sort_aliases_match_field,
                            "match_field_requested": list_sort_aliases_match_field_requested,
                            "match_field_alias_resolved": list_sort_aliases_match_field_alias_resolved,
                        "case_sensitive": args.list_sort_aliases_case_sensitive,
                        "min_group_size": args.list_sort_aliases_min_group_size,
                        "max_group_size": args.list_sort_aliases_max_group_size,
                        "min_group_size_global": args.list_sort_aliases_min_group_size_global,
                        "max_group_size_global": args.list_sort_aliases_max_group_size_global,
                        "min_group_share_pct_global": args.list_sort_aliases_min_group_share_pct_global,
                        "max_group_share_pct_global": args.list_sort_aliases_max_group_share_pct_global,
                        "min_group_share_pct": args.list_sort_aliases_min_group_share_pct,
                        "max_group_share_pct": args.list_sort_aliases_max_group_share_pct,
                        "min_group_share_delta_pct": args.list_sort_aliases_min_group_share_delta_pct,
                        "max_group_share_delta_pct": args.list_sort_aliases_max_group_share_delta_pct,
                        "min_group_share_delta_abs_pct": args.list_sort_aliases_min_group_share_delta_abs_pct,
                        "max_group_share_delta_abs_pct": args.list_sort_aliases_max_group_share_delta_abs_pct,
                        "min_group_size_delta": args.list_sort_aliases_min_group_size_delta,
                        "max_group_size_delta": args.list_sort_aliases_max_group_size_delta,
                        "min_group_size_delta_abs": args.list_sort_aliases_min_group_size_delta_abs,
                        "max_group_size_delta_abs": args.list_sort_aliases_max_group_size_delta_abs,
                        "min_group_size_delta_pct": args.list_sort_aliases_min_group_size_delta_pct,
                        "max_group_size_delta_pct": args.list_sort_aliases_max_group_size_delta_pct,
                        "min_group_size_delta_abs_pct": args.list_sort_aliases_min_group_size_delta_abs_pct,
                        "max_group_size_delta_abs_pct": args.list_sort_aliases_max_group_size_delta_abs_pct,
                        "limit": args.list_sort_aliases_limit,
                        "sort": resolved_list_sort_aliases_sort,
                        "sort_requested": list_sort_aliases_sort_requested,
                        "sort_alias_resolved": list_sort_aliases_sort_alias_resolved,
                        "sort_family": list_sort_aliases_sort_info["sort_family"],
                        "sort_key": list_sort_aliases_sort_info["sort_key"],
                        "sort_direction": list_sort_aliases_sort_info["sort_direction"],
                        "sort_is_desc": list_sort_aliases_sort_info["sort_is_desc"],
                        "group_count": len(grouped),
                        "group_sizes": group_sizes,
                        "group_share_pct": group_share_pct,
                        "global_alias_count": global_alias_count,
                        "group_sizes_global": global_group_sizes,
                        "group_share_pct_global": global_group_share_pct,
                        "aliases": alias_map,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.list_presets:
            presets = load_preset_file(args.preset_file)
            list_presets_tag_match_requested = args.list_presets_tag_match
            resolved_list_presets_tag_match = _resolve_tag_match_mode(args.list_presets_tag_match)
            list_presets_tag_match_alias_resolved = (
                list_presets_tag_match_requested != resolved_list_presets_tag_match
            )
            list_presets_sort_requested = args.list_presets_sort
            resolved_list_presets_sort = _resolve_list_presets_sort_mode(args.list_presets_sort)
            list_presets_sort_alias_resolved = list_presets_sort_requested != resolved_list_presets_sort
            list_presets_sort_info = _describe_list_presets_sort_mode(resolved_list_presets_sort)
            list_presets_tag_filter_mode_requested = args.list_presets_tag_filter_mode
            resolved_list_presets_tag_filter_mode = _resolve_filter_mode(args.list_presets_tag_filter_mode)
            list_presets_tag_filter_mode_alias_resolved = (
                list_presets_tag_filter_mode_requested != resolved_list_presets_tag_filter_mode
            )
            list_presets_tag_not_match_requested = args.list_presets_tag_not_match
            resolved_list_presets_tag_not_match = _resolve_tag_match_mode(args.list_presets_tag_not_match)
            list_presets_tag_not_match_alias_resolved = (
                list_presets_tag_not_match_requested != resolved_list_presets_tag_not_match
            )
            list_presets_tag_not_filter_mode_requested = args.list_presets_tag_not_filter_mode
            resolved_list_presets_tag_not_filter_mode = _resolve_filter_mode(
                args.list_presets_tag_not_filter_mode
            )
            list_presets_tag_not_filter_mode_alias_resolved = (
                list_presets_tag_not_filter_mode_requested
                != resolved_list_presets_tag_not_filter_mode
            )
            required_tags: set[str] = set()
            excluded_tags: set[str] = set()
            if args.list_presets_tag:
                if args.list_presets_tag_case_sensitive:
                    required_tags = {tag.strip() for tag in args.list_presets_tag.split(",") if tag.strip()}
                else:
                    required_tags = {tag.strip().lower() for tag in args.list_presets_tag.split(",") if tag.strip()}
                if not required_tags:
                    raise ValueError("--list-presets-tag must include at least one non-empty tag")
            if args.list_presets_tag_not_contains:
                if args.list_presets_tag_case_sensitive:
                    excluded_tags = {
                        tag.strip() for tag in args.list_presets_tag_not_contains.split(",") if tag.strip()
                    }
                else:
                    excluded_tags = {
                        tag.strip().lower()
                        for tag in args.list_presets_tag_not_contains.split(",")
                        if tag.strip()
                    }
                if not excluded_tags:
                    raise ValueError(
                        "--list-presets-tag-not-contains must include at least one non-empty tag"
                    )
            required_tags_sorted = sorted(required_tags)
            excluded_tags_sorted = sorted(excluded_tags)
            tag_filter_raw = args.list_presets_tag.strip() if isinstance(args.list_presets_tag, str) else ""
            tag_not_filter_raw = (
                args.list_presets_tag_not_contains.strip()
                if isinstance(args.list_presets_tag_not_contains, str)
                else ""
            )
            list_presets_name_filter_mode_requested = args.list_presets_name_filter_mode
            resolved_list_presets_name_filter_mode = _resolve_filter_mode(args.list_presets_name_filter_mode)
            list_presets_name_filter_mode_alias_resolved = (
                list_presets_name_filter_mode_requested != resolved_list_presets_name_filter_mode
            )
            list_presets_name_not_filter_mode_requested = args.list_presets_name_not_filter_mode
            resolved_list_presets_name_not_filter_mode = _resolve_filter_mode(
                args.list_presets_name_not_filter_mode
            )
            list_presets_name_not_filter_mode_alias_resolved = (
                list_presets_name_not_filter_mode_requested
                != resolved_list_presets_name_not_filter_mode
            )
            name_filter = args.list_presets_name_contains.strip() if args.list_presets_name_contains else None
            if args.list_presets_name_contains is not None and not name_filter:
                raise ValueError("--list-presets-name-contains must include at least one non-empty character")
            name_contains_raw = name_filter or ""
            name_not_filter = (
                args.list_presets_name_not_contains.strip()
                if args.list_presets_name_not_contains
                else None
            )
            name_not_contains_raw = name_not_filter or ""
            if args.list_presets_name_not_contains is not None and not name_not_filter:
                raise ValueError(
                    "--list-presets-name-not-contains must include at least one non-empty character"
                )
            name_values = (
                [name_filter if args.list_presets_name_case_sensitive else name_filter.lower()]
                if name_filter
                else []
            )
            name_not_values = (
                [name_not_filter if args.list_presets_name_case_sensitive else name_not_filter.lower()]
                if name_not_filter
                else []
            )
            if args.list_presets_limit is not None and args.list_presets_limit < 1:
                raise ValueError("--list-presets-limit must be >= 1")
            filtered_presets = {
                name: preset
                for name, preset in presets.items()
                if isinstance(preset, dict)
                and _matches_preset_name(
                    name,
                    name_filter,
                    filter_mode=resolved_list_presets_name_filter_mode,
                    case_sensitive=args.list_presets_name_case_sensitive,
                )
                and (
                    not name_not_filter
                    or not _matches_preset_name(
                        name,
                        name_not_filter,
                        filter_mode=resolved_list_presets_name_not_filter_mode,
                        case_sensitive=args.list_presets_name_case_sensitive,
                    )
                )
                and _matches_preset_tags(
                    preset,
                    required_tags,
                    match_mode=resolved_list_presets_tag_match,
                    filter_mode=resolved_list_presets_tag_filter_mode,
                    case_sensitive=args.list_presets_tag_case_sensitive,
                )
                and (
                    not excluded_tags
                    or not _matches_preset_tags(
                        preset,
                        excluded_tags,
                        match_mode=resolved_list_presets_tag_not_match,
                        filter_mode=resolved_list_presets_tag_not_filter_mode,
                        case_sensitive=args.list_presets_tag_case_sensitive,
                    )
                )
            }
            preset_names = _sort_preset_names(
                list(filtered_presets.keys()),
                filtered_presets,
                sort_mode=resolved_list_presets_sort,
            )
            truncated = False
            if args.list_presets_limit is not None and len(preset_names) > args.list_presets_limit:
                preset_names = preset_names[: args.list_presets_limit]
                truncated = True
            list_meta_extra_fields: dict[str, Any] | None = None
            if args.list_presets_meta_include_filters:
                list_meta_extra_fields = {
                    "tag_filter": tag_filter_raw or "none",
                    "tag_match": resolved_list_presets_tag_match,
                    "tag_match_requested": list_presets_tag_match_requested,
                    "tag_match_alias_resolved": str(list_presets_tag_match_alias_resolved).lower(),
                    "tag_filter_mode": resolved_list_presets_tag_filter_mode,
                    "tag_filter_mode_requested": list_presets_tag_filter_mode_requested,
                    "tag_filter_mode_alias_resolved": str(list_presets_tag_filter_mode_alias_resolved).lower(),
                    "tag_not_filter": tag_not_filter_raw or "none",
                    "tag_not_match": resolved_list_presets_tag_not_match,
                    "tag_not_match_requested": list_presets_tag_not_match_requested,
                    "tag_not_match_alias_resolved": str(list_presets_tag_not_match_alias_resolved).lower(),
                    "tag_not_filter_mode": resolved_list_presets_tag_not_filter_mode,
                    "tag_not_filter_mode_requested": list_presets_tag_not_filter_mode_requested,
                    "tag_not_filter_mode_alias_resolved": str(list_presets_tag_not_filter_mode_alias_resolved).lower(),
                    "tag_case_sensitive": str(args.list_presets_tag_case_sensitive).lower(),
                    "tag_values": ",".join(required_tags_sorted) if required_tags_sorted else "none",
                    "tag_not_values": ",".join(excluded_tags_sorted) if excluded_tags_sorted else "none",
                    "name_contains": name_contains_raw or "none",
                    "name_values": ",".join(name_values) if name_values else "none",
                    "name_filter_mode": resolved_list_presets_name_filter_mode,
                    "name_filter_mode_requested": list_presets_name_filter_mode_requested,
                    "name_filter_mode_alias_resolved": str(list_presets_name_filter_mode_alias_resolved).lower(),
                    "name_not_contains": name_not_contains_raw or "none",
                    "name_not_values": ",".join(name_not_values) if name_not_values else "none",
                    "name_not_filter_mode": resolved_list_presets_name_not_filter_mode,
                    "name_not_filter_mode_requested": list_presets_name_not_filter_mode_requested,
                    "name_not_filter_mode_alias_resolved": str(list_presets_name_not_filter_mode_alias_resolved).lower(),
                    "name_case_sensitive": str(args.list_presets_name_case_sensitive).lower(),
                    "limit": str(args.list_presets_limit)
                    if args.list_presets_limit is not None
                    else "none",
                    "sort": resolved_list_presets_sort,
                    "sort_requested": list_presets_sort_requested,
                    "sort_alias_resolved": str(list_presets_sort_alias_resolved).lower(),
                    "sort_family": list_presets_sort_info["sort_family"],
                    "sort_tag": list_presets_sort_info["sort_tag"] or "none",
                    "sort_direction": list_presets_sort_info["sort_direction"],
                    "sort_is_desc": str(list_presets_sort_info["sort_is_desc"]).lower(),
                }
            if args.list_presets_meta_include_generated_at:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["generated_at_utc"] = _utc_now_iso()
            if args.list_presets_meta_include_cwd:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["cwd"] = os.getcwd()
            if args.list_presets_meta_include_python_version:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["python_version"] = sys.version.split()[0]
            if args.list_presets_meta_include_pid:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["pid"] = str(os.getpid())
            if args.list_presets_meta_include_hostname:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["hostname"] = socket.gethostname()
            if args.list_presets_meta_include_git_head:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_head"] = _git_head_short(cwd=os.getcwd())
            if args.list_presets_meta_include_git_head_date_utc:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_head_date_utc"] = _git_head_commit_date_utc(cwd=os.getcwd())
            if args.list_presets_meta_include_git_head_subject:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_head_subject"] = _git_head_subject(cwd=os.getcwd())
            if args.list_presets_meta_include_git_branch:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_branch"] = _git_branch_name(cwd=os.getcwd())
            if args.list_presets_meta_include_git_remote:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_remote"] = _git_remote_origin_url(cwd=os.getcwd())
            if args.list_presets_meta_include_git_dirty:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_dirty"] = _git_dirty_state(cwd=os.getcwd())
            if args.list_presets_meta_include_git_toplevel:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_toplevel"] = _git_toplevel(cwd=os.getcwd())
            if args.list_presets_meta_include_git_repo_name:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_repo_name"] = _git_repo_name(cwd=os.getcwd())
            if args.list_presets_meta_include_git_worktree_name:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["git_worktree_name"] = _git_worktree_name(cwd=os.getcwd())
            if args.list_presets_meta_include_argv:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["argv"] = " ".join(sys.argv)
            if args.list_presets_meta_include_argv_tokens:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                if args.list_presets_meta_format == "json":
                    list_meta_extra_fields["argv_tokens"] = list(sys.argv)
                else:
                    list_meta_extra_fields["argv_tokens"] = json.dumps(
                        list(sys.argv), ensure_ascii=False, separators=(",", ":")
                    )
            if args.list_presets_meta_include_argv_sha256:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["argv_sha256"] = hashlib.sha256(
                    "\0".join(sys.argv).encode("utf-8")
                ).hexdigest()
            if args.list_presets_meta_include_argv_count:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["argv_count"] = len(sys.argv)
            if args.list_presets_meta_include_preset_file_sha256:
                if list_meta_extra_fields is None:
                    list_meta_extra_fields = {}
                list_meta_extra_fields["preset_file_sha256"] = _file_sha256(args.preset_file)
            list_output_columns = _resolve_preset_output_columns(
                args.list_presets_format,
                with_schema_column=args.summary_tsv_with_schema_column,
            )
            list_meta_payload = _compose_meta_payload(
                {
                    "schema": list_meta_schema_id,
                    "filtered_count": len(filtered_presets),
                    "emitted_count": len(preset_names),
                    "output_record_count": len(preset_names),
                    "output_is_empty": len(preset_names) == 0,
                    "output_is_single_record": len(preset_names) == 1,
                    "output_has_multiple_records": len(preset_names) > 1,
                    "output_truncated_count": max(len(filtered_presets) - len(preset_names), 0),
                    "truncated": truncated,
                    "output_format": args.list_presets_format,
                    "output_transport": _resolve_preset_output_transport(args.list_presets_format),
                    "output_has_header": _resolve_preset_output_has_header(args.list_presets_format),
                    "output_delimiter": _resolve_preset_output_delimiter(args.list_presets_format),
                    "output_field_count": len(list_output_columns),
                    "output_column_count": _resolve_preset_output_column_count(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_columns": list_output_columns,
                    "output_columns_sha256": _resolve_preset_output_columns_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_schema": PRESET_OUTPUT_SHAPE_SCHEMA,
                    "output_shape_fields": _resolve_preset_output_shape_fields(),
                    "output_shape_payload": _resolve_preset_output_shape_payload(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json": _resolve_preset_output_shape_payload_json(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_bytes": _resolve_preset_output_shape_payload_json_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256": _resolve_preset_output_shape_payload_json_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256_algo": _resolve_preset_output_shape_payload_json_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple": _resolve_preset_output_shape_tuple(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple_bytes": _resolve_preset_output_shape_tuple_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256": _resolve_preset_output_shape_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256_algo": _resolve_preset_output_shape_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "name_filter_mode": resolved_list_presets_name_filter_mode,
                    "name_filter_mode_requested": list_presets_name_filter_mode_requested,
                    "name_filter_mode_alias_resolved": list_presets_name_filter_mode_alias_resolved,
                    "name_not_filter_mode": resolved_list_presets_name_not_filter_mode,
                    "name_not_filter_mode_requested": list_presets_name_not_filter_mode_requested,
                    "name_not_filter_mode_alias_resolved": list_presets_name_not_filter_mode_alias_resolved,
                    "name_case_sensitive": args.list_presets_name_case_sensitive,
                    "name_contains": name_contains_raw or None,
                    "name_not_contains": name_not_contains_raw or None,
                    "name_values": name_values,
                    "name_not_values": name_not_values,
                    "tag_match": resolved_list_presets_tag_match,
                    "tag_match_requested": list_presets_tag_match_requested,
                    "tag_match_alias_resolved": list_presets_tag_match_alias_resolved,
                    "tag_filter_mode": resolved_list_presets_tag_filter_mode,
                    "tag_filter_mode_requested": list_presets_tag_filter_mode_requested,
                    "tag_filter_mode_alias_resolved": list_presets_tag_filter_mode_alias_resolved,
                    "tag_not_match": resolved_list_presets_tag_not_match,
                    "tag_not_match_requested": list_presets_tag_not_match_requested,
                    "tag_not_match_alias_resolved": list_presets_tag_not_match_alias_resolved,
                    "tag_not_filter_mode": resolved_list_presets_tag_not_filter_mode,
                    "tag_not_filter_mode_requested": list_presets_tag_not_filter_mode_requested,
                    "tag_not_filter_mode_alias_resolved": list_presets_tag_not_filter_mode_alias_resolved,
                    "tag_case_sensitive": args.list_presets_tag_case_sensitive,
                    "tag_filter": tag_filter_raw or None,
                    "tag_not_filter": tag_not_filter_raw or None,
                    "tag_values": required_tags_sorted,
                    "tag_not_values": excluded_tags_sorted,
                    "sort": resolved_list_presets_sort,
                    "sort_requested": list_presets_sort_requested,
                    "sort_alias_resolved": list_presets_sort_alias_resolved,
                    "sort_family": list_presets_sort_info["sort_family"],
                    "sort_tag": list_presets_sort_info["sort_tag"],
                    "sort_direction": list_presets_sort_info["sort_direction"],
                    "sort_is_desc": list_presets_sort_info["sort_is_desc"],
                },
                list_meta_extra_fields,
            )

            if args.list_presets_format == "json":
                limited_presets = {name: filtered_presets[name] for name in preset_names}
                list_output_columns = _resolve_preset_output_columns(
                    args.list_presets_format,
                    with_schema_column=args.summary_tsv_with_schema_column,
                )
                payload = {
                    "schema_version": "v1",
                    "output_format": args.list_presets_format,
                    "output_transport": _resolve_preset_output_transport(args.list_presets_format),
                    "output_has_header": _resolve_preset_output_has_header(args.list_presets_format),
                    "output_delimiter": _resolve_preset_output_delimiter(args.list_presets_format),
                    "output_field_count": len(list_output_columns),
                    "output_column_count": _resolve_preset_output_column_count(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_columns": list_output_columns,
                    "output_columns_sha256": _resolve_preset_output_columns_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_schema": PRESET_OUTPUT_SHAPE_SCHEMA,
                    "output_shape_fields": _resolve_preset_output_shape_fields(),
                    "output_shape_payload": _resolve_preset_output_shape_payload(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json": _resolve_preset_output_shape_payload_json(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_bytes": _resolve_preset_output_shape_payload_json_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256": _resolve_preset_output_shape_payload_json_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256_algo": _resolve_preset_output_shape_payload_json_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple": _resolve_preset_output_shape_tuple(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple_bytes": _resolve_preset_output_shape_tuple_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256": _resolve_preset_output_shape_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256_algo": _resolve_preset_output_shape_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "presets": limited_presets,
                    "filtered_count": len(filtered_presets),
                    "emitted_count": len(limited_presets),
                    "output_record_count": len(limited_presets),
                    "output_is_empty": len(limited_presets) == 0,
                    "output_is_single_record": len(limited_presets) == 1,
                    "output_has_multiple_records": len(limited_presets) > 1,
                    "output_truncated_count": max(len(filtered_presets) - len(limited_presets), 0),
                    "truncated": truncated,
                    "name_filter_mode": resolved_list_presets_name_filter_mode,
                    "name_filter_mode_requested": list_presets_name_filter_mode_requested,
                    "name_filter_mode_alias_resolved": list_presets_name_filter_mode_alias_resolved,
                    "name_not_filter_mode": resolved_list_presets_name_not_filter_mode,
                    "name_not_filter_mode_requested": list_presets_name_not_filter_mode_requested,
                    "name_not_filter_mode_alias_resolved": list_presets_name_not_filter_mode_alias_resolved,
                    "name_case_sensitive": args.list_presets_name_case_sensitive,
                    "name_contains": name_contains_raw or None,
                    "name_not_contains": name_not_contains_raw or None,
                    "name_values": name_values,
                    "name_not_values": name_not_values,
                    "tag_match": resolved_list_presets_tag_match,
                    "tag_match_requested": list_presets_tag_match_requested,
                    "tag_match_alias_resolved": list_presets_tag_match_alias_resolved,
                    "tag_filter_mode": resolved_list_presets_tag_filter_mode,
                    "tag_filter_mode_requested": list_presets_tag_filter_mode_requested,
                    "tag_filter_mode_alias_resolved": list_presets_tag_filter_mode_alias_resolved,
                    "tag_not_match": resolved_list_presets_tag_not_match,
                    "tag_not_match_requested": list_presets_tag_not_match_requested,
                    "tag_not_match_alias_resolved": list_presets_tag_not_match_alias_resolved,
                    "tag_not_filter_mode": resolved_list_presets_tag_not_filter_mode,
                    "tag_not_filter_mode_requested": list_presets_tag_not_filter_mode_requested,
                    "tag_not_filter_mode_alias_resolved": list_presets_tag_not_filter_mode_alias_resolved,
                    "tag_case_sensitive": args.list_presets_tag_case_sensitive,
                    "tag_filter": tag_filter_raw or None,
                    "tag_not_filter": tag_not_filter_raw or None,
                    "tag_values": required_tags_sorted,
                    "tag_not_values": excluded_tags_sorted,
                    "sort": resolved_list_presets_sort,
                    "sort_requested": list_presets_sort_requested,
                    "sort_alias_resolved": list_presets_sort_alias_resolved,
                    "sort_family": list_presets_sort_info["sort_family"],
                    "sort_tag": list_presets_sort_info["sort_tag"],
                    "sort_direction": list_presets_sort_info["sort_direction"],
                    "sort_is_desc": list_presets_sort_info["sort_is_desc"],
                }
                if args.list_presets_with_meta:
                    payload["meta"] = list_meta_payload
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0
            if args.list_presets_format == "resolved-json":
                resolved_presets: dict[str, dict[str, Any]] = {}
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved_presets[name] = resolve_preset_with_defaults(preset)
                payload = {
                    "schema_version": "v1",
                    "output_format": args.list_presets_format,
                    "output_transport": _resolve_preset_output_transport(args.list_presets_format),
                    "output_has_header": _resolve_preset_output_has_header(args.list_presets_format),
                    "output_delimiter": _resolve_preset_output_delimiter(args.list_presets_format),
                    "output_field_count": _resolve_preset_output_column_count(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_column_count": _resolve_preset_output_column_count(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_columns": _resolve_preset_output_columns(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_columns_sha256": _resolve_preset_output_columns_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_schema": PRESET_OUTPUT_SHAPE_SCHEMA,
                    "output_shape_fields": _resolve_preset_output_shape_fields(),
                    "output_shape_payload": _resolve_preset_output_shape_payload(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json": _resolve_preset_output_shape_payload_json(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_bytes": _resolve_preset_output_shape_payload_json_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256": _resolve_preset_output_shape_payload_json_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_payload_json_sha256_algo": _resolve_preset_output_shape_payload_json_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple": _resolve_preset_output_shape_tuple(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_tuple_bytes": _resolve_preset_output_shape_tuple_bytes(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256": _resolve_preset_output_shape_sha256(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "output_shape_sha256_algo": _resolve_preset_output_shape_sha256_algo(
                        args.list_presets_format,
                        with_schema_column=args.summary_tsv_with_schema_column,
                    ),
                    "preset_file": str(args.preset_file),
                    "presets": resolved_presets,
                    "filtered_count": len(filtered_presets),
                    "emitted_count": len(resolved_presets),
                    "output_record_count": len(resolved_presets),
                    "output_is_empty": len(resolved_presets) == 0,
                    "output_is_single_record": len(resolved_presets) == 1,
                    "output_has_multiple_records": len(resolved_presets) > 1,
                    "output_truncated_count": 0,
                    "truncated": truncated,
                    "name_filter_mode": resolved_list_presets_name_filter_mode,
                    "name_filter_mode_requested": list_presets_name_filter_mode_requested,
                    "name_filter_mode_alias_resolved": list_presets_name_filter_mode_alias_resolved,
                    "name_not_filter_mode": resolved_list_presets_name_not_filter_mode,
                    "name_not_filter_mode_requested": list_presets_name_not_filter_mode_requested,
                    "name_not_filter_mode_alias_resolved": list_presets_name_not_filter_mode_alias_resolved,
                    "name_case_sensitive": args.list_presets_name_case_sensitive,
                    "name_contains": name_contains_raw or None,
                    "name_not_contains": name_not_contains_raw or None,
                    "name_values": name_values,
                    "name_not_values": name_not_values,
                    "tag_match": resolved_list_presets_tag_match,
                    "tag_match_requested": list_presets_tag_match_requested,
                    "tag_match_alias_resolved": list_presets_tag_match_alias_resolved,
                    "tag_filter_mode": resolved_list_presets_tag_filter_mode,
                    "tag_filter_mode_requested": list_presets_tag_filter_mode_requested,
                    "tag_filter_mode_alias_resolved": list_presets_tag_filter_mode_alias_resolved,
                    "tag_not_match": resolved_list_presets_tag_not_match,
                    "tag_not_match_requested": list_presets_tag_not_match_requested,
                    "tag_not_match_alias_resolved": list_presets_tag_not_match_alias_resolved,
                    "tag_not_filter_mode": resolved_list_presets_tag_not_filter_mode,
                    "tag_not_filter_mode_requested": list_presets_tag_not_filter_mode_requested,
                    "tag_not_filter_mode_alias_resolved": list_presets_tag_not_filter_mode_alias_resolved,
                    "tag_case_sensitive": args.list_presets_tag_case_sensitive,
                    "tag_filter": tag_filter_raw or None,
                    "tag_not_filter": tag_not_filter_raw or None,
                    "tag_values": required_tags_sorted,
                    "tag_not_values": excluded_tags_sorted,
                    "sort": resolved_list_presets_sort,
                    "sort_requested": list_presets_sort_requested,
                    "sort_alias_resolved": list_presets_sort_alias_resolved,
                    "sort_family": list_presets_sort_info["sort_family"],
                    "sort_tag": list_presets_sort_info["sort_tag"],
                    "sort_direction": list_presets_sort_info["sort_direction"],
                    "sort_is_desc": list_presets_sort_info["sort_is_desc"],
                }
                if args.list_presets_with_meta:
                    payload["meta"] = list_meta_payload
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0
            if args.list_presets_format == "summary":
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved = resolve_preset_with_defaults(preset)
                    print(_format_preset_summary_line(name, resolved))
                if args.list_presets_with_meta:
                    _emit_list_presets_text_meta(
                        len(filtered_presets),
                        len(preset_names),
                        truncated,
                        schema_id=list_meta_schema_id,
                        output_format=args.list_presets_format,
                        extra_fields=list_meta_extra_fields,
                        meta_format=args.list_presets_meta_format,
                        json_schema_version=list_meta_json_schema_version,
                    )
                return 0
            if args.list_presets_format == "summary-tsv":
                _emit_preset_summary_tsv_header(
                    args.summary_tsv_with_schema_header,
                    args.summary_tsv_description,
                    args.summary_tsv_with_schema_column,
                    schema_id,
                )
                for name in preset_names:
                    preset = filtered_presets[name]
                    if not isinstance(preset, dict):
                        raise ValueError(f"{args.preset_file}: presets.{name} must be an object")
                    resolved = resolve_preset_with_defaults(preset)
                    print(
                        _format_preset_summary_tsv_row(
                            name,
                            resolved,
                            description_mode=args.summary_tsv_description,
                            with_schema_column=args.summary_tsv_with_schema_column,
                            schema_id=schema_id,
                            description_max_len=args.summary_tsv_description_max_len,
                        )
                    )
                if args.list_presets_with_meta:
                    _emit_list_presets_text_meta(
                        len(filtered_presets),
                        len(preset_names),
                        truncated,
                        schema_id=list_meta_schema_id,
                        output_format=args.list_presets_format,
                        extra_fields=list_meta_extra_fields,
                        meta_format=args.list_presets_meta_format,
                        json_schema_version=list_meta_json_schema_version,
                    )
                return 0
            for name in preset_names:
                print(name)
            if args.list_presets_with_meta:
                _emit_list_presets_text_meta(
                    len(filtered_presets),
                    len(preset_names),
                    truncated,
                    schema_id=list_meta_schema_id,
                    output_format=args.list_presets_format,
                    extra_fields=list_meta_extra_fields,
                    meta_format=args.list_presets_meta_format,
                    json_schema_version=list_meta_json_schema_version,
                )
            return 0

        if args.task_set_json is None:
            raise ValueError("task_set_json is required (or use --list-presets)")

        preset: dict[str, Any] = {}
        if args.preset:
            preset = load_preset_config(args.preset_file, args.preset)

        models_raw = args.models if args.models is not None else preset.get("models")
        conditions_raw = (
            args.prompt_conditions
            if args.prompt_conditions is not None
            else preset.get("prompt_conditions")
        )
        if not isinstance(models_raw, str) or not models_raw.strip():
            raise ValueError("--models is required (or provide preset.models)")
        if not isinstance(conditions_raw, str) or not conditions_raw.strip():
            raise ValueError("--prompt-conditions is required (or provide preset.prompt_conditions)")

        repeats = args.repeats if args.repeats is not None else int(preset.get("repeats", 1))
        max_total_runs = (
            args.max_total_runs if args.max_total_runs is not None else int(preset.get("max_total_runs", 0))
        )
        max_total_runs_mode = (
            args.max_total_runs_mode
            if args.max_total_runs_mode is not None
            else str(preset.get("max_total_runs_mode", "fail"))
        )
        max_runs_per_model = (
            args.max_runs_per_model if args.max_runs_per_model is not None else int(preset.get("max_runs_per_model", 0))
        )
        max_runs_per_prompt_condition = (
            args.max_runs_per_prompt_condition
            if args.max_runs_per_prompt_condition is not None
            else int(preset.get("max_runs_per_prompt_condition", 0))
        )
        max_runs_per_task = (
            args.max_runs_per_task if args.max_runs_per_task is not None else int(preset.get("max_runs_per_task", 0))
        )
        max_runs_per_task_model = (
            args.max_runs_per_task_model
            if args.max_runs_per_task_model is not None
            else int(preset.get("max_runs_per_task_model", 0))
        )
        max_runs_per_task_prompt_condition = (
            args.max_runs_per_task_prompt_condition
            if args.max_runs_per_task_prompt_condition is not None
            else int(preset.get("max_runs_per_task_prompt_condition", 0))
        )
        cheap_first = args.cheap_first if args.cheap_first is not None else bool(preset.get("cheap_first", False))
        fair_model_allocation = (
            args.fair_model_allocation
            if args.fair_model_allocation is not None
            else bool(preset.get("fair_model_allocation", False))
        )

        if repeats < 1:
            raise ValueError("--repeats must be >= 1")
        if max_total_runs < 0:
            raise ValueError("--max-total-runs must be >= 0")
        if max_total_runs_mode not in {"fail", "cap"}:
            raise ValueError("--max-total-runs-mode must be one of: fail, cap")
        if max_runs_per_model < 0:
            raise ValueError("--max-runs-per-model must be >= 0")
        if max_runs_per_prompt_condition < 0:
            raise ValueError("--max-runs-per-prompt-condition must be >= 0")
        if max_runs_per_task < 0:
            raise ValueError("--max-runs-per-task must be >= 0")
        if max_runs_per_task_model < 0:
            raise ValueError("--max-runs-per-task-model must be >= 0")
        if max_runs_per_task_prompt_condition < 0:
            raise ValueError("--max-runs-per-task-prompt-condition must be >= 0")

        task_set = load_json(args.task_set_json)
        task_set_id, tasks = validate_task_set(task_set, args.task_set_json)

        models = _dedupe_keep_order(parse_csv_list(models_raw, "--models"))
        conditions = _dedupe_keep_order(parse_csv_list(conditions_raw, "--prompt-conditions"))

        if cheap_first:
            models = sorted(models, key=_cheap_first_rank)

        plan: list[dict[str, Any]] = []
        run_index = 0
        model_cursor = 0
        stop_planning = False

        runs_per_model: dict[str, int] = {model: 0 for model in models}

        def total_cap_reached() -> bool:
            return bool(max_total_runs and len(plan) >= max_total_runs)

        def iter_models() -> list[str]:
            nonlocal model_cursor
            if not fair_model_allocation or len(models) <= 1:
                return models
            min_runs = min(runs_per_model.values())
            # Prioritize currently under-allocated models first, then retain cheap-first/base order.
            under_allocated = [m for m in models if runs_per_model[m] == min_runs]
            if len(under_allocated) == len(models):
                # All tied: rotate to avoid deterministic first-model stickiness.
                ordered = models[model_cursor:] + models[:model_cursor]
                model_cursor = (model_cursor + 1) % len(models)
                return ordered
            ordered = sorted(models, key=lambda m: (runs_per_model[m], models.index(m)))
            return ordered
        runs_per_prompt_condition: dict[str, int] = {condition: 0 for condition in conditions}
        runs_per_task: dict[str, int] = {task["task_id"]: 0 for task in tasks}
        runs_by_task_model: dict[str, dict[str, int]] = {
            task["task_id"]: {model: 0 for model in models} for task in tasks
        }
        runs_by_model_prompt_condition: dict[str, dict[str, int]] = {
            model: {condition: 0 for condition in conditions} for model in models
        }
        runs_by_task_prompt_condition: dict[str, dict[str, int]] = {
            task["task_id"]: {condition: 0 for condition in conditions} for task in tasks
        }
        runs_by_repeat_index: dict[str, int] = {str(rep): 0 for rep in range(1, repeats + 1)}
        if max_runs_per_prompt_condition:
            # Condition-first expansion keeps per-condition caps from starving later models.
            for condition in conditions:
                if stop_planning:
                    break
                for task in tasks:
                    if stop_planning:
                        break
                    for rep in range(1, repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if max_runs_per_model and runs_per_model[model] >= max_runs_per_model:
                                continue
                            if runs_per_prompt_condition[condition] >= max_runs_per_prompt_condition:
                                continue
                            if max_runs_per_task and runs_per_task[task["task_id"]] >= max_runs_per_task:
                                continue
                            if (
                                max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= max_runs_per_task_model
                            ):
                                continue
                            if (
                                max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
                            runs_by_repeat_index[str(rep)] += 1
                            plan.append(
                                {
                                    "run_id": f"run-{run_index:04d}",
                                    "task_id": task["task_id"],
                                    "source": task["source"],
                                    "model": model,
                                    "prompt_condition": condition,
                                    "repeat_index": rep,
                                }
                            )
        else:
            # Default expansion order (no per-prompt cap): condition -> task -> repeat -> model.
            # Keeping model iteration innermost lets fair_model_allocation rotate continuously,
            # reducing model skew when other caps (e.g., task×prompt) truncate candidate runs.
            for condition in conditions:
                if stop_planning:
                    break
                for task in tasks:
                    if stop_planning:
                        break
                    for rep in range(1, repeats + 1):
                        if stop_planning:
                            break
                        for model in iter_models():
                            if total_cap_reached() and max_total_runs_mode == "cap":
                                stop_planning = True
                                break
                            if max_runs_per_model and runs_per_model[model] >= max_runs_per_model:
                                continue
                            if max_runs_per_task and runs_per_task[task["task_id"]] >= max_runs_per_task:
                                continue
                            if (
                                max_runs_per_task_model
                                and runs_by_task_model[task["task_id"]][model] >= max_runs_per_task_model
                            ):
                                continue
                            if (
                                max_runs_per_task_prompt_condition
                                and runs_by_task_prompt_condition[task["task_id"]][condition]
                                >= max_runs_per_task_prompt_condition
                            ):
                                continue
                            run_index += 1
                            runs_per_model[model] += 1
                            runs_per_prompt_condition[condition] += 1
                            runs_per_task[task["task_id"]] += 1
                            runs_by_task_model[task["task_id"]][model] += 1
                            runs_by_model_prompt_condition[model][condition] += 1
                            runs_by_task_prompt_condition[task["task_id"]][condition] += 1
                            runs_by_repeat_index[str(rep)] += 1
                            plan.append(
                                {
                                    "run_id": f"run-{run_index:04d}",
                                    "task_id": task["task_id"],
                                    "source": task["source"],
                                    "model": model,
                                    "prompt_condition": condition,
                                    "repeat_index": rep,
                                }
                            )

        if max_total_runs_mode == "fail" and max_total_runs and len(plan) > max_total_runs:
            raise ValueError(
                f"planned runs ({len(plan)}) exceed --max-total-runs ({max_total_runs}); "
                "reduce models/conditions/repeats or increase cap, or use --max-total-runs-mode cap"
            )

        potential_runs_per_model = len(tasks) * len(conditions) * repeats
        potential_runs_total = potential_runs_per_model * len(models)
        potential_runs_per_condition = len(tasks) * len(models) * repeats
        potential_runs_per_task = len(models) * len(conditions) * repeats
        skipped_runs_by_model = {
            model: max(0, potential_runs_per_model - runs_per_model[model]) for model in models
        }
        skipped_runs_by_prompt_condition = {
            condition: max(0, potential_runs_per_condition - runs_per_prompt_condition[condition])
            for condition in conditions
        }
        skipped_runs_by_task = {
            task_id: max(0, potential_runs_per_task - runs_per_task[task_id])
            for task_id in runs_per_task
        }
        potential_runs_per_model_prompt_condition = len(tasks) * repeats
        potential_runs_by_model_prompt_condition = {
            model: {condition: potential_runs_per_model_prompt_condition for condition in conditions}
            for model in models
        }
        skipped_runs_by_model_prompt_condition = {
            model: {
                condition: max(
                    0,
                    potential_runs_by_model_prompt_condition[model][condition]
                    - runs_by_model_prompt_condition[model][condition],
                )
                for condition in conditions
            }
            for model in models
        }
        potential_runs_per_task_model = len(conditions) * repeats
        potential_runs_by_task_model = {
            task["task_id"]: {model: potential_runs_per_task_model for model in models}
            for task in tasks
        }
        skipped_runs_by_task_model = {
            task_id: {
                model: max(0, potential_runs_by_task_model[task_id][model] - runs_by_task_model[task_id][model])
                for model in models
            }
            for task_id in runs_by_task_model
        }
        potential_runs_per_task_prompt_condition = len(models) * repeats
        potential_runs_by_task_prompt_condition = {
            task["task_id"]: {condition: potential_runs_per_task_prompt_condition for condition in conditions}
            for task in tasks
        }
        skipped_runs_by_task_prompt_condition = {
            task_id: {
                condition: max(
                    0,
                    potential_runs_by_task_prompt_condition[task_id][condition]
                    - runs_by_task_prompt_condition[task_id][condition],
                )
                for condition in conditions
            }
            for task_id in runs_by_task_prompt_condition
        }
        potential_runs_per_repeat_index = len(tasks) * len(models) * len(conditions)
        potential_runs_by_repeat_index = {
            str(rep): potential_runs_per_repeat_index for rep in range(1, repeats + 1)
        }
        skipped_runs_by_repeat_index = {
            repeat_key: max(0, potential_runs_by_repeat_index[repeat_key] - runs_by_repeat_index[repeat_key])
            for repeat_key in runs_by_repeat_index
        }

        planned_run_ratio_total = _safe_ratio(len(plan), potential_runs_total)
        planned_run_ratio_by_model = _ratio_map_1d(runs_per_model, {model: potential_runs_per_model for model in models})
        planned_run_ratio_by_prompt_condition = _ratio_map_1d(
            runs_per_prompt_condition,
            {condition: potential_runs_per_condition for condition in conditions},
        )
        planned_run_ratio_by_task = _ratio_map_1d(runs_per_task, {task_id: potential_runs_per_task for task_id in runs_per_task})
        planned_run_ratio_by_model_prompt_condition = _ratio_map_2d(
            runs_by_model_prompt_condition,
            potential_runs_by_model_prompt_condition,
        )
        planned_run_ratio_by_task_model = _ratio_map_2d(runs_by_task_model, potential_runs_by_task_model)
        planned_run_ratio_by_task_prompt_condition = _ratio_map_2d(
            runs_by_task_prompt_condition,
            potential_runs_by_task_prompt_condition,
        )
        planned_run_ratio_by_repeat_index = _ratio_map_1d(
            runs_by_repeat_index,
            potential_runs_by_repeat_index,
        )

        payload: dict[str, Any] = {
            "schema_version": "v1",
            "task_set_id": task_set_id,
            "generated_at_utc": _utc_now_iso(),
            "config": {
                "preset": args.preset,
                "preset_file": str(args.preset_file) if args.preset else None,
                "models": models,
                "prompt_conditions": conditions,
                "repeats": repeats,
                "cheap_first": bool(cheap_first),
                "fair_model_allocation": bool(fair_model_allocation),
                "max_total_runs": max_total_runs,
                "max_total_runs_mode": max_total_runs_mode,
                "max_runs_per_model": max_runs_per_model,
                "max_runs_per_prompt_condition": max_runs_per_prompt_condition,
                "max_runs_per_task": max_runs_per_task,
                "max_runs_per_task_model": max_runs_per_task_model,
                "max_runs_per_task_prompt_condition": max_runs_per_task_prompt_condition,
            },
            "summary": {
                "task_count": len(tasks),
                "model_count": len(models),
                "prompt_condition_count": len(conditions),
                "unique_call_units": len(tasks) * len(models) * len(conditions),
                "planned_runs_total": len(plan),
                "potential_runs_total": potential_runs_total,
                "skipped_runs_total": max(0, potential_runs_total - len(plan)),
                "planned_run_ratio_total": planned_run_ratio_total,
                "planned_run_ratio_by_model": planned_run_ratio_by_model,
                "planned_run_ratio_by_prompt_condition": planned_run_ratio_by_prompt_condition,
                "planned_run_ratio_by_task": planned_run_ratio_by_task,
                "planned_run_ratio_by_model_prompt_condition": planned_run_ratio_by_model_prompt_condition,
                "planned_run_ratio_by_task_model": planned_run_ratio_by_task_model,
                "planned_run_ratio_by_task_prompt_condition": planned_run_ratio_by_task_prompt_condition,
                "planned_run_ratio_by_repeat_index": planned_run_ratio_by_repeat_index,
                "planned_runs_by_model": runs_per_model,
                "planned_runs_by_prompt_condition": runs_per_prompt_condition,
                "planned_runs_by_task": runs_per_task,
                "planned_runs_by_model_prompt_condition": runs_by_model_prompt_condition,
                "planned_runs_by_task_model": runs_by_task_model,
                "planned_runs_by_task_prompt_condition": runs_by_task_prompt_condition,
                "planned_runs_by_repeat_index": runs_by_repeat_index,
                "potential_runs_by_model": {model: potential_runs_per_model for model in models},
                "potential_runs_by_prompt_condition": {
                    condition: potential_runs_per_condition for condition in conditions
                },
                "potential_runs_by_task": {task_id: potential_runs_per_task for task_id in runs_per_task},
                "potential_runs_by_model_prompt_condition": potential_runs_by_model_prompt_condition,
                "potential_runs_by_task_model": potential_runs_by_task_model,
                "potential_runs_by_task_prompt_condition": potential_runs_by_task_prompt_condition,
                "potential_runs_by_repeat_index": potential_runs_by_repeat_index,
                "skipped_runs_by_model": skipped_runs_by_model,
                "skipped_runs_by_prompt_condition": skipped_runs_by_prompt_condition,
                "skipped_runs_by_task": skipped_runs_by_task,
                "skipped_runs_by_model_prompt_condition": skipped_runs_by_model_prompt_condition,
                "skipped_runs_by_task_model": skipped_runs_by_task_model,
                "skipped_runs_by_task_prompt_condition": skipped_runs_by_task_prompt_condition,
                "skipped_runs_by_repeat_index": skipped_runs_by_repeat_index,
            },
            "plan": plan,
        }

        out = args.output or args.task_set_json.with_suffix("").with_suffix(".batch-plan.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(out)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        emit_error(str(exc), hints=[f"task_set_json={args.task_set_json}" if "args" in locals() else "task_set_json=<unknown>"])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
