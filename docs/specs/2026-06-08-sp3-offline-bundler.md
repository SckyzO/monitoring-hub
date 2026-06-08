# SP3 — Offline bundler (`mh bundle`, recipe, self-contained archive)

> Sub-project 3 of the forge-engine refactor. Depends on SP1 (core + catalogue +
> `exporter`/`dashboard` kinds + `mh` CLI) and SP2 (signed apt/yum repos, OCI,
> catalog serving) — both complete and merged. Greenfield big-bang exception
> applies (no external users yet).

---

## 1. Context & goals

Monitoring Hub targets offline-first / air-gapped / HPC environments. The
differentiator (roadmap pillar 5) is an **offline bundle generator**: select
catalogue items, produce a single self-contained archive that installs on a
**disconnected** machine with no network and no backend.

SP3 builds **C1** of the layered offline model: a CLI bundler (`mh bundle`) that
runs where there *is* internet and emits the archive. The **bundle recipe** (the
roadmap pivot) is a versioned JSON describing the bundle exactly (items, pinned
versions, kinds, overlay refs, checksums); the portal (SP4) will generate it
later, the CLI consumes it now and can also synthesise one from flags.

Goals:

- Reproducible, auditable bundles: the recipe pins versions; the archive carries
  a `SHA256SUMS` integrity manifest and an optional detached signature on the
  recipe.
- Kind-agnostic: the bundler embeds whatever artefact types the selected
  catalogue items expose — `rpm`/`deb`/`grafana-dashboard` today, `alert-rule`/
  `stack` automatically once SP5 adds those kinds. No per-kind special-casing.
- Offline consumption is **transparent and operator-driven**: the archive ships a
  ready-to-use *local* apt/yum repository plus a `README.md` documenting the exact
  commands. No "magic" install script (auditable, minimal bash surface).

Non-goals (later sub-projects): portal cart → recipe (SP4); in-browser zip /
on-demand backend build service (SP6).

---

## 2. The central constraint (offline repo layout)

A yum repository served from `baseurl=file://` only resolves a package
`<location href>` that is **relative** (librepo path-joins it onto the baseurl;
it does **not** honour an absolute `file://` href — established empirically in
SP2.6's L3 smoke). Therefore the offline yum repo must be **co-located**: the
`.rpm` sit next to their `repodata/` in one directory, generated with an **empty
location-prefix** so hrefs are relative.

This is the inverse of SP2's *split* topology (metadata on Pages, blobs on
Releases via an absolute URL). Consequently the bundler **reuses the SP2.1/SP2.2
primitives** (`build_rpm_repo`, `build_apt_repo`, `sign_repomd`,
`sign_apt_release`) with offline parameters, **not** `build_distribution` (which
is split-topology only). The apt flat repo is already co-located, so it carries
over directly.

`build_rpm_repo` needs two **backward-compatible** extensions for offline reuse
(SP3.3; defaults preserve SP2 behaviour exactly):
1. `location_prefix` accepts `""` (or `None`) → **omit** the `--location-prefix`
   flag, so `createrepo_c` writes the default relative href (just the filename),
   which `file://` resolves.
