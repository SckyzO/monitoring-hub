# SP2 — Distribution (signed apt/yum repos, OCI publish, catalog serving)

> Spec for SP2 of the forge engine. Depends on SP1 (core + `exporter`/`dashboard`
> producers + `mh` CLI + catalog builder + L3 smoke-test), complete and merged.
> Greenfield big-bang exception applies (no external users yet).
> Companion to `docs/specs/2026-06-04-sp1-forge-core.md`.

---

## 1. Context & goals

SP1 turns a manifest into **built, signed artifacts** (RPM/DEB via nfpm, a Docker
build context, a validated dashboard JSON) and a kind-agnostic `catalog.json`.
SP1 stops at the package boundary: it produces files on disk, it does not make
them **installable** or **pullable**.

SP2 closes that gap. It turns the artifacts of SP1 into the first two consumption
pillars of the product:

1. **Signed apt/yum repositories** — a user adds one source line and runs
   `dnf install node_exporter` / `apt install node-exporter`.
2. **Docker / OCI images** (multi-arch) — `docker pull ghcr.io/sckyzo/...`.
3. **Catalogue serving** — `catalog.json`, GPG public keys, downloadable
   dashboard JSON, and the RPM repo metadata, served over HTTP.

SP2 is **distribution**, not new kinds. No manifest-model change is required for
exporters/dashboards beyond populating `Artifact.url` at publish time.

---

## 2. Hosting topology (the central constraint)

GitHub Pages is metadata-only: ~1 GB site soft-limit and ~100 GB/month bandwidth
soft-limit. The package blobs (~GB total across 34 items × RPM/DEB × distros ×
arches) and their download traffic **cannot** live on Pages. Therefore:

- **Metadata → GitHub Pages** (small text/XML, deployed via the Actions artifact
  flow — no `gh-pages` branch).
- **Package blobs → GitHub Releases** (free, generous bandwidth, CDN-backed).
- **OCI images → GHCR** (`ghcr.io`).

A package manager repo is **index + blobs**. Whether index and blobs may live on
different hosts is **asymmetric** between the two ecosystems, and that asymmetry
drives the whole design:

| Ecosystem | Package reference in the index | Split index/blobs across hosts? |
|---|---|---|
| **YUM/DNF** | `primary.xml` `<location href>` — can be an **absolute URL** | **Yes.** createrepo_c `--location-prefix` writes absolute hrefs. |
| **APT** | `Packages` `Filename:` — **relative** to the source base URL | **No.** apt has no notion of an absolute package URL. |

Consequences:

- **RPM**: `repodata/` (small) on **Pages**, `.rpm` on **Releases** via
  `createrepo_c --location-prefix <releases-base-url>`. DNF reads metadata from
  Pages and fetches packages from Releases.
- **APT**: the whole repo must sit on one host. We use the **flat repository
  format** (no `dists/` hierarchy; `InRelease` / `Release` / `Packages` and the
  `.deb` side by side) hosted entirely on **GitHub Releases**, one release tag
  per codename. apt follows GitHub's redirect to `objects.githubusercontent.com`.

### 2.1 Resulting layout

```
GitHub Pages (sckyzo.github.io/monitoring-hub, metadata only — MB)
├── catalog.json
├── RPM-GPG-KEY-monitoring-hub               # GPG public key (rpm)
├── apt/monitoring-hub.asc                    # GPG public key (apt)
├── el9/x86_64/repodata/repomd.xml(.asc)      # signed RPM metadata
├── el9/aarch64/repodata/...
├── el10/x86_64/repodata/... · el10/aarch64/repodata/...
└── dashboards/<name>.json                    # downloadable (pillar 4)

GitHub Releases (blobs — GB)
├── tag rpm-<name>-<version> : *.rpm          # RPM packages
└── tag apt-<codename>       : InRelease + Release + Release.gpg
                               + Packages(.gz) + *.deb   (flat repo)

GHCR
└── ghcr.io/sckyzo/monitoring-hub/<name>:<version>|latest  (multi-arch)
```

### 2.2 User-facing source lines (retro-compatible URLs)

The public Pages URL is identical whether deployment uses a `gh-pages` branch or
the Actions artifact flow, so **existing apt/yum sources keep working**.

```ini
# YUM (metadata on Pages, .rpm on Releases via location-prefix)
[monitoring-hub]
baseurl=https://sckyzo.github.io/monitoring-hub/el9/$basearch
gpgkey=https://sckyzo.github.io/monitoring-hub/RPM-GPG-KEY-monitoring-hub
gpgcheck=1
```

