from scripts.check_update import normalize, parse_dockerfile_pins


def test_parse_extracts_arg_version_pins() -> None:
    text = (
        "FROM python:3.12-slim\nARG NFPM_VERSION=2.46.3\nARG SYFT_VERSION=v1.0.0\nRUN echo nope\n"
    )
    assert parse_dockerfile_pins(text) == {"NFPM": "2.46.3", "SYFT": "v1.0.0"}


def test_parse_handles_multi_token_names() -> None:
    assert parse_dockerfile_pins("ARG GO_RELEASER_VERSION=1.2.3\n") == {"GO_RELEASER": "1.2.3"}


def test_parse_ignores_non_version_args() -> None:
    assert parse_dockerfile_pins("ARG USER_UID=1000\nARG USER_GID=1000\n") == {}


def test_parse_empty_when_no_pins() -> None:
    assert parse_dockerfile_pins("FROM scratch\n") == {}


def test_normalize_strips_single_leading_v() -> None:
    assert normalize("v2.46.3") == "2.46.3"
    assert normalize("2.46.3") == "2.46.3"
    assert normalize("v1.0.0-rc1") == "1.0.0-rc1"
