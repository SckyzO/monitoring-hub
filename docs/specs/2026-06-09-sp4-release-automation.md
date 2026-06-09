# SP4 — Release automation (upstream watcher → signed bump PRs → continuous publish)

> Sub-project 4 of the forge-engine refactor. Depends on SP1 (core + catalogue +
> `exporter`/`dashboard` kinds + `mh` CLI) and SP2 (signed apt/yum repos, OCI,
> catalog serving) — both complete and merged. SP3 (offline bundler) is also
> merged but not a dependency. Greenfield big-bang exception applies (no external
> users yet; gh-pages mirror kept for apt/yum source backward-compat).

---

## 1. Context & goals

The legacy product's defining strength was **continuous, hands-off publishing**:
a cron watched upstream projects, and when an exporter released a new version the
pipeline opened a PR bumping the manifest, then on merge rebuilt and republished
every artefact (rpm/deb/container) automatically. That chain was removed in the
greenfield cutover. As a result **nothing has been published since 2026-05-05**
even though upstreams have shipped new versions, and the new `forge-release.yml`
only ever fires on a manual `release: published` / `workflow_dispatch` — there is
no watcher, no schedule, no bump PRs.

SP4 rebuilds that chain on the forge engine **and improves it**, taking the
refactor as the opportunity to fix the legacy design's weak points:

- **Logic in `mh`, not in bash.** The legacy `build.yml` was 923 lines of shell;
  detection lived in a 127-line `watcher.py` and change-detection in a
  `state_manager.py`. SP4 keeps all decisions inside the typed, tested engine;
  workflows stay thin (`./dev run mh …`).
- **Shift-left validation.** A bad bump must turn the **PR** red and never merge,
  instead of breaking the post-merge publish (legacy behaviour).
- **Parallelism + per-leg failure isolation.** One broken target×arch leg must
  not sink the whole release; the catalogue self-heals.
- **Extensible detection.** Version detection becomes a registry, like producers
  and kinds — adding a new source type is additive, no core change.

Goals:

- A scheduled watcher opens **one signed bump PR per outdated item**; its CI
  builds the real packages **unsigned** (throwaway) to prove the bump is sound;
  auto-merge only on green.
- Post-merge, the changed item is rebuilt **signed** and published to
  Pages ‖ Releases ‖ GHCR **‖ Docker Hub**, with publishing serialized so
  concurrent merges never corrupt the catalogue.
- Builds are **parallel per item** (and per target×arch); a failed leg is
  published-around and **reconciled** (retried) by the next scheduled run —
  derived from `expected − present`, with no mutable failure state on disk.
- First real forge-published releases land, unfreezing the catalogue.

Non-goals (later sub-projects): website consuming the live catalogue (SP5);
Helm chart publishing (SP6, own brainstorm); optional Pulp/Nexus `Publisher`
target (SP6+); a build-history/analytics backend or API (deferred — see §11).

---

## 2. The central constraint (signing keys must never reach PR CI)

The release signing key (`GPG_PRIVATE_KEY` / `GPG_PASSPHRASE`) and registry
credentials are repo secrets. **A PR from a bump branch must be able to build but
must never see those secrets** (PR CI is the natural place for untrusted/forkable
input, and a leak there is unrecoverable). This is the load-bearing constraint
that shapes the whole loop:

- **In the bump PR:** build the real rpm/deb/container for the bumped item, but
  **unsigned**, with artefacts discarded after the run. This validates that the
  new version builds without ever exposing a key. A broken bump → PR red → no
  merge.
- **Post-merge on `main`:** the item is **already pinned** to the new version
  (the merged manifest), so the signed rebuild is **deterministic** — it produces
  the same bytes the PR validated, now signed and published.

This split is why the bump carries the **pinned version** (not "latest"): it makes
the post-merge rebuild reproducible and removes any time-of-check/time-of-use gap.

---

## 3. The loop (end to end)