```bash
# APT (flat repo on Releases)
deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://github.com/SckyzO/monitoring-hub/releases/download/apt-noble/ ./
```

### 2.3 No vendor lock-in (design insurance)

The package-blob host is **not hardcoded**. The createrepo_c location prefix and
the apt base URL are **CLI parameters** (`--package-base-url`), defaulting to
GitHub Releases. The publish layer is a `Publisher` protocol with concrete
adapters. A future self-hosted **S3-compatible** store (Cloudflare R2, Garage on
a dedicated server, MinIO) is added as one `S3Publisher` adapter plus a different
`--package-base-url` — **no change to repo generation or the rest of the engine**.
This is the explicit, reserved extension point; it is **not built** in SP2 (YAGNI).

---

## 3. Scope of SP2

**In scope:**

- `forge/repo/` — generate signed repo trees: RPM (`createrepo_c`), APT flat
  (`apt-ftparchive`), metadata signing (gpg), assembly of the Pages tree
  (`./public`) and the Releases staging tree (`./release`).
- `forge/publish/` — `Publisher` protocol + `GitHubReleasesPublisher`
  (`.rpm` + flat apt assets) + `OciPublisher` (buildah build per-arch + manifest
  list + skopeo push to GHCR).
- CLI: `mh repo build`, `mh publish --oci`, `mh publish --releases`.
- `mh build` rebalance: emit the **Docker build context** to disk
  (`./dist/docker/<name>/`), no daemon at build time (fully testable in
  `make ci`); image build/push moves entirely to `mh publish --oci`.
- `Artifact.url` populated at repo-build (rpm/deb) and publish (oci).
- `forge-release.yml` workflow: `mh build --all` → `mh repo build --sign` →
  `actions/deploy-pages ./public` ∥ `mh publish --releases` ∥ `mh publish --oci`.
- Dev image additions: `createrepo_c`, `apt-utils` (apt-ftparchive), `buildah`,
  `skopeo`, `gpg`, `qemu-user-static`.
- Gated L3-style repo-consume smoke-test (real `dnf install` / `apt install` from
  a generated signed repo).

**Out of scope (YAGNI, explicit):**

- Offline bundler `mh bundle` + recipe generation (SP3).
- Website (SP4).
- `mh publish --pages` (GitHub forbids triggering `deploy-pages` from a CLI; Pages
  deploy stays CI-native).
- S3/R2/Garage publisher and CDN mirrors (reserved extension point, roadmap
  "Repository Mirrors").
- Incremental / state-diff publication (each run regenerates the full tree; the
  stateless apt-ftparchive + createrepo_c model makes this cheap enough).

---

## 4. Architecture

Dependencies point inward; `domain/` depends on nothing. SP2 adds two layers next
to `packaging/`, both used by the CLI, neither known to `kinds/`.

```
cli/  →  repo/ · publish/ · catalog/ · sources/ · kinds/  →  domain/
                  ↑                          ↑
            packaging/ (nfpm, docker-context, sign) ────┘
```

| Layer | Role | Depends on |
|---|---|---|
| `repo/` | Generate signed repo trees (createrepo_c, apt-ftparchive, gpg metadata sign) + assemble `./public` and `./release`. Pure file generation behind an injected runner; no network. | domain, packaging (sign), catalog |
| `publish/` | Push artifacts: `Publisher` protocol + GitHub Releases + OCI adapters. All network I/O isolated here. | domain |

Rule of layers preserved: `repo/` generates files and never pushes; `publish/`
pushes and never generates repo metadata. Swapping the blob host touches only a
`Publisher` adapter and a base-URL parameter.

### 4.1 Module structure

```
src/forge/
  repo/
    __init__.py
    rpm.py            # build_rpm_repo(packages, out_dir, location_prefix, runner)
    deb.py            # build_apt_repo(packages, out_dir, codename, runner)
    metadata_sign.py  # sign_repomd / sign_apt_release (gpg via runner)
    builder.py        # build_distribution(...) -> populates ./public + ./release
  publish/
    __init__.py
    base.py           # Publisher protocol
    releases.py       # GitHubReleasesPublisher
    oci.py            # OciPublisher (buildah + skopeo)
```

---

## 5. Component design

### 5.1 `repo/rpm.py`

`build_rpm_repo(*, packages: list[Path], repodata_dir: Path, location_prefix: str,
runner: CommandRunner) -> Path`

