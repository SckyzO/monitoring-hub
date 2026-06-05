# SP1 — Forge Core: kind-extensible engine + exporter & dashboard kinds + CLI

- **Status:** Approved (design), pending implementation plan
- **Date:** 2026-06-04
- **Scope:** First sub-project (SP1) of the monitoring-hub product rebuild
- **Supersedes:** the engine portion of the old `REFACTOR-PLAN.md`

---

## 1. Context & goals

The current engine (`core/engine/`) is a god object (`builder.py`, 565 lines)
with marshmallow schemas, a duplicated `site_generator` (v1 used locally via
`devctl`, v2 used in CI — local output diverges from prod), and a systemic
`PYTHONPATH=$GITHUB_WORKSPACE; python3 -m core.engine.X` invocation hack (no
installed package). It is not in production and has no real users yet, so a
greenfield rewrite is on the table without backward-compat constraints.

SP1 delivers the **foundation** every other sub-project depends on: a clean,
typed, **kind-extensible** engine that turns reference manifests into
distributable artifacts and a kind-agnostic `catalog.json`, exposed through an
**installable CLI**. It proves the kind abstraction with **two deliberately
different kinds** (`exporter` and `dashboard`).

Goals:

1. Replace the god object with layered, testable modules.
2. Make "item kind" a first-class extension point (registry), so adding kinds
   later is additive — no core changes. This keeps the door open to the broader
   "software factory" ambition without speculative work now.
3. Ship an installable `mh` CLI (no repo clone needed to build/customize).
4. First-class, update-safe customization via override-overlay.
5. Lock behavior with golden tests so later sub-projects can't regress it.

Non-goals: see §3 (out of scope).

---

## 2. Product vision (recap) & decomposition

Full vision lives in the workspace-level `ROADMAP.md`. Summary:

- **Ambition:** a complete **monitoring catalogue** (exporters, dashboards,
  alert rules, stacks), with the core designed to later generalize into a
  "software factory" (any tool packaged from a manifest) — **without a core
  rewrite**.
- **Audience:** both public open-source catalogue **and** offline-first
  (air-gapped / HPC), treated equally.
- **Consumption pillars:** (1) signed apt/yum repos, (2) Docker/OCI images,
  (3) browse + copy web catalogue, (4) downloadable manifests/bundles,
  (5) **offline bundle generator** (the differentiator).

Sub-projects (dependency order):

| SP | Content | Depends on |
|---|---|---|
| **SP1** | Core + catalogue + kinds `exporter`/`dashboard` + CLI `mh` | — |
| SP2 | Distribution: signed apt/yum repos, OCI publish, catalog serving | SP1 |
| SP3 | Offline bundler: `mh bundle`, **bundle recipe** format, archives | SP1 + SP2 |
| SP4 | Website (React+Vite CSR) consuming `catalog.json` + Cosmos | SP1 |
| SP5 | Additional kinds: `alert-rule`, `stack`; collection import | SP1 |
| SP6 | Software-factory kinds, in-browser zip, backend build service | SP1–5 |

---

## 3. Scope of SP1

**In scope:**

- Domain models (Pydantic v2): manifest envelope + per-kind `spec` (discriminated
  union), `Artifact`, `CatalogEntry`, `BundleRecipe` (model stub only).
- Kind registry (in-tree, decorator, auto-discovery).
- Two producers: `exporter` (RPM/DEB via nfpm + Docker + GPG sign) and
  `dashboard` (fetch/validate JSON; no OS packaging).
- Manifest source resolution: published catalogue, local file, local dir.
- Override-overlay (both `--set` and `*.override.yaml`), update-safe.
- `catalog.json` generation (kind-agnostic, `schema_version`).
- CLI `mh`: `validate`, `pull`, `build`, `catalog build`, `list`.
- Tooling: uv + hatchling, ruff, mypy --strict, pytest, container-first.

**Out of scope (YAGNI, explicit):**

- Offline bundler `mh bundle` + recipe generation (SP3 — seam reserved only).
- apt/yum repo metadata + OCI publishing + gh-pages serving (SP2).
- Website (SP4).
- Kinds beyond exporter/dashboard, `stack` meta-kind, collection import (SP5).
- Backend build service, in-browser zip (SP6).