```
 cron (every 6h, 4×/day)                      on PR merge to main
 ─────────                                    ───────────────────
 mh watch                                     forge-release (per changed item)
   │  detect latest per manifest                │  mh build <ref> (SIGNED)  ── parallel matrix
   │  skip pre-releases                         │     emits entry.json per leg
   │  diff vs pinned version                    │  mh catalog assemble      ── serial join
   ▼                                            │  publish  ─── Pages ‖ Releases ‖ GHCR ‖ Docker Hub
 one bump PR per outdated item                  ▼     (concurrency: serialized, cancel-in-progress:false)
   │  validated manifest write (engine)       updated catalog.json
   │  PR CI: mh build <ref> UNSIGNED  ── shift-left validation
   │  auto-merge if green
   ▼
 (merge) ──────────────────────────────────▶ forge-release
```

Plus a **daily reconcile** (same `forge-release` entrypoint, `workflow_dispatch`
/ schedule) that rebuilds only the **missing** legs (§7).

---

## 4. Detection — extensible `VersionSource` registry

Detection becomes a registry auto-discovered exactly like producers and kinds
(`@register(...)`), so adding a source type never touches the core.

```python
@dataclass(frozen=True)
class DetectedVersion:
    item: str            # manifest name
    kind: str            # exporter | dashboard | ...
    current: str         # pinned version from the manifest (clean)
    latest: str          # detected upstream version (clean)
    source_type: str     # "github-release"
    outdated: bool        # latest > current under the version policy
```

```python
class VersionSource(Protocol):
    type: ClassVar[str]
    def latest(self, manifest: ManifestBase, *, runner: Runner) -> str | None: ...
```

**SP4 ships exactly one source: `github-release`.** Empirically verified: all 32
exporters under management publish proper GitHub Releases (`gh api .../releases/latest`
resolves for every one). A `github-tags` source was considered and **rejected** as
speculative dead code — no managed exporter is tags-only, and
`GET /tags?per_page=1` does not sort by semver anyway, so it would be both unused
and incorrect. Dashboard detectors (`grafana-revision`) and generic
(`url-etag`, `latest-tag`) are deferred to whenever those kinds actually get
watched; they slot in by registration with **zero** core change.

**Version policy** (applied in the registry, source-agnostic):

1. **Skip pre-releases by default** — `latest` ignores any tag matching
   `rc` / `beta` / `alpha` / `-pre` / `dev`. An auto-merging loop must never bump
   to a pre-release. Not configurable off in SP4 (no need).
2. **Optional per-manifest major pin, OFF by default** — a manifest may declare a
   ceiling (e.g. stay on `1.x`); absent the key, behaviour is unchanged, so the
   current 35 manifests bump freely as today. (Concrete key shape decided at
   implementation; reuses the existing `spec.upstream` block.)

> **Doc↔model gap to reconcile (SP4.1):** manifests carry
> `spec.upstream.strategy: latest_release` but `domain/manifest.py`'s `Upstream`
> model has no `strategy` field (currently accepted only because validation is
> lenient there). SP4 either (a) adds `strategy: Literal["latest_release"]` to the
> model and maps it to the `github-release` source, or (b) drops the field from the
> manifests and infers the source from `upstream.type`. Decide and make the model
> and the 35 manifests consistent; `mh validate` must enforce the result.

---

## 5. Build / assemble decoupling (enables parallelism)

Today `mh catalog build` couples two concerns in one loop: it builds every item
**and** writes `catalog.json`. That forces a single sequential job and makes
`catalog.json` a contended output. SP4 splits them:

- **`mh build <ref> --out DIR` (per item, parallelizable):** builds one item and,
  in addition to its artefacts, **persists its `CatalogEntry` as `entry.json`** in
  `DIR`. The build result already carries `.entry` — this just writes it. Emitted
  **only on success** (a failed build writes no `entry.json`).
- **`mh catalog assemble --entries DIR [--previous catalog.json]` (single, cheap
  join):** reads every `entry.json`, merges into the previous catalogue, and
  writes `catalog.json`. Missing item ⇒ keep its previous entry (self-heal, §7).
  `build_catalog(...)` is already pure (diffs `previous` keyed by `(kind, name)`)
  — assemble feeds it the collected entries.

CI structural safety (no half-finished entries assembled): the matrix of
per-item builds is a `needs:` dependency of the single assemble job, so assemble
runs only after all legs have terminated; it consumes only the `entry.json` files
that were actually emitted. Local safety: **`write_catalog` becomes atomic**
(temp file + `os.replace`) — it is currently a bare `path.write_text(...)`
(SP4.0 fix).

