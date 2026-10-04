# Development Guide

## Prerequisites

Before developing this project, ensure you have the following installed:

### [uv](https://docs.astral.sh/uv/)  
Python project and environment management.  
Install: [uv docs](https://docs.astral.sh/uv/getting-started/installation/)

### [make](https://www.gnu.org/software/make/)  
Run common project tasks via the `Makefile`.

#### macOS  
```sh
xcode-select --install
```

#### Windows  
```powershell
choco install make
```

#### Linux
Usually pre-installed. If not:
```sh
sudo apt install build-essential   # Debian/Ubuntu
sudo dnf groupinstall "Development Tools"   # Fedora
```

### [git](https://git-scm.com/downloads)  
Version control, and what `make repo` uses to initialise the repository.

### [GitHub CLI](https://cli.github.com)  
Lets `make repo` create the GitHub remote and apply the branch policies.  
Authenticate once with `gh auth login`.

### [Docker](https://docs.docker.com/get-docker/)  
For building and running containerized deployments.


## Installation in development mode

Install all dependencies including development tools:

```bash
uv sync
```

This creates a `.venv` folder and installs the project and default development
dependencies from `pyproject.toml` and the committed `uv.lock` file. After changing
dependencies, use `uv add`/`uv remove`, then run `uv lock` and commit the lockfile.

Activate the environment:

* **Linux / macOS (bash/zsh):**
  ```bash
  source .venv/bin/activate
  ```

* **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

* **Windows (cmd.exe):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

## Development Tasks

All tasks are defined in the `Makefile` for convenience.

### Running the Full Quality Gate

```bash
make qa
```

Runs **Ruff** for linting and formatting, **Mypy** for type checking, and **Pytest** for
the test suite. Each stage is also available on its own: `make lint`, `make format`,
`make typecheck` and `make test`.

### Running Unit Tests

Before running tests, configure environment variables in `.env.test` if needed.

```bash
make test
```

Executes the test suite using **Pytest**, without the lint, format and type checks.

### Creating the Repository

Initialise the local repository and create its first commit on `main`:

```bash
make repo
```

The same command then creates the GitHub remote, pushes `main`, and applies the branch
policies. The remote is private by default; to make it public:

```bash
make repo REPO_ARGS=--public
```

`main` is protected: pull requests need one approval including the code owner, all
conversations resolved, the branch up to date with `main`, linear history, and the `qa`
check green. Force pushes and branch deletion are rejected.

Branch rulesets are a paid GitHub feature on private repositories. On a free plan the
command says so, leaves `main` unprotected and finishes the rest; make the repository
public or upgrade the plan, then re-run `make repo` to apply the policies.

The local steps need only git; the remote ones need the
[GitHub CLI](https://cli.github.com) authenticated with `gh auth login`. Without it the
local repository is still created and nothing is pushed.

The command is safe to re-run: each step is skipped if it is already done, so an
interrupted run can be finished by running it again.

### Migrating to Git Worktrees

Migrate the repository to a shared bare-repository layout:

```bash
make worktree
```

This creates `.bare` for the shared Git history and a directory for the current
branch. If the current branch is not the remote default branch, a second directory
is created for that default branch. The converted repository root contains only
`.bare`, the `.git` pointer, and the worktree directories. Before converting, it
copies the complete original repository, including `.git`, to a sibling directory
named `<repo-name>-legacy-bak`, restores the original files to the current branch
worktree, and refuses to overwrite an existing backup or worktree layout. If the
migration fails, the original repository is restored and the temporary backup is
removed.

### Building the Project

```bash
make build
```

Generates a distribution package in the `dist/` directory.

### Releasing

Every push to `main` that passes QA cuts a release: the version is finalized,
tagged, and `main` is bumped to the next prerelease. You can control the release
process with the following options on the `.github/workflows/release.yml` workflow:

- `create-github-release` (on by default) — cuts a GitHub release for the new tag.
- `attach-distribution` (off by default) — builds the distribution and attaches it to the
  GitHub release as downloadable files. Requires `create-github-release` to also be on.
- `publish-to-pypi` (off by default) — builds the distribution and publishes it to PyPI.
  Only relevant if you distribute this project as a package.
- `publish-docker-image` (on in this project) — builds the Dockerfile and pushes the image to
  `ghcr.io/gvieralopez/network-monitor-tds`, tagged with the version and `latest`. Needs
  `packages: write` in the release job's `permissions`.
- `prepare-next-version` (on by default) — bumps `main` to the next prerelease once the
  release is out.

#### Publishing to PyPI

Set up Trusted Publishing so no API token has to be stored as a secret:

1. Go to <https://pypi.org/manage/account/publishing/>
2. Under "Add a new pending publisher," choose GitHub Actions
3. Fill in the workflow name `release.yml` and the environment name `pypi`
4. Save. PyPI will now trust publish requests coming from that workflow.

Then, in `.github/workflows/release.yml`, add `id-token: write` to `permissions`, enable
`publish-to-pypi`, and point the deployment environment at the project:

```yaml
    permissions:
      contents: write
      id-token: write
    with:
      cookie-pyrate-ref: ...
      publish-to-pypi: true
      pypi-project-url: https://pypi.org/project/network_monitor_tds/
```

Without `id-token: write` the whole workflow fails to start, so add it in the same edit.

### Cleaning Up

```bash
make clean
```

Removes build artifacts, caches, and temporary files.


### Building a Docker Image

```bash
make dockerimage
```

Generates a Docker image with the package pre-installed and ready to use. To try it on the local
network, with its data in a named volume:

```bash
docker run --rm --network host --cap-add NET_RAW --cap-add NET_ADMIN \
  -v nmtds-data:/data network-monitor-tds:latest
```

The image runs as a non-root user (uid 10001) and listens on `0.0.0.0:8000`. Both capabilities are
required: without them the container stops at start with `operation not permitted`. To keep the
data in a host folder instead, make it writable by uid 10001, or run with `--user` set to the
folder's owner.





## Pre-Commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run code quality checks automatically before each commit.

### Setup

Install the hooks:

```bash
make repo  # if you haven't already
uv run pre-commit install
```

Checks will now run automatically on every commit.

### Manual Execution

Trigger all hooks manually:

```bash
uv run pre-commit run --all-files
```

This runs the same lint, format and type checks as `make qa`, without the tests.

