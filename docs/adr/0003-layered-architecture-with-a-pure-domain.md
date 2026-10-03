# Layered architecture with a pure domain

The package is split into `domain` (frozen dataclasses and pure functions, no I/O, no pydantic, no SQLAlchemy), `application` (use cases that talk to the outside only through `Protocol` ports), and adapters around them (`infrastructure`, `plugins`, `web`, `cli`), wired together in `bootstrap.py`. A flatter layout was the first proposal and was rejected as not future-proof; the layering makes the logic that decides device names, categories and presence testable without a database or network, and lets storage, packet capture or the web framework be swapped by touching one adapter.

## Consequences

- Dependencies point inward only: nothing imports `web`, and the domain imports nothing from the project outside itself.
- The web layer receives a small `WebContext` instead of the bootstrap container, to avoid a circular import.
