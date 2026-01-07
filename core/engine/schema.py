from marshmallow import Schema, fields, validate
from core.config.settings import SUPPORTED_DISTROS, DEFAULT_BASE_IMAGE

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

class RPMSchema(Schema):
    enabled = fields.Bool(load_default=False)
    targets = fields.List(fields.Str(), load_default=SUPPORTED_DISTROS)
    summary = fields.Str()
    dependencies = fields.List(fields.Str(), load_default=[])
    service_file = fields.Bool(load_default=False)
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
    type = fields.Str(required=True, validate=validate.OneOf(["github"]))
    repo = fields.Str(required=True)
    strategy = fields.Str(load_default="latest_release")
    archive_name = fields.Str(allow_none=True) # Pattern like "{name}_{version}_linux_{arch}.tar.gz"

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