`mh catalog build` stays as a convenience wrapper (build-all + assemble) for local
use; the workflow uses the decoupled commands.

---

## 6. Publishing & concurrency

The existing `forge-release.yml` topology is correct and is **reused**:
`build → repo (assemble signed trees) → deploy-pages ‖ publish-releases ‖ publish-oci`.
SP4 changes four things:

1. **Per-item / per-leg build matrix** (`fail-fast: false`) instead of a single
   `mh build --all`, each leg emitting `entry.json` (§5).
2. **Add a Docker Hub publish leg** alongside GHCR — a second `Publisher` target
   reusing the existing OCI publisher (`mh publish --oci`), authenticated to
   `docker.io` with `DOCKERHUB_TOKEN` via the `./dev` env allowlist (never argv).
3. **Serialize publishing** so two near-simultaneous merges can't interleave
   catalogue writes: `concurrency: { group: forge-release-publish, cancel-in-progress: false }`
   (queue, never cancel — a cancelled publish could leave a partial catalogue).
4. **Trigger on merge of a bump PR** (push to `main` touching `catalog/**`) and on
   schedule (reconcile), in addition to the existing `release`/`workflow_dispatch`.

**Concurrent updates** are safe by construction: one PR per item touches a
**disjoint** manifest path (`catalog/<kind>/<name>/manifest.yaml`), so bump PRs
never conflict. `catalog.json` is **never committed in a PR** (it is a build
output, regenerated post-merge), so there is no merge contention on it. GitHub's
"require branches to be up to date before merging" must stay **OFF** — re-basing a
bump branch would rewrite and **destroy the SSH commit signature**
(`required_linear_history` is already off for the same reason).

---

## 7. Partial-failure isolation & self-healing reconcile

Requirement: if one leg fails (e.g. `slurm_exporter` arm/el9 only) it must **not**
break the other legs; the portal shows that version as not-yet-available for that
target, and it gets retried — without a manual step.

**Design (no mutable failure state on disk):**

- Per-leg isolation: `fail-fast: false` on the build matrix; successful legs emit
  `entry.json`, failed legs emit nothing. Assemble publishes everything that
  built.
- **No `status: failed` field** is stored anywhere. Instead the set of legs to
  (re)build is **derived**:
  `missing = expected(manifest matrix) − present(catalog.json)`.
  The manifest matrix is the source of truth for what *should* exist; the
  published catalogue is what *does* exist; the difference is what to build.
- The **daily reconcile** run computes `missing` and rebuilds exactly those legs,
  then re-assembles and republishes. This is self-healing: a transient failure
  (registry 504, runner hiccup) is silently fixed on the next run with no retry
  workflow, no state machine, and no version-bump dependency.
- **Total failure** (upstream archive 404, nothing builds for an item) → the
  **bump PR** never goes green in the first place, so it never merges and the
  catalogue is never touched. Blocking, as it should be.
- **Partial failure** post-merge → good legs published, missing legs reconciled
  next run. Portal renders per-target "available (vX)" / "not yet available" by
  reading `catalog.json` alone.

**Visibility / notification (GitHub-native, no backend):** self-healing must not
mean silent. A failed leg deliberately stays *visible*:

- The bump PR going red on a validation failure already emails the author
  (built-in GitHub PR-check notification) — total failures are caught before merge.
- Post-merge and reconcile runs: the per-leg matrix is `fail-fast: false`, but the
  `assemble`/publish jobs run with `if: always()` so good legs *publish* while the
  **overall run is still marked failed** (a failed matrix job fails the run). That
  triggers GitHub's native "Actions failure" email on `main` and a red run in the
  Actions tab. A `$GITHUB_STEP_SUMMARY` step lists the `missing = expected − present`
  set so the run page names exactly which legs failed.
- A **persistent** failure therefore re-pings every daily reconcile until fixed; a
  **transient** flake self-heals and the next run goes green (one mail at worst).
  Accepted trade-off: occasional single mail for a self-healing flake is the cost
  of "always tell me." A finer Slack/digest alert (compute `missing`, post it) is
  a small additive step, deferred beyond SP4.

