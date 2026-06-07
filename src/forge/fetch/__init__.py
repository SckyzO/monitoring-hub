"""Source acquisition adapters (spec §7.1): HTTP download (httpx + tenacity),
archive extraction, and upstream URL resolution. Pure/injected so the unit
suite needs no network (real download lives behind the ``Downloader`` seam)."""