---

## 4. Architecture

Dependencies point inward; `domain/` depends on nothing.

```
cli/  →  sources/ · catalog/ · kinds/  →  domain/
                          ↑
                    packaging/ (adapters: nfpm, docker, sign)
```

| Layer | Role | Depends on |
|---|---|---|
| `domain/` | Pure Pydantic models (Manifest, per-kind specs, Artifact, CatalogEntry, BundleRecipe stub). No I/O. The contract. | nothing |
| `kinds/` | Registry (`@register("exporter")`) + one producer per kind. `Producer` protocol: `validate → build → (artifacts, CatalogEntry)`. | domain |
| `packaging/` | Tooling adapters: nfpm wrapper (RPM/DEB), Docker build, GPG sign. Used by the exporter producer. | domain |
| `sources/` | Manifest resolution (published catalogue / local file / local dir) + overlay application. | domain |
| `catalog/` | Assemble `CatalogEntry` objects into `catalog.json` (kind-agnostic). | domain |
| `cli/` | Click commands (`mh`), thin orchestration. | all |

Rule of layers: `domain/` models neither download nor sign. The exporter
producer *uses* `packaging/` but `packaging/` does not know about kinds → no
cross-coupling. This is what dismantles the current god object.

---

## 5. Package structure (src layout)

Import package name: **`forge`** (product-neutral, durable; product/brand and
distribution names may evolve independently).

```
monitoring-hub/
  pyproject.toml              # uv + hatchling; console_scripts: mh = forge.cli.main:cli
  src/forge/
    domain/    manifest.py · kinds.py · catalog.py · artifact.py · recipe.py(stub, SP3)
    kinds/     registry.py · base.py · exporter.py · dashboard.py
    sources/   resolver.py · overlay.py
    packaging/ nfpm.py · docker.py · sign.py
    catalog/   builder.py        # generates catalog.json
    cli/       main.py
  catalog/                       # THE DATA (reference manifests), public catalogue source
    exporters/<name>/manifest.yaml
    dashboards/<name>/manifest.yaml
  tests/                         # fixtures = manifests, golden = expected outputs
```

The installable `mh` comes from `console_scripts` → eliminates the
`PYTHONPATH`/`python3 -m core.engine.X` hack. CI calls the same `mh` as local.

---

## 6. Domain model

### 6.1 Manifest = common envelope + per-kind `spec` (discriminated union)

```python
class ManifestBase(BaseModel):        # shared by all kinds
    kind: str
    name: str
    description: str
    category: str
    version: str
    license: str | None = None

class ExporterManifest(ManifestBase):
    kind: Literal["exporter"]
    spec: ExporterSpec     # upstream, build, RPM/DEB/Docker targets

class DashboardManifest(ManifestBase):
    kind: Literal["dashboard"]
    spec: DashboardSpec    # source (grafana id / url / git / local), datasource, tags

Manifest = Annotated[ExporterManifest | DashboardManifest, Field(discriminator="kind")]
```

Adding a kind = a new `ManifestBase` subclass + a producer. No core change.

### 6.2 Layering fix: drop `new`/`updated` from the manifest

The current marshmallow `ManifestSchema` carries `new`/`updated` booleans —
catalog *state* leaking into a domain object. These move out: they become
**state computed at catalog-build time** (diff against the previous
`catalog.json`), carried by `CatalogEntry`, never the manifest.

### 6.3 Artifact (output model)

`Artifact` is distinct from `kind` (cardinality 1 kind → N artifacts). An
exporter yields many artifacts (RPM el8/el9/el10 × arch, DEB, Docker image); a
dashboard yields one. Shape:

```python
class Artifact(BaseModel):
    type: str        # rpm | deb | docker-image | grafana-dashboard | ...
    target: str | None = None   # el9, ubuntu-24.04, ...
    arch: str | None = None
    url: str | None = None      # populated at publish time (SP2)
    sha256: str
    signed: bool = False
```

### 6.4 BundleRecipe (stub, SP3)