**Why not store `failed` / why not an API:** a stored `failed` status turns a
static, reproducible artefact (`catalog.json`) into a mutable state machine —
exactly the friction we are removing — and a backend/API would reintroduce the
24/7 server SP1–SP3 deliberately eliminated (breaks static hosting, air-gap, and
the single-contract model). `expected − present` gives the same self-healing with
zero new moving parts. A build-history/analytics surface, *if* ever needed, is an
additive read-only concern and stays deferred (§11).

---

## 8. CLI surface (SP4 additions)

| Command | Purpose |
|---|---|
| `mh watch [--kind K] [--json]` | Detect outdated items; emit `DetectedVersion[]` as JSON (consumed by the bump workflow). Read-only, no writes. |
| `mh bump <ref> --to <version>` | Validated manifest write (load → set version → re-validate → atomic write). Engine-side, never `sed`. |
| `mh build <ref> --out DIR` | (extended) also emit `entry.json` for the built item. |
| `mh catalog assemble --entries DIR [--previous catalog.json] --out catalog.json` | Join per-item `entry.json` into the catalogue (merge over previous). |
| `mh publish --oci … --registry docker.io` | (extended) Docker Hub target alongside GHCR. |

`mh catalog build` (build-all + assemble) is retained for local convenience.

---

## 9. Testing strategy

Mirrors SP1–SP3: pure logic + FakeRunner command-construction in `make ci`; real
network/registry behind gates.

### 9.1 Unit — pure logic (in `make ci`)
- Version policy: pre-release filtering (`rc`/`beta`/`alpha`/`-pre`/`dev` table-driven),
  `latest > current` comparison (semver with leading-`v` stripped via `clean_version`),
  optional major-pin ceiling (on/off), `outdated` computation.
- `VersionSource` registry: discovery/registration, dispatch by `type`, unknown
  type → clear error (no silent default).
- `missing = expected − present`: matrix-vs-catalogue diff (table-driven:
  all-present, one leg missing, whole item missing, extra-in-catalogue ignored).
- `catalog assemble`: golden catalogue from a set of `entry.json`; missing entry
  keeps previous version; atomic-write (temp+rename) leaves no partial file on
  simulated mid-write failure.

### 9.2 Unit — command construction via FakeRunner (in `make ci`)
- `github-release` source: exact `gh api repos/<repo>/releases/latest` (or
  `gh release view`) argv; pre-release result skipped; network-less.
- `mh bump`: load→set→revalidate→atomic write; invalid target version rejected
  before write; `extra=forbid` preserved.
- `mh build … --out`: asserts `entry.json` emitted on success, **absent** on
  build failure.
- Docker Hub publish leg: exact `buildah login docker.io` + `mh publish --oci`
  argv; **credential never in argv** (env-only, regression guard, same as SP2).
- CLI wiring (`CliRunner`): `mh watch --json` shape; `mh catalog assemble`
  flag threading.

### 9.3 Gated integration — real loop (outside `make ci`, in `forge-smoke.yml`)
Gated by `FORGE_DOCKER_TESTS=1` + tools:
- `mh watch` against one real exporter repo → asserts a `DetectedVersion` with
  `outdated` set when the manifest is intentionally behind.
- End-to-end dry: bump a manifest → `mh build <ref>` (unsigned) → `entry.json`
  emitted → `mh catalog assemble` → catalogue updated. Proves the shift-left PR
  path without secrets.
- Reconcile: seed a catalogue missing one leg → reconcile rebuilds **only** that
  leg → catalogue complete.

---

## 10. Decomposition (SP4.x, SP1/SP2/SP3-style granularity)

