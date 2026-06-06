"""Override-overlay deep-merge + --set parsing (spec §8)."""

from __future__ import annotations

from forge.sources.overlay import deep_merge


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
