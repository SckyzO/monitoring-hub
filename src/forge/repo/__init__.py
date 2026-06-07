"""Repository-tree generation (spec §4, §5.1-5.4).

Pure file generation behind an injected ``CommandRunner``: RPM repodata
(createrepo_c), flat APT metadata (apt-ftparchive), metadata signing (gpg), and
assembly of the Pages tree (``./public``) + the Releases staging tree
(``./release``). No network — that is ``forge.publish``'s job.
"""
