"""Override-overlay deep-merge + --set parsing (spec §8)."""

from __future__ import annotations

import pytest

from forge.domain.errors import SourceResolutionError
from forge.sources.overlay import apply_set_overrides, deep_merge, parse_set_override


def test_deep_merge_recurses_into_nested_mappings() -> None:
    base = {"spec": {"build": {"method": "binary_repack"}, "version": "1.0"}}
    overlay = {"spec": {"build": {"binary_name": "node_exporter"}}}
    merged = deep_merge(base, overlay)
    assert merged == {
        "spec": {
            "build": {"method": "binary_repack", "binary_name": "node_exporter"},
            "version": "1.0",
        }
    }


def test_deep_merge_overlay_scalar_replaces_base() -> None:
    base = {"spec": {"version": "1.0"}}
    overlay = {"spec": {"version": "2.0"}}
    assert deep_merge(base, overlay) == {"spec": {"version": "2.0"}}


def test_deep_merge_replaces_lists_not_concatenates() -> None:
    base = {"spec": {"targets": ["el8", "el9"]}}
    overlay = {"spec": {"targets": ["el10"]}}
    assert deep_merge(base, overlay) == {"spec": {"targets": ["el10"]}}


def test_deep_merge_does_not_mutate_inputs() -> None:
    base = {"spec": {"a": 1}}
    overlay = {"spec": {"b": 2}}
    deep_merge(base, overlay)
    assert base == {"spec": {"a": 1}}
    assert overlay == {"spec": {"b": 2}}


def test_parse_set_override_builds_nested_dict() -> None:
    result = parse_set_override("spec.build.binary_name=node_exporter")
    assert result == {"spec": {"build": {"binary_name": "node_exporter"}}}


def test_parse_set_override_yaml_types_the_value() -> None:
    assert parse_set_override("spec.artifacts.rpm.enabled=true") == {
        "spec": {"artifacts": {"rpm": {"enabled": True}}}
    }
    assert parse_set_override("spec.source.revision=39") == {"spec": {"source": {"revision": 39}}}


def test_parse_set_override_keeps_slash_path_as_string() -> None:
    result = parse_set_override("spec.install_path=/usr/local/bin")
    assert result == {"spec": {"install_path": "/usr/local/bin"}}


def test_parse_set_override_without_equals_raises() -> None:
    with pytest.raises(SourceResolutionError):
        parse_set_override("spec.build.binary_name")


def test_parse_set_override_empty_key_segment_raises() -> None:
    with pytest.raises(SourceResolutionError):
        parse_set_override("spec..binary_name=x")


def test_apply_set_overrides_merges_multiple_in_order() -> None:
    base = {"spec": {"version": "1.0"}}
    merged = apply_set_overrides(
        base,
        ['spec.version="2.0"', "spec.build.binary_name=x"],
    )
    assert merged == {"spec": {"version": "2.0", "build": {"binary_name": "x"}}}
