from marshmallow import Schema, fields, validate

class UpstreamSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["github"]))
    repo = fields.Str(required=True)
    strategy = fields.Str(load_default="latest_release")

class BuildSchema(Schema):
    method = fields.Str(required=True, validate=validate.OneOf(["binary_repack", "source_build"]))
    binary_name = fields.Str(required=True)

class RPMSchema(Schema):
    enabled = fields.Bool(load_default=False)
    targets = fields.List(fields.Str(), load_default=["el8", "el9", "el10"])
    summary = fields.Str()
    service_file = fields.Bool(load_default=False)

class DockerSchema(Schema):
    enabled = fields.Bool(load_default=False)
    base_image = fields.Str(load_default="gcr.io/distroless/static-debian12")
    entrypoint = fields.List(fields.Str())

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
