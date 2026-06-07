"""Stage a manifest's committed ``assets/`` into a build work dir.

``extra_files.source`` entries are written as ``assets/<file>`` (resolved by
nfpm relative to its cwd = the work dir) and custom Dockerfiles ``COPY`` files
from the build context root. Staging the tree once makes both resolve without
the producer knowing which files a given manifest references.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def stage_assets(manifest_dir: Path | None, work_dir: Path) -> None:
    """Copy ``manifest_dir/assets`` into ``work_dir/assets`` if it exists.

    A no-op when ``manifest_dir`` is ``None`` (programmatic manifest) or has no
    ``assets/`` subdir, so callers can stage unconditionally.
    """
    if manifest_dir is None:
        return
    assets = manifest_dir / "assets"
    if not assets.is_dir():
        return
    shutil.copytree(assets, work_dir / "assets", dirs_exist_ok=True)
