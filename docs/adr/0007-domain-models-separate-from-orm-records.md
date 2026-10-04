# Domain models are separate from ORM records

SQLAlchemy ORM models (`DeviceRecord`, `FactRecord` …) live in `infrastructure/db/models.py` and repositories map them to and from frozen domain dataclasses. Using ORM entities as the domain model would have meant fewer types, but ORM objects must be mutable, async lazy loading is a common source of `MissingGreenlet` bugs, and the domain would depend on SQLAlchemy. The cost is one small `*_from_record` / `write_*` pair per entity.

## Consequences

- Sessions use `expire_on_commit=False` and records have no relationships; repositories query explicitly.
- Enums are stored as plain strings, not SQLAlchemy `Enum` columns, so adding a category or event kind never needs a migration.
- A test assigns `SqlUnitOfWork` to the `UnitOfWork` port so mypy proves the adapters match the ports.