`domain/recipe.py` defines `BundleRecipe` (a selection of `{kind, name,
version}` + overlay refs + checksums) as a model placeholder so SP3 plugs in
without touching the core. **Not built in SP1.**

---

## 7. Kinds: exporter & dashboard

Catalogue items are populated by **reference manifests** — small pointers +
curation metadata. Content is never vendored; the producer fetches the source
at build time (same pattern as exporters referencing `upstream.repo`).
Granularity: **one manifest per item** (curated; independent versioning).

### 7.1 exporter producer

`upstream` (httpx) → download binary → repack via **nfpm** (RPM/DEB) → build
Docker image → GPG sign → emit `[Artifact]` + `CatalogEntry`. Uses
`packaging/` adapters.

### 7.2 dashboard producer

Resolve `spec.source` → validate JSON → emit a `grafana-dashboard` Artifact +
`CatalogEntry`. **No OS packaging** (this is the abstraction stress test).

Source shapes (per kind):

- `grafana` — `{id, revision}` → grafana.com download API
- `url` — raw https URL
- `git` — `{repo, ref, path}` (another git repo)
- `local` — in-tree path (fallback)

Examples:

```yaml
kind: dashboard
name: node-overview
description: Node Exporter Full
category: System
version: "39"                 # pinned grafana.com revision
spec:
  source: { type: grafana, id: 1860, revision: 39 }
  datasource: prometheus
```

```yaml
kind: alert-rule              # (SP5; shown for source-shape illustration)
name: node-alerts
description: Node exporter alerting rules
category: System
version: v1.8.0
spec:
  source: { type: git, repo: you/monitoring-rules, ref: v1.8.0, path: rules/node.yml }
```

---

## 8. Override-overlay (update-safe, both forms in v1)

```
mh build node_exporter --set spec.targets.rpm.install_path=/usr/local/bin
# or node_exporter.override.yaml (partial mapping)
```

Mechanism: resolve base manifest → **deep-merge** overlay → **validate the
EFFECTIVE manifest** with Pydantic. Validating the result (not the base) makes
an invalid override **fail loudly** (no silent default). The overlay patches by
**field path**, so it survives upstream manifest updates; an overlay targeting a
removed field raises a **clear error** (no silent ignore). Bundle recipes (SP3)
may reference overlays → custom bundles stay reproducible.

---

## 9. Registry (in-tree, no central list)

```python
# kinds/base.py
class Producer(Protocol):
    kind: str
    def validate(self, m: Manifest) -> None: ...
    def build(self, m: Manifest, ctx: BuildContext) -> BuildResult: ...  # [Artifact] + CatalogEntry
```

