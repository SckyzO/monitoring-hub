"""Bundle archiving (spec §5.5): tar the assembled tree into a .tar.gz.

Literal ``tar -czf <out> -C <staging> .`` — universal extractability on minimal
air-gapped targets. ``--format zstd`` would be a trivial future extension point
(YAGNI now). The packer never reaches into the tree; it only shells out.
"""

from __future__ import annotations

from pathlib import Path

from forge.domain.errors import BundleError
from forge.packaging.runner import CommandRunner


def pack(staging: Path, out: Path, *, runner: CommandRunner) -> Path:
    """Create ``out`` (``.tar.gz``) from the contents of ``staging``. Returns ``out``."""
    out.parent.mkdir(parents=True, exist_ok=True)
    result = runner.run(["tar", "-czf", str(out), "-C", str(staging), "."])
    if result.returncode != 0:
        raise BundleError(f"tar failed: {result.stderr}")
    return out
