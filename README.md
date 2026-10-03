# Network Monitor TDS

A network monitor that doesn't sucks

## Quick Start

### Prerequisites
- [uv](https://docs.astral.sh/uv/) - Python package manager

### Installation

```bash
uv sync
```

The generated `uv.lock` is committed for reproducible installations. Use `uv add`
and `uv remove` to change dependencies, then run `uv lock`. The lockfile is the
deployment source of truth; a separate `requirements.txt` is not generated.

### Run

```bash
cp .env.example .env  # Configure as needed
uv run nmtds
```

## Development

For setup, testing, building, and other development tasks, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

Contributions are welcome!  
Please ensure all QA checks and tests pass before opening a pull request.


---

<sub>🚀 Project starter provided by [Cookie Pyrate](https://github.com/gvieralopez/cookie-pyrate)</sub>