2. `keep_packages: bool = False` → when `True`, do **not** unlink the staged
   `.rpm` after indexing, so the offline repo keeps blobs **and** metadata
   together (SP2's Pages tree still gets `False` = metadata only).

---

## 3. Scope of SP3

In scope:

1. `forge.bundle` package: recipe resolution, artefact acquisition, offline-repo
   assembly, archive packaging, orchestrator.
2. `mh bundle` CLI: recipe-driven **and** flag-driven (flags synthesise a
   recipe).
3. Artefact sources: published GitHub Releases (default) and a local `--packages`
   directory (a prior `mh build` output).
4. Self-contained `.tar.gz` archive with the layout of §6.
5. Optional repo-metadata signing (`--sign --key-id`), mirroring `mh repo build`.
6. Gated L3 offline-consume smoke (real bundle installed in a `--network none`
   container).

Out of scope (explicit): building packages (that stays in `mh build`; the bundler
acquires already-built blobs); `docker save` images (deferred to optional SP3.5);
the portal; any backend.

---

## 4. Architecture

### 4.1 Module structure

```
src/forge/bundle/
  __init__.py
  resolver.py    # recipe <-> catalog; flag synthesis; target/arch filtering
  source.py      # ArtifactSource Protocol + ReleasesFetcher + LocalDirSource
  assemble.py    # offline repos + dashboards/alerts + key + README + SHA256SUMS
  archive.py     # tar.gz packaging
  builder.py     # build_bundle orchestrator
```

Mirrors the SP2 `forge.repo` / `forge.publish` shape: pure logic split from the
single I/O seam (`CommandRunner` for `gh`/`createrepo_c`/`apt-ftparchive`/`gpg`),
each module independently testable with the existing `FakeRunner`.

### 4.2 Reused seams (no new I/O abstraction)

- `forge.packaging.runner.CommandRunner` / `SubprocessRunner` — every external
  command (`gh release download`, `createrepo_c`, `apt-ftparchive`, `gpg`, `tar`).
- `forge.repo.rpm.build_rpm_repo` / `forge.repo.deb.build_apt_repo` — offline repo
  metadata (empty/relative location-prefix for rpm).
- `forge.repo.metadata_sign.sign_repomd` / `sign_apt_release` — optional signing.
- `forge.catalog.builder.load_catalog` — read `catalog.json` to resolve items.
- `forge.packaging.checksum.file_sha256` — `SHA256SUMS` entries.
- `forge.domain.recipe.BundleRecipe` / `RecipeItem` — the recipe model (extended).

---

## 5. Component design

### 5.1 `domain/recipe.py` (extend the SP1.1 stub)

`RecipeItem` gains optional `targets: list[str] | None` and `arches:
list[str] | None` (per-item matrix filter; `None` = all available). `BundleRecipe`
gains `generated_at: str` and `arches: list[str] | None` (bundle-wide default
filter). Keep `extra="forbid"`. The model stays the canonical in-memory form;
YAML/JSON are just serialisations.

### 5.2 `bundle/resolver.py`

- `load_recipe(path) -> BundleRecipe` — YAML/JSON → `BundleRecipe` via
  `parse`-style validation (bad keys → `BundleError`, new error in §7).
- `recipe_from_selection(items, *, targets, arches) -> BundleRecipe` — synthesise
  a recipe from CLI `--item name[@version]` selections + global filters.
- `resolve_artifacts(recipe, catalog) -> list[ResolvedArtifact]` — for each
  recipe item, look it up in `catalog.json` (match `(kind, name)`; version must
  match the pin or `BundleError`), expand its `artifacts[]`, filter by the
  effective `(targets, arches)`. `ResolvedArtifact` carries `kind`, `name`,
  `version`, the `Artifact`, and the expected on-disk filename (reconstructed the
  same way as `forge.repo.builder`). Pure; no I/O.

### 5.3 `bundle/source.py`

- `ArtifactSource` `@runtime_checkable` Protocol: `fetch(artifact:
  ResolvedArtifact, dest: Path) -> Path` (places the blob at `dest`, returns it).
- `LocalDirSource(root: Path)` — locates the blob by filename via `root.rglob`
  (a prior `mh build` / `dist/` tree); missing → `BundleError`.
- `ReleasesFetcher(repo: str, runner: CommandRunner)` — `gh release download
  <tag> --pattern <filename> --dir <dest> --repo <repo>` where the tag is the
  SP2.3 convention (`rpm-<target>-<arch>` / `apt-<codename>`); non-zero →
  `BundleError`. Ambient `GH_TOKEN` (no token in argv), like SP2.5.
- Dashboards/alerts (Pages-hosted JSON/YAML artefacts) are fetched by their
  `Artifact.url` when using `ReleasesFetcher`, or copied from the local tree with
  `LocalDirSource`.

### 5.4 `bundle/assemble.py`

`assemble_bundle(resolved, *, staging, key_id=None, public_key=None, runner)`:

- Group rpm artefacts by `(target, rpm_arch)` → for each, stage the `.rpm` into
  `staging/yum/<target>/<arch>/` and run `build_rpm_repo(location_prefix="")`
  **without removing the blobs** (offline repo keeps both metadata and packages,
  unlike SP2's Pages tree); sign repomd iff `key_id`.
- Group deb artefacts by codename → `build_apt_repo` into `staging/apt/<codename>/`
  (flat); sign Release iff `key_id`.
- Copy `grafana-dashboard` artefacts → `staging/dashboards/<name>.json`; future
  kinds land in their own `staging/<kind-plural>/` dir (kind-agnostic switch).
- Copy `public_key` → `staging/RPM-GPG-KEY-monitoring-hub` (+ `apt/` keyring) iff
  given.
- Write canonical `staging/recipe.json`; sign → `recipe.json.asc` iff `key_id`.
- Render `staging/README.md` from a template (per-distro add-repo + import-key +
  install commands, derived from the resolved targets).
- Write `staging/SHA256SUMS` over every file (via `file_sha256`).

### 5.5 `bundle/archive.py`

`pack(staging, out: Path, runner) -> Path` — `tar -czf <out> -C <staging> .`
(deterministic-ish ordering). `.tar.gz` is the default for universal
extractability on minimal air-gapped targets; a future `--format zstd` is a
trivial extension point (YAGNI now).

### 5.6 `bundle/builder.py`

`build_bundle(*, recipe, catalog, source, staging, out, key_id=None,
public_key=None, runner) -> Path` — orchestrates resolve → fetch each artefact
via `source` → assemble → pack. Returns the archive path.

---

## 6. Bundle layout (the produced archive)

```
recipe.json                       # canonical BundleRecipe (+ recipe.json.asc if --sign)
SHA256SUMS                        # integrity over all files
README.md                         # exact per-distro commands
RPM-GPG-KEY-monitoring-hub        # iff --sign
yum/<target>/<arch>/              # .rpm + repodata/ co-located (relative href)
apt/<codename>/                   # flat: .deb + Packages(.gz) + Release[/InRelease/Release.gpg]
dashboards/<name>.json
alerts/<name>.yaml                # empty until SP5 adds the alert-rule kind
```

Offline consumption (documented in `README.md`, operator-run):

```
# RHEL/EL
tar xzf bundle.tar.gz && cd bundle
sudo rpm --import RPM-GPG-KEY-monitoring-hub          # iff signed
sudo tee /etc/yum.repos.d/mh-offline.repo <<EOF
[mh-offline]
name=mh-offline
baseurl=file:///PATH/bundle/yum/el9/x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=1                                       # iff signed
gpgkey=file:///PATH/bundle/RPM-GPG-KEY-monitoring-hub
EOF
sudo dnf -y install node_exporter

# Debian/Ubuntu
sudo install -d /etc/apt/keyrings
sudo cp bundle/RPM-GPG-KEY-monitoring-hub /etc/apt/keyrings/mh.asc   # iff signed
echo 'deb [signed-by=/etc/apt/keyrings/mh.asc] file:///PATH/bundle/apt/noble ./' \
  | sudo tee /etc/apt/sources.list.d/mh-offline.list
sudo apt-get update && sudo apt-get install -y node-exporter
```

---

## 7. Domain & error changes

- `domain/recipe.py` extended (§5.1): `RecipeItem.targets/arches`,
  `BundleRecipe.generated_at/arches`. No breaking change to the stub fields.
- New `BundleError(ForgeError)` in `domain/errors.py` for bundler-specific
  failures (recipe load, item not in catalogue, version mismatch, blob not found,
  fetch failure). Signing failures keep raising `SigningError` (SP2.1).

---

## 8. CLI surface

```
mh bundle --recipe recipe.yaml -o bundle.tar.gz
    [--target el9,ubuntu-24.04] [--arch amd64,arm64]
    [--packages ./dist]                 # source = local tree (default = Releases)
    [--repo SckyzO/monitoring-hub]      # source repo for Releases fetch
    [--catalog catalog.json]
    [--sign --key-id <ID>] [--public-key <path>]

mh bundle --item node_exporter@1.9.1 --item blackbox_exporter
    --target el9 --arch amd64 -o bundle.tar.gz
    # flags synthesise a recipe, then bundle (same downstream path)
```

Rules: exactly one of `--recipe` / `--item…` (both → UsageError; neither →
UsageError). `--sign` without `--key-id` → UsageError. Default source =
`ReleasesFetcher`; `--packages` switches to `LocalDirSource`. Kind-agnostic — no
`--dashboards`/`--alerts` flags; selection is by item, artefact types follow.

---

## 9. Testing strategy

TDD, test-first, per increment; ≥95% coverage on new modules (enforced by
`make ci`). Three layers:

### 9.1 Unit — pure logic (in `make ci`)
- `resolver.resolve_artifacts`: catalog lookup, version-pin mismatch → BundleError,
  target/arch filtering (table-driven); `recipe_from_selection` synthesis;
  `load_recipe` valid + `extra=forbid` rejection.

### 9.2 Unit — command construction & tree assembly via FakeRunner (in `make ci`)
- `source.ReleasesFetcher`: exact `gh release download` argv (tag, `--pattern`,
  `--dir`, `--repo`); non-zero → BundleError. `LocalDirSource`: rglob locate +
  missing → BundleError.
- `assemble.assemble_bundle`: golden tree (yum co-located with relative href +
  packages kept; apt flat; dashboards; key; `recipe.json`; `SHA256SUMS` covering
  every file; `README.md` rendered for the resolved targets); signing branch
  asserts `sign_repomd`/`sign_apt_release` invoked and `recipe.json.asc` emitted;
  **passphrase never in argv** (regression guard).
- `archive.pack`: exact `tar -czf … -C …` argv.
- CLI wiring (`CliRunner`): `--recipe` vs `--item` exclusivity, `--sign` without
  `--key-id` errors, source dispatch (`--packages` → LocalDirSource), target/arch
  threaded to the resolver.

### 9.3 Gated integration — real offline consume (outside `make ci`)
Gated by `FORGE_DOCKER_TESTS=1` + tools, in `forge-smoke.yml`:
- `mh build` a real node_exporter rpm+deb locally → `mh bundle --packages` →
  extract in a container started with **`--network none`** → configure the file://
  local repo from the bundle → `dnf -y install` / `apt-get install` → run the
  binary. Proves the bundle installs with **zero network** and that the
  co-located relative-href yum repo resolves offline. Optionally `--sign` and
  assert signature verification.

---

## 10. Decomposition (SP3.x, SP1/SP2-style granularity)

| Inc | Content |
|---|---|
| **SP3.0** | Foundation: branch, `forge.bundle` scaffold, extend `BundleRecipe` + `load_recipe`, `BundleError`, `mh bundle` stub, full gate |
| **SP3.1** | `resolver.py`: recipe ↔ catalog, target/arch filtering, `recipe_from_selection` |
| **SP3.2** | `source.py`: `ArtifactSource` + `ReleasesFetcher` (`gh`) + `LocalDirSource` |
| **SP3.3** | `assemble.py`: offline co-located repos + dashboards + key + README + `SHA256SUMS` + recipe signing |
| **SP3.4** | `archive.py` + `mh bundle` end-to-end + gated L3 offline-consume smoke + full gate + PR |
| **SP3.5** | (optional) `--images`: ship OCI images as per-arch `docker-archive` tarballs. Daemonless (`docker save` has no daemon here): default `RegistryImageSource` (`skopeo copy`), opt-in `LocalImageSource` (`buildah bud`); multi-arch default, `--image-arch` narrows |

Each increment is its own branch → signed commits → PR merged `--merge`. The
per-increment plan is committed to `docs/plans/` at Task 0.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Absolute `file://` href unresolved offline | Co-located repo, empty location-prefix → relative href (§2, proven in SP2.6). |
| Nothing published to Releases yet | L3 smoke uses `--packages` from a local `mh build`; `ReleasesFetcher` covered by FakeRunner unit tests; real-Releases path exercised once a release exists. |
| Signing key absent where `mh bundle` runs | Repo signing optional (`--sign`); default integrity via `SHA256SUMS` + optional recipe signature. |
| zstd missing on air-gapped target | `.tar.gz` default (gzip universal); zstd is a future opt-in. |
| Bundle size (docker images) | Images opt-in (`--images`); default bundle is repo + metadata + small JSON/YAML. |
| `docker-archive` can't hold a multi-arch index | One `<name>-<version>-<arch>.tar` per arch (each `docker load`-able); `--image-arch` narrows the set. |
| Passphrase leak via argv | gpg via agent/env, never argv (asserted), same as SP2. |
```