- Runs `createrepo_c --location-prefix <location_prefix> <work>` where `<work>`
  contains the `.rpm` for one `(target, arch)`; emits `repodata/` into
  `repodata_dir` (the Pages path `el9/x86_64/`).
- `--location-prefix` makes `primary.xml` hrefs absolute → Releases.
- Pure wrapper; the caller groups packages by `(target, arch)`.

### 5.2 `repo/deb.py`

`build_apt_repo(*, packages: list[Path], repo_dir: Path, codename: str,
origin: str, runner: CommandRunner) -> Path`

- Flat format. Copies the `.deb` into `repo_dir`, then:
  - `apt-ftparchive packages .` → `Packages` (+ gzip → `Packages.gz`).
  - `apt-ftparchive -o APT::FTPArchive::Release::Codename=<codename>
    -o ...::Origin=<origin> release .` → `Release`.
- Mixed-arch `Packages` is correct for flat repos (apt filters on the
  `Architecture:` field).

### 5.3 `repo/metadata_sign.py`

Repo **metadata** signing is distinct from package signing (SP1 `packaging/sign.py`
handles `.rpm`/`.deb`). Text/XML detached & inline signatures:

- `sign_repomd(repomd: Path, *, key_id: str, runner) -> Path` →
  `gpg --batch --detach-sign --armor -u <key_id> repomd.xml` → `repomd.xml.asc`.
- `sign_apt_release(release: Path, *, key_id, runner) -> tuple[Path, Path]` →
  `gpg --clearsign` → `InRelease` and `gpg --detach-sign --armor` → `Release.gpg`.
- Passphrase via gpg-agent / env, **never argv** (matches the SP1 secrets rule).
- **Gated on key presence.** No `key_id` → metadata emitted unsigned (local dev,
  unit tests). With key (CI) → signed.

### 5.4 `repo/builder.py`

`build_distribution(*, catalog: Catalog, packages_dir: Path, dashboards_dir: Path,
public_out: Path, release_out: Path, package_base_url: str,
key_id: str | None, runner) -> Catalog`

Orchestrates the full tree:

1. Group built `.rpm` by `(target, arch)` → `repo/rpm.py` → `public_out/<target>/<arch>/repodata/` + copy `.rpm` to `release_out/rpm-<name>-<version>/`.
2. Group built `.deb` by codename → `repo/deb.py` → `release_out/apt-<codename>/` (flat).
3. Sign metadata (`repomd.xml.asc`, `InRelease`, `Release.gpg`) if `key_id`.
4. Copy GPG public key, `catalog.json`, and `dashboards/*.json` into `public_out`.
5. Return an updated `Catalog` with each `Artifact.url` set to its hosted URL
   (rpm/deb → `package_base_url`-derived; dashboards → Pages URL).

### 5.5 `publish/base.py`

```python
class Publisher(Protocol):
    def publish(self, staging: Path) -> None: ...
```

Minimal protocol so the CLI is host-agnostic. Network is confined here.

### 5.6 `publish/releases.py`

`GitHubReleasesPublisher(repo: str, token: str, runner)` — for each
`rpm-*` / `apt-*` subdir of the staging tree, ensure the release tag exists and
upload assets (`gh release upload --clobber` semantics via the GitHub API / `gh`).
Idempotent: re-running clobbers assets (stable URLs per tag).

### 5.7 `publish/oci.py`

`OciPublisher(registry: str, runner)` — for each `./dist/docker/<name>/` build
context (Dockerfile + staged binary emitted by `mh build`):

- `buildah bud --arch amd64 -t <img>:amd64 .` and `--arch arm64` (daemonless,
  rootless, runs in the dev image — no docker socket).
- `buildah manifest create` + `add` per arch → multi-arch manifest list.
- `skopeo copy` / `buildah manifest push` → `ghcr.io/.../<name>:<version>` and
  `:latest`.
- **Gated** (needs qemu/binfmt for cross-arch + registry auth), like the L3 test.

### 5.8 `mh build` rebalance

SP1 builds the image inline via the `docker` CLI (daemon required, not testable in
`make ci`). SP2 changes the Docker artifact path to **emit the build context** to
`./dist/docker/<name>/` (render Dockerfile + stage binary) — pure file generation,
**fully testable in `make ci`**. Actual image build+push moves to
`mh publish --oci` (buildah/skopeo, gated). The only docker-family code left runs
in `publish/oci.py`, behind the gate. `packaging/docker.py` keeps its renderer;
its `DockerBuilder` (docker CLI) is removed.

