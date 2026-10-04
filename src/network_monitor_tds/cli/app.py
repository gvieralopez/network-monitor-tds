import asyncio
from collections.abc import Awaitable, Callable
from typing import Annotated

import typer
from pydantic import ValidationError

from network_monitor_tds import __version__
from network_monitor_tds.application.errors import UnknownPluginError
from network_monitor_tds.application.plugins import (
    get_plugin_config,
    list_plugin_configs,
    set_plugin_enabled,
    sync_plugin_configs,
    update_plugin_settings,
)
from network_monitor_tds.bootstrap import Container, build_container, serve
from network_monitor_tds.domain.plugins.models import PluginConfig, PluginId
from network_monitor_tds.infrastructure.db.migrator import current_revision, prepare_database
from network_monitor_tds.plugins.host.registry import PluginClass, plugin_defaults
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
    settings = AppSettings()
    _with_database(lambda container: prepare_database(container.engine, settings.database_path))
    asyncio.run(serve(settings))


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


@plugins_app.command("show", help="Show a plugin's settings.")
def plugins_show_command(plugin_id: str) -> None:
    async def show(container: Container) -> list[str]:
        config = await get_plugin_config(container.unit_of_work(), PluginId(plugin_id))
        return _settings_lines(container.plugins[config.plugin_id], config)

    for line in _guarded(lambda: _with_prepared_database(show)):
        typer.echo(line)


@plugins_app.command(
    "set", help="Change plugin settings, e.g. nmtds plugins set technitium url=http://dns:5380"
)
def plugins_set_command(
    plugin_id: str, assignments: Annotated[list[str], typer.Argument(help="key=value pairs")]
) -> None:
    async def update(container: Container) -> list[str]:
        unit_of_work, now = container.unit_of_work, container.clock.now()
        config = await get_plugin_config(unit_of_work(), PluginId(plugin_id))
        plugin = container.plugins[config.plugin_id]
        merged = {**config.settings, **_parse_assignments(assignments)}
        settings = plugin.settings_model.model_validate(merged).model_dump(mode="json")
        updated = await update_plugin_settings(unit_of_work(), config.plugin_id, settings, now)
        return [*_settings_lines(plugin, updated), "Restart nmtds serve to apply the changes."]

    for line in _guarded(lambda: _with_prepared_database(update)):
        typer.echo(line)


def _with_prepared_database[T](action: Callable[[Container], Awaitable[T]]) -> T:
    async def prepare_then(container: Container) -> T:
        await prepare_database(container.engine, container.settings.database_path)
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


def _settings_lines(plugin: PluginClass, config: PluginConfig) -> list[str]:
    secrets = plugin.settings_model.secret_fields()
    return [
        f"{name} = {'********' if name in secrets and value else value}"
        for name, value in config.settings.items()
    ]


def _parse_assignments(assignments: list[str]) -> dict[str, str]:
    pairs = [assignment.partition("=") for assignment in assignments]
    invalid = [
        assignment for assignment, (_, sign, _) in zip(assignments, pairs, strict=True) if not sign
    ]
    if invalid:
        typer.echo(f"Expected key=value, got: {', '.join(invalid)}", err=True)
        raise typer.Exit(code=2)
    return {key.strip(): value for key, _, value in pairs}


def _update_plugin(plugin_id: PluginId, enabled: bool) -> PluginConfig:
    async def update(container: Container) -> PluginConfig:
        now = container.clock.now()
        return await set_plugin_enabled(container.unit_of_work(), plugin_id, enabled, now)

    return _guarded(lambda: _with_prepared_database(update))


def _guarded[T](action: Callable[[], T]) -> T:
    try:
        return action()
    except (UnknownPluginError, ValidationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def _report(config: PluginConfig) -> None:
    typer.echo(f"{config.plugin_id} is {_state(config)}")


def _state(config: PluginConfig) -> str:
    return "on" if config.enabled else "off"
