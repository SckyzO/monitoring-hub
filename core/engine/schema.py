from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from core.config.settings import DEFAULT_BASE_IMAGE, SUPPORTED_DISTROS


class FileInstallSchema(Schema):
    source = fields.Str(required=True)
    dest = fields.Str(required=True)
    mode = fields.Str(load_default="0644")
    config = fields.Bool(load_default=False)


class DirectorySchema(Schema):
    path = fields.Str(required=True)
    mode = fields.Str(load_default="0755")
    owner = fields.Str(load_default="root")
    group = fields.Str(load_default="root")


class SystemdSchema(Schema):
    enabled = fields.Bool(load_default=False)
    arguments = fields.List(fields.Str(), load_default=[])
    after = fields.List(fields.Str(), load_default=["network.target"])
    restart = fields.Str(load_default="on-failure")
    type = fields.Str(load_default="simple")


class RPMSchema(Schema):
    enabled = fields.Bool(load_default=False)
    targets = fields.List(fields.Str(), load_default=SUPPORTED_DISTROS)
    summary = fields.Str()
    install_path = fields.Str(allow_none=True)
    dependencies = fields.List(fields.Str(), load_default=[])
    systemd = fields.Nested(SystemdSchema, load_default={"enabled": False})
    system_user = fields.Str(allow_none=True)
    extra_files = fields.List(fields.Nested(FileInstallSchema), load_default=[])
    directories = fields.List(fields.Nested(DirectorySchema), load_default=[])


class ValidationSchema(Schema):
    enabled = fields.Bool(load_default=True)
    port = fields.Int(allow_none=True)
    command = fields.Str(allow_none=True)
    args = fields.Str(allow_none=True)


class DockerSchema(Schema):
    enabled = fields.Bool(load_default=False)
    base_image = fields.Str(load_default=DEFAULT_BASE_IMAGE)
    entrypoint = fields.List(fields.Str())
    cmd = fields.List(fields.Str(), load_default=[])
    validation = fields.Nested(ValidationSchema, load_default={})


class UpstreamSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["github", "local"]))
    repo = fields.Str(allow_none=True)
    strategy = fields.Str(load_default="latest_release")
    archive_name = fields.Str(
        allow_none=True
    )  # Pattern like "{name}_{version}_linux_{arch}.tar.gz"

    # Local source support
    local_binary = fields.Str(allow_none=True)  # Path to raw binary
    local_archive = fields.Str(allow_none=True)  # Path to .tar.gz or .gz

    @validates_schema
    def validate_upstream(self, data, **_kwargs):
        """Validate type-specific requirements."""
        if data.get("type") == "github":
            if not data.get("repo"):
                raise ValidationError("'repo' is required for upstream type 'github'")
        elif data.get("type") == "local":
            if not data.get("local_binary") and not data.get("local_archive"):
                raise ValidationError(
                    "'local_binary' or 'local_archive' required for upstream type 'local'"
                )
            if data.get("local_binary") and data.get("local_archive"):
                raise ValidationError("Only one of 'local_binary' or 'local_archive' allowed")


class ExtraSourceSchema(Schema):
    url = fields.Str(required=True)
    filename = fields.Str(required=True)


class BuildSchema(Schema):
    method = fields.Str(required=True, validate=validate.OneOf(["binary_repack", "source_build"]))
    binary_name = fields.Str(required=True)
    extra_binaries = fields.List(fields.Str(), load_default=[])
    extra_sources = fields.List(fields.Nested(ExtraSourceSchema), load_default=[])
    archs = fields.List(fields.Str(), load_default=["amd64", "arm64"])


class ArtifactsSchema(Schema):
    rpm = fields.Nested(RPMSchema)
    docker = fields.Nested(DockerSchema)


class ManifestSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    category = fields.Str(required=False, dump_default="System")
    new = fields.Bool(required=False, dump_default=False)
    updated = fields.Bool(required=False, dump_default=False)
    version = fields.Str(required=True)
    upstream = fields.Nested(UpstreamSchema, required=True)
    build = fields.Nested(BuildSchema, required=True)
    artifacts = fields.Nested(ArtifactsSchema, required=True)