---

## 6. CLI surface

```
mh build --all --out ./dist
    # SP1 extended: also emits ./dist/docker/<name>/ build contexts (no daemon)

mh repo build
    --packages ./dist --catalog ./catalog --dashboards ./dist/dashboards
    --out ./public --release-out ./release
    --package-base-url https://github.com/SckyzO/monitoring-hub/releases/download
    [--sign --key-id <ID>]
    # generates the Pages tree + the Releases staging tree, signs metadata

mh publish --oci      [--registry ghcr.io/sckyzo/monitoring-hub]
mh publish --releases ./release   [--repo SckyzO/monitoring-hub]
    # Pages deploy is NOT a CLI command — it is CI-native (deploy-pages ./public)
```

---

## 7. Domain changes

- `Artifact.url` (already a reserved `str | None`) is **populated** at repo-build
  (rpm/deb) and publish (oci). No schema change.
- No new domain model. Base URLs are CLI parameters, not a global config file
  (YAGNI; introduce config only when a real multi-host need arises).

---

## 8. CI — `forge-release.yml`

Triggered on release/tag (and `workflow_dispatch`). Job graph:

1. **build** — `mh build --all --out ./dist` (daemonless; runs in dev image).
2. **repo** — import GPG key from secret → `mh repo build --sign --key-id` →
   uploads `./public` as the Pages artifact and `./release` as a job artifact.
3. **deploy-pages** — `actions/deploy-pages` (needs `pages:write` + `id-token:write`).
4. **publish-releases** — `mh publish --releases ./release` (`contents:write`).
5. **publish-oci** — `mh publish --oci` (`packages:write`; qemu/binfmt set up).

Secrets: `GPG_PRIVATE_KEY` + `GPG_PASSPHRASE` (existing), `GITHUB_TOKEN` (auto).
Permissions: explicit minimum per job, never `write-all`. Actions pinned by SHA.

---

## 9. Testing strategy

- **Unit (in `make ci`, no daemon/network):** a fake `CommandRunner` asserts the
  exact `createrepo_c` / `apt-ftparchive` / `gpg` / `buildah` / `skopeo`
  command lines and the generated tree structure. Golden tests for the assembled
  `./public` and `./release` layouts and for `Artifact.url` population.
- **Gated integration (outside `make ci`, `FORGE_DOCKER_TESTS=1` + tools):**
  real `createrepo_c` + `apt-ftparchive` produce a real signed repo; an
  L3-style consume test installs from it (`dnf install` from local repodata,
  `apt install` from a local flat repo). Extends the SP1 smoke harness.

---

## 10. Decomposition (SP2.x, SP1-style granularity)

| Inc | Content |
|---|---|
| **SP2.0** | Foundation: branch, dev image (`createrepo_c`, `apt-utils`, `buildah`, `skopeo`, `gpg`, `qemu-user-static`), `Artifact.url` wiring, `repo/`+`publish/` scaffolds |
| **SP2.1** | RPM repo: `repo/rpm.py` (createrepo_c + `--location-prefix`) + `metadata_sign.sign_repomd` |
| **SP2.2** | APT flat repo: `repo/deb.py` (apt-ftparchive) + `metadata_sign.sign_apt_release` |
| **SP2.3** | `repo/builder.py` + `mh repo build` (assemble public+release, dashboards, keys, catalog.json, `Artifact.url`) |
| **SP2.4** | OCI: `mh build` emits Docker context + `publish/oci.py` (buildah/skopeo) + `mh publish --oci`; remove `DockerBuilder` |
| **SP2.5** | `publish/releases.py` (`GitHubReleasesPublisher`) + `mh publish --releases` |
| **SP2.6** | `forge-release.yml` + gated L3 repo-consume smoke + full gate + PR |

Each increment is its own branch → signed commits → PR merged `--merge`.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| apt cannot split index/blobs across hosts | Flat repo wholly on Releases (§2). |
| Vendor lock-in to GitHub Releases | `--package-base-url` param + pluggable `Publisher` → S3/R2/Garage later (§2.3). |
| buildah multi-arch needs emulation | qemu/binfmt in CI; OCI build is gated, like L3. |
| Pages bandwidth/size limit | Only metadata on Pages; blobs on Releases (§2). |
| Metadata signing leaking passphrase | gpg-agent/env, never argv (§5.3, matches SP1). |
| Mutable per-codename apt release tag | Clobber-upload to a stable tag → stable URLs, idempotent (§5.6). |
