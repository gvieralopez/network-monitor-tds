from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, UniqueConstraint
from sqlalchemy.schema import CreateTable

from network_monitor_tds.infrastructure.db.models import NAMING_CONVENTION, Base


def test_base_metadata_uses_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_naming_convention_names_constraints() -> None:
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    Table("parent", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", ForeignKey("parent.id")),
        Column("code", String),
        UniqueConstraint("code"),
    )

    ddl = str(CreateTable(child))

    assert "CONSTRAINT pk_child" in ddl
    assert "CONSTRAINT fk_child_parent_id_parent" in ddl
    assert "CONSTRAINT uq_child_code" in ddl
