"""Publishing layer (spec §4, §5.5-5.7).

The single boundary for network I/O: a ``Publisher`` pushes a staging tree to a
remote. Concrete adapters (GitHub Releases, OCI/GHCR; later S3-compatible R2 /
Garage / MinIO) land in SP2.4-SP2.5. Swapping the blob host is one new adapter,
no change elsewhere.
"""
