from marshmallow import Schema, fields, validate

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
    targets = fields.List(fields.Str(), load_default=["el8", "el9", "el10"])
    summary = fields.Str()
    service_file = fields.Bool(load_default=False)
    system_user = fields.Str(allow_none=True)
    extra_files = fields.List(fields.Nested(FileInstallSchema), load_default=[])
    directories = fields.List(fields.Nested(DirectorySchema), load_default=[])

class DockerSchema(Schema):
    enabled = fields.Bool(load_default=False)
    base_image = fields.Str(load_default="registry.access.redhat.com/ubi9/ubi-minimal")
    entrypoint = fields.List(fields.Str())
    cmd = fields.List(fields.Str(), load_default=[])
    smoke_test_port = fields.Int(load_default=9100)

class UpstreamSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["github"]))
    repo = fields.Str(required=True)
    strategy = fields.Str(load_default="latest_release")

class ExtraSourceSchema(Schema):
    url = fields.Str(required=True)
    filename = fields.Str(required=True)

class BuildSchema(Schema):
    method = fields.Str(required=True, validate=validate.OneOf(["binary_repack", "source_build"]))
    binary_name = fields.Str(required=True)
    extra_binaries = fields.List(fields.Str(), load_default=[])
    extra_sources = fields.List(fields.Nested(ExtraSourceSchema), load_default=[])

class ArtifactsSchema(Schema):
    rpm = fields.Nested(RPMSchema)
    docker = fields.Nested(DockerSchema)

class ManifestSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    version = fields.Str(required=True)
    upstream = fields.Nested(UpstreamSchema, required=True)
    build = fields.Nested(BuildSchema, required=True)
    artifacts = fields.Nested(ArtifactsSchema, required=True)