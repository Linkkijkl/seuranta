import pytest
import string
from fastapi.testclient import TestClient
from src.lease_monitor import Lease
import src.database as database
import src.models as models
from sqlalchemy import select


@pytest.mark.asyncio
async def test_name_form_minor_sanitisation(async_client, async_session):
    form = {"username": "45spoons."}
    response = await async_client.post("/name-form",  data=form)
    assert response.status_code == 302

    entity = await async_session.get_one(models.TrackedEntity, 1)

    assert entity.name == "45spoons"

@pytest.mark.asyncio
async def test_name_form_creates_device(async_client, async_session):
    form = {"username": "45spoons"}
    response = await async_client.post("/name-form",  data=form)
    assert response.status_code == 302

    device = await async_session.get_one(models.Device, 1)

    assert device.mac_addr == "11:aa:22:bb:33:cc"

@pytest.mark.asyncio
async def test_name_form_links_device(async_client, async_session):
    form = {"username": "45spoons"}
    response = await async_client.post("/name-form",  data=form)
    assert response.status_code == 302

    entity = await async_session.get_one(models.TrackedEntity, 1)
    device = await async_session.get_one(models.Device, 1)

    assert device.tracked_entity_id == entity.id

@pytest.mark.asyncio
async def test_name_form_changes_name(async_client, async_session):
    form = {"username": "45spoons"}
    response = await async_client.post("/name-form",  data=form)
    assert response.status_code == 302

    entity = await async_session.get_one(models.TrackedEntity, 1)
    device = await async_session.get_one(models.Device, 1)

    assert device.tracked_entity_id == entity.id

    form = {"username": "spoons"}
    response = await async_client.post("/name-form",  data=form)
    assert response.status_code == 302

    entity = await async_session.get_one(models.TrackedEntity, 1)
    device = await async_session.get_one(models.Device, 1)

    assert entity.name == "spoons"
    assert device.tracked_entity_id == entity.id