`@register("exporter")` populates a dict; `get_producer(kind)` returns the
instance. Modules in `kinds/` are **auto-imported** (pkgutil) so registration
happens on import — **no central list to edit** per new kind ("extensibility
without modifying the core").

---

## 10. catalog.json contract

```json
{ "schema_version": 1, "generated_at": "...", "items": [
  {"kind":"exporter","name":"node_exporter","version":"1.11.1","category":"System",
   "artifacts":[{"type":"rpm","target":"el9","arch":"x86_64","sha256":"…","signed":true}]},
  {"kind":"dashboard","name":"node-overview","version":"39","category":"System",
   "artifacts":[{"type":"grafana-dashboard","sha256":"…"}]} ]}
```

Uniform envelope + per-item `artifacts[]` (the `Artifact` model). Website and
bundler consume it identically. `schema_version` for forward compatibility.

---

## 11. CLI surface (`mh`)

| Command | Role | Usage |
|---|---|---|
| `mh validate <item\|path\|--all>` | Pydantic schema + producer semantic validation | CI on PRs; aggregates all errors (not fail-fast) |
| `mh pull <item>` | fetch a manifest from the published catalogue to local | customization entry point |
| `mh build <item\|path> [--set …] [--overlay f]` | build one item's artifacts locally; apply overlay | local + CI |
| `mh catalog build` | assemble `catalog.json` from manifests + build results | CI publish |
| `mh list [--kind exporter]` | list catalogue items | terminal |

An *item reference* = a catalogue name **or** a manifest path. Human-readable
output by default, `--json` where CI needs it. **Non-zero exit** on
validation/build failure.

---

## 12. Versioning & update detection

Manifests **pin** an exact version (release tag / grafana revision / git ref) →
reproducible (critical for offline bundles). The `watcher` becomes
**kind-aware** via the same registry:

- exporter → poll GitHub releases (already the case)
- grafana → poll the revisions API
- git → poll the ref / latest tag
- url → ETag / checksum

It opens **bump PRs** like exporters do, reusing the signed App-token pipeline.
Per-source version-retrieval conventions are **deferred to kind
standardization** (see §17).

---

## 13. Data flow (build one item)

```
manifest.yaml (+ overlay?) → sources.resolver (load + merge)
  → Pydantic validate → Manifest (discriminated by kind)
  → registry.get_producer(kind) → producer.validate → producer.build
  → BuildResult: [Artifact…] + CatalogEntry
  → catalog.builder → catalog.json
```

---

## 14. Error handling

- Typed hierarchy: `ForgeError` → `ManifestError`, `SourceResolutionError`,
  `BuildError`, `SigningError`. CLI catches at top level, prints the real
  cause, exits non-zero.
- **Wrap the operation that can fail, not the one that follows.** No `except`
  that swallows and returns a default; no `defaultdict`-style masking.
- Overlay targeting a removed field → clear error.
- `mh validate` aggregates all Pydantic errors into one actionable report
  (which item, which field).

---

## 15. Testing strategy (TDD, container-first)

- **Unit tests per layer:** domain models (validation, discriminated union,
  overlay deep-merge), registry (register/get/auto-discovery), each producer
  (I/O mocked).
- **Fixtures = manifests:** a representative set (exporter with systemd,
  exporter with dict `archive_name`, dashboard from grafana, alert from git).
- **Golden tests:** for a manifest + pinned inputs, produced artifacts /
  `CatalogEntry` match a committed golden (catalog.json snapshot, nfpm config,
  rendered systemd unit) → zero-regression guarantee and locked contract.
- **Injected I/O:** producers receive adapters (httpx client, nfpm/docker
  runner) → fakes in tests, **no network** in unit tests.
- **Gates:** `mypy --strict` + `ruff` + `pytest-cov`, run via `make test` in
  the dev image.
- **One integration canary in CI:** real node_exporter RPM build + install-test
  in a container (reuses the current canary concept).

---

## 16. Tooling & conventions

- Package manager: `uv`; build backend: `hatchling` (PEP 517).
- Lint/format: `ruff`. Type: `mypy --strict`. Test: `pytest` (+xdist, +cov).
- CLI: `Click`. HTTP: `httpx`. Retries: `tenacity`.
- Packaging: `nfpm` for RPM/DEB (replaces ~650 lines of Jinja templates).
- **Container-first:** all tooling runs in the dev image; nothing on host.
- `console_scripts: mh = forge.cli.main:cli`.

---

## 17. Deferred / to standardize

- **Dashboard `preview`/screenshot** field — for the website browse experience;
  standardize at the `dashboard` kind level.
- **Per-source version retrieval** (dashboards/alerts) — grafana revision / git
  ref / url ETag; formalize when standardizing kinds.
- **CLI name** — `mh` vs `forge` (consistency with the package). Defaulting to
  `mh`; confirm later.
- **Collection import** (one manifest → many items from a repo) — SP5, seam
  reserved.

---

## 18. Repo strategy

Same repo, **greenfield `src/forge/`**: `git rm` the old engine, write fresh.
Keep the signed App-token pipeline, GPG/OIDC secrets, branch protection. The
`.git` bloat (853 MB) is **orthogonal** — a separate `filter-repo` purge if a
clean history is wanted, decided independently.

---

## 19. Open questions / risks

- Portal-side custom build (SP3): assemble pre-built artifacts (static-site
  friendly) vs build-on-demand (needs a backend). Decided in SP3.
- nfpm coverage of "special" exporters (extra files, directories, system users,
  custom systemd) — validate via a POC across a representative set during SP1
  implementation; fall back to templates only where nfpm cannot express a case.
- `stack` meta-kind (references other items) intentionally excluded from SP1 to
  avoid premature composition complexity.
