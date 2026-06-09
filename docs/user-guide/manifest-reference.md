# Manifest Reference

A catalogue item is a single `manifest.yaml` describing what to build and where
the content comes from. Manifests live at `catalog/<kind>/<name>/manifest.yaml`.

Every manifest is a common **envelope** plus a per-`kind` **`spec`**. Two kinds
exist today: `exporter` (packages: RPM/DEB/Docker) and `dashboard` (Grafana
dashboards). The full, always-valid example is
[`manifest.reference.yaml`](manifest.reference.yaml) — it is parsed by the test
suite on every CI run, so it can never drift from the schema. This page explains
each field; copy from the reference file when authoring a new item.

> Unknown keys are rejected. A typo'd field fails `mh validate` rather than being
> silently ignored.

## Envelope (all kinds)

| Field | Required | Default | Notes |
|---|---|---|---|
| `kind` | yes | — | `exporter` or `dashboard` |
| `name` | yes | — | Unique catalogue id; the package base name (e.g. `node_exporter`) |
| `description` | yes | — | One-line summary |
| `category` | no | `System` | Free text (System, Database, Network, …) |
| `version` | yes | — | Upstream tag **verbatim** — the `v` is kept (the download URL uses it as-is) |
| `license` | no | `null` | SPDX id of the upstream project |

## `kind: exporter`

### `spec.upstream`

| Field | Required | Default | Notes |
|---|---|---|---|
| `type` | yes | — | `github` or `local` |
| `repo` | github only | — | `owner/repo` |
| `strategy` | no | `latest_release` | Only value today; drives the upstream watcher |
| `pin_major` | no | `null` | Int ceiling for auto-bumps (e.g. `1` keeps the item on 1.x) |
| `archive_name` | no | convention | Release asset name override (string or per-arch dict) |
| `local_binary` | local only | — | Vendored binary path (XOR `local_archive`) |
| `local_archive` | local only | — | Vendored archive path (XOR `local_binary`) |

**Archive name placeholders:** `{name}`, `{version}`, `{clean_version}`
(`{version}` without a leading `v`), `{arch}`. Default pattern when omitted:

```yaml
archive_name: "{name}-{clean_version}.linux-{arch}.tar.gz"
```

Per-arch form when upstream names assets inconsistently:

```yaml
archive_name:
  amd64: example_exporter-{clean_version}.linux-amd64.tar.gz
  arm64: example_exporter-{clean_version}.linux-aarch64.tar.gz
```

**Local upstream** (vendored, no GitHub):

```yaml
upstream:
  type: local
  local_binary: assets/example_exporter   # exactly one of local_binary / local_archive
```

### `spec.build`

| Field | Required | Default | Notes |
|---|---|---|---|
| `method` | yes | — | `binary_repack` or `source_build` |
| `binary_name` | yes | — | Executable in the archive → `/usr/bin/<name>` |
| `extra_binaries` | no | `[]` | Additional executables to ship |
| `extra_sources` | no | `[]` | Extra files fetched by URL (`{url, filename}`) |
| `archs` | no | `[amd64, arm64]` | Build architectures |

### `spec.artifacts`

Each of `rpm`, `deb`, `docker` is optional and independent; set `enabled: true`
to publish that artifact type.

**`rpm`** (RHEL/Alma/Rocky) — and **`deb`** (Debian/Ubuntu), which adds
`section` (default `utils`) and `priority` (default `optional`):

| Field | Default | Notes |
|---|---|---|
| `enabled` | `false` | |
| `targets` | rpm `[el9, el10]` / deb `[ubuntu-24.04, ubuntu-26.04, debian-12, debian-13]` | Auto-build set; any string accepted (e.g. `el8` is still buildable by hand) |
| `summary` | `null` | Package summary |
| `install_path` | `null` (rpm only) | Override binary dir (default `/usr/bin`) |
| `dependencies` | `[]` | Extra Requires/Depends |
| `system_user` | `null` | Create a service account |
| `systemd` | see below | Service unit |
| `extra_files` | `[]` | `{source, dest, mode="0644", config=false}` |
| `directories` | `[]` | `{path, mode="0755", owner="root", group="root"}` |

**`systemd`** block: `enabled` (default `false`), `arguments` (`[]`),
`after` (`["network.target"]`), `restart` (`on-failure`), `type` (`simple`).

**`docker`**:

| Field | Default | Notes |
|---|---|---|
| `enabled` | `false` | |
| `base_image` | `registry.access.redhat.com/ubi9/ubi-minimal` | |
| `entrypoint` | `[]` | Image ENTRYPOINT |
| `cmd` | `[]` | Default CMD args |
| `dockerfile` | `null` | Path to a Jinja2 Dockerfile template (relative to the manifest dir) for custom layers; null = generic renderer |
| `validation` | see below | Build-time image smoke check |

**`validation`** block: `enabled` (default `true`), `port` (`null`),
`command` (`null`), `args` (`null`). Use `port` for a TCP probe, or `command`
for a custom check.

## `kind: dashboard`

A dashboard manifest replaces the whole `spec`:

```yaml
kind: dashboard
name: node_exporter_full
description: Node Exporter Full dashboard
category: System
version: "1"
spec:
  datasource: prometheus      # optional (default null)
  tags: [prometheus, node]    # default []
  source:                     # discriminated on `type`; pick exactly one
    type: grafana             # grafana.com revision
    id: 1860
    revision: 37
```

Other `source` types: `url` (`{url}`), `git` (`{repo, ref, path}`),
`local` (`{path}` relative to the manifest dir).

## Validating

```bash
mh validate <name>     # one item
mh validate --all      # the whole catalogue
```

See [Adding Exporters](adding-exporters.md) for a practical walkthrough.
