import asyncio
from collections.abc import Awaitable, Callable

import typer

from network_monitor_tds import __version__
from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.plugins import (
    list_plugin_configs,
    set_plugin_enabled,
    sync_plugin_configs,
)
from network_monitor_tds.bootstrap import Container, build_container, prepare_database, serve
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.infrastructure.db.migrator import current_revision
from network_monitor_tds.plugins.host.registry import plugin_defaults
from network_monitor_tds.settings import AppSettings

app = typer.Typer(
    no_args_is_help=True, help="Network Monitor TDS", pretty_exceptions_show_locals=False
)
db_app = typer.Typer(no_args_is_help=True, help="Manage the database.")
plugins_app = typer.Typer(no_args_is_help=True, help="Manage discovery plugins.")
app.add_typer(db_app, name="db")
app.add_typer(plugins_app, name="plugins")


@app.command("serve", help="Run the monitor.")
def serve_command() -> None:
    asyncio.run(serve(AppSettings()))


@app.command("version", help="Show the installed version.")
def version_command() -> None:
    typer.echo(__version__)


@db_app.command("upgrade", help="Migrate the database to the latest schema.")
def db_upgrade_command() -> None:
    revision = _with_prepared_database(lambda container: current_revision(container.engine))
    typer.echo(f"Database is at revision {revision}")


@db_app.command("current", help="Show the database schema revision without changing it.")
def db_current_command() -> None:
    database_path = AppSettings().database_path
    if not database_path.exists():
        typer.echo(f"No database at {database_path} yet")
        return
    revision = _with_database(lambda container: current_revision(container.engine))
    typer.echo(revision or "Empty database")


@plugins_app.command("list", help="List installed plugins and whether they are enabled.")
def plugins_list_command() -> None:
    for line in _with_prepared_database(_plugin_lines):
        typer.echo(line)


@plugins_app.command("enable", help="Enable a plugin.")
def plugins_enable_command(plugin_id: str) -> None:
    _report(_update_plugin(PluginId(plugin_id), True))


@plugins_app.command("disable", help="Disable a plugin.")
def plugins_disable_command(plugin_id: str) -> None:
    _report(_update_plugin(PluginId(plugin_id), False))


def _with_prepared_database[T](action: Callable[[Container], Awaitable[T]]) -> T:
    async def prepare_then(container: Container) -> T:
        await prepare_database(container)
        await sync_plugin_configs(
            container.unit_of_work(),
            plugin_defaults(dict(container.plugins)),
            container.clock.now(),
        )
        return await action(container)

    return _with_database(prepare_then)


def _with_database[T](action: Callable[[Container], Awaitable[T]]) -> T:
    async def run() -> T:
        container = build_container(AppSettings())
        try:
            return await action(container)
        finally:
            await container.engine.dispose()

    return asyncio.run(run())


async def _plugin_lines(container: Container) -> list[str]:
    configs = await list_plugin_configs(container.unit_of_work())
    return [
        f"{_state(config):<4}{config.plugin_id:<14} {container.plugins[config.plugin_id].info.name}"
        for config in configs
        if config.plugin_id in container.plugins
    ]


def _update_plugin(plugin_id: PluginId, enabled: bool) -> PluginConfig:
    async def update(container: Container) -> PluginConfig:
        now = container.clock.now()
        return await set_plugin_enabled(container.unit_of_work(), plugin_id, enabled, now)

    try:
        return _with_prepared_database(update)
    except UnknownPluginError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def _report(config: PluginConfig) -> None:
    typer.echo(f"{config.plugin_id} is {_state(config)}")


def _state(config: PluginConfig) -> str:
    return "on" if config.enabled else "off"
