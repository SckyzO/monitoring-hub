# State Management

How Monitoring Hub tracks and manages exporter versions.

## Catalog System

The `catalog.json` file contains all deployed exporters and their versions.

## Change Detection

State Manager compares:

- Local manifest versions
- Deployed catalog versions
- Force rebuild flags

## Version Comparison

Version format handling:

- Strips `v` prefix for comparison
- Supports semantic versioning
- Handles custom version schemes
