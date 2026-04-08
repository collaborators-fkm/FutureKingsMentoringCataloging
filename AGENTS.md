# AGENTS

## Type Organization

- Put project-local shared types, dataclasses, and `TypedDict` definitions in `app_types.py` unless they are only used in `configuration.py`.
- Import shared app types from `app_types.py` instead of redefining them in feature modules.
