from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import src.schemas as schemas
import src.models as models
from src.utils import sanitise_name

import datetime

async def create_tracked_entity_with_device(db: AsyncSession, tracked_entity: schemas.TrackedEntityCreate, device: schemas.DeviceCreate):
    db_tracked_entity = models.TrackedEntity(
        name=sanitise_name(tracked_entity.name),
        devices=[models.Device(mac_addr=device.mac_addr, hostname=device.hostname)],
        created_datetime=datetime.datetime.now()
    )
    db.add(db_tracked_entity)
    await db.commit()
    await db.refresh(db_tracked_entity)
    return db_tracked_entity

async def get_device_by_mac_addr(db: AsyncSession, mac_addr: str):
    db_result = await db.execute(select(models.Device).filter(models.Device.mac_addr == mac_addr))
    device = db_result.scalars().first()
    return device

async def get_tracked_entity_by_mac_addr(db: AsyncSession, mac_addr: str) -> schemas.TrackedEntity:
    db_result = await db.execute(select(models.TrackedEntity).join(models.Device).filter(models.Device.mac_addr == mac_addr))
    tracked_entity = db_result.scalars().first()
    return tracked_entity

async def get_tracked_entity_by_name(db: AsyncSession, name: str):
    db_result = await db.execute(select(models.TrackedEntity).filter(models.TrackedEntity.name == name))
    tracked_entity = db_result.scalars().first()
    return tracked_entity

async def update_tracked_entity_name(db: AsyncSession, tracked_entity: models.TrackedEntity, name: str):
    tracked_entity.name = sanitise_name(name)
    await db.commit()
    await db.refresh(tracked_entity)
    return tracked_entity

async def add_device_to_tracked_entity(db: AsyncSession, tracked_entity: models.TrackedEntity, device: models.Device):
    tracked_entity.devices.append(device)
    await db.commit()
    await db.refresh(tracked_entity)
    return tracked_entity

async def get_tracked_entity_names_by_mac_addrs(db: AsyncSession, mac_addrs: list[str]) -> list[str]:
    db_result = await db.execute(select(models.TrackedEntity.name).where(models.TrackedEntity.devices.any(models.Device.mac_addr.in_(mac_addrs))))
    names = db_result.scalars()
    return names

async def add_membership(db: AsyncSession, membership: schemas.MembershipCreate):
    db_membership = models.Membership(
        tracked_entity_id=membership.tracked_entity_id,
        group_id=membership.tracked_entity_id,
        joined_date=datetime.date.today()
    )
    db.add(db_membership)
    await db.commit()
    await db.refresh(db_membership)
    return db_membership

async def delete_membership(db: AsyncSession, membership: schemas.MembershipDelete):
    ident = {"tracked_entity_id": membership.tracked_entity_id, "group_id": membership.group_id}
    db_membership = db.get_one(models.Membership, ident)
    db.delete(db_membership)
    await db.commit()
