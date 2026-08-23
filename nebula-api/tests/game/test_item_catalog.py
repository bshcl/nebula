"""Tests for item_masters catalog and seed."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.game.inventory.catalog import get_item_master, npc_gift_reject_reason
from app.game.inventory.seed import seed_item_masters
from app.infra.models import Base, ItemMaster
from app.shared.item_types import GrantSource, ItemCategory


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_seed_is_idempotent(db) -> None:
    assert seed_item_masters(db) == 2
    assert seed_item_masters(db) == 0
    assert db.query(ItemMaster).count() == 2


def test_star_candy_is_npc_giftable(db) -> None:
    seed_item_masters(db)
    item = get_item_master(db, "star_candy")
    assert item is not None
    assert item.category == ItemCategory.GIFT
    assert item.grant_source == GrantSource.NPC_GIFT
    assert npc_gift_reject_reason(item) is None


def test_navigator_emblem_not_npc_giftable(db) -> None:
    seed_item_masters(db)
    item = get_item_master(db, "navigator_emblem")
    assert item is not None
    assert item.grant_source == GrantSource.QUEST_REWARD
    assert npc_gift_reject_reason(item) == "not_giftable_by_npc"


def test_unknown_item_reject_reason(db) -> None:
    assert npc_gift_reject_reason(get_item_master(db, "no_such_thing")) == "unknown_item"


def test_inactive_item_reject_reason(db) -> None:
    db.add(
        ItemMaster(
            item_id="retired_candy",
            display_name="Retired Candy",
            category=ItemCategory.GIFT,
            grant_source=GrantSource.NPC_GIFT,
            is_active=False,
            stackable=True,
        )
    )
    db.commit()
    item = get_item_master(db, "retired_candy")
    assert npc_gift_reject_reason(item) == "inactive_item"