| Inc | Content |
|---|---|
| **SP4.0** | Foundation: branch; atomic `write_catalog` (temp+rename); build/assemble decoupling (`mh build --out` emits `entry.json`; `mh catalog assemble`); `forge.detect` package scaffold (`VersionSource` Protocol + registry stub); full gate |
| **SP4.1** | Detection: `github-release` source + version policy (skip pre-release ON, optional major-pin OFF) + reconcile the `upstream.strategy` doc↔model gap; `mh watch [--json]`; pure-logic + FakeRunner tests |
| **SP4.2** | Bump: `mh bump <ref> --to` validated atomic manifest write; `expected − present` diff helper; tests |
| **SP4.3** | Scan workflow: `scan-updates.yml` on a **6-hourly cron (4×/day)** → `mh watch` → one **signed** bump PR per outdated item (app-token, create-pull-request, sign-commits, auto-merge) → PR CI runs `mh build <ref>` **unsigned** (shift-left). **Idempotent per item**: fixed branch `bump/<item>` so a re-scan updates the open PR instead of opening a duplicate. Branch protection note: keep "up-to-date branch" OFF |
| **SP4.4** | Release rework: `forge-release.yml` per-item/per-leg matrix (`fail-fast:false`) emitting `entry.json` → serial `mh catalog assemble` (`if: always()`, publishes good legs) → serialized publish (`concurrency cancel-in-progress:false`); a failed leg still fails the run (native failure email) + `$GITHUB_STEP_SUMMARY` lists `missing = expected − present`; trigger on `main` push touching `catalog/**`; daily reconcile job; gated smoke |
| **SP4.5** | Docker Hub publisher: extend OCI publish to `docker.io` (second leg, env-only creds); FakeRunner + gated smoke |
| **SP4.6** | `manifest.reference.yaml` rewritten in the current `kind`/`spec` schema → `docs/user-guide/manifest.reference.yaml`, validated by `mh validate`; docs; **first real end-to-end forge-published release** (unfreeze catalogue, reconcile with gh-pages mirror); full gate + PR |

Each increment is its own branch → signed commits → PR merged `--merge`. The
per-increment plan is committed to `docs/plans/` at Task 0.

---

## 11. Alternatives considered

- **Nexus / Artifactory.** These are *repository managers* (host + serve
  rpm/deb/OCI). They overlap only with SP2 (which already produces signed static
  repos servable from Pages/Releases). They do not provide the upstream-watch →
  bump-PR → rebuild loop that is the actual subject of SP4, and adopting one would
  reintroduce a 24/7 service, contradicting the static/air-gap model. Rejected for
  SP4; could become an *optional* `Publisher` target later.
- **Pulp.** Same category (repo manager). Its air-gap story (`PulpExport` →
  `tar.gz` → `PulpImport`) is **Pulp-to-Pulp** — the import target must itself run
  Pulp — so it does **not** replace SP3's lightweight, backend-less bundle, and
  `catalog.json` remains the canonical contract for the website and bundler.
  Deferred as an optional `Publisher` target (SP6+), not a core dependency.
- **Backend / API for state and on-demand builds.** Would cleanly model per-leg
  build status and history, but reintroduces the always-on server SP1–SP3
  eliminated and breaks static hosting + air-gap + single-contract. The
  `expected − present` reconcile delivers the required self-healing with no server.
  A read-only build-history/analytics surface is deferred until a concrete need
  exists.
- **Helm chart publishing.** Real future value, but the user has no Helm context
  yet and it deserves its own brainstorm. Deferred to SP6.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Signing key leaks into PR CI | Bump PR builds **unsigned**, artefacts discarded; signed rebuild only post-merge on `main` (§2). Credential-in-argv regression guards (§9.2). |
| Bump to a broken upstream release | Shift-left: PR CI builds the real packages; broken bump → PR red → never merges (§3, §7 total-failure). |
| Concurrent merges corrupt catalogue | One PR per item = disjoint paths; `catalog.json` never committed in PRs; publish serialized `cancel-in-progress:false` (§6). |
| Rebase destroys SSH signatures | "Up-to-date branch" protection OFF; `required_linear_history` already off; `--merge` only (§6). |
| Half-finished `entry.json` assembled | Emit-on-success-only + assemble `needs:` all build legs + atomic `write_catalog` (§5). |
| Transient leg failure freezes a version | `expected − present` daily reconcile rebuilds only missing legs; no manual retry (§7). |
| Auto-bump to a pre-release | Pre-release filter ON by default in the version policy (§4). |
| `upstream.strategy` doc↔model mismatch | Reconciled in SP4.1; `mh validate` enforces the chosen shape (§4). |
| Docker Hub rate limits / auth | Token via `./dev` env allowlist (never argv); GHCR remains primary, Docker Hub is an additional mirror leg (§6). |
| Detection over-narrow (`github-release` only) | Empirically all 32 exporters use Releases; registry makes new sources additive with zero core change (§4). |
