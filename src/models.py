from typing import List, Set, Optional
import enum
import src.utils as utils
from sqlalchemy import ForeignKey
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Enum
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
import datetime


class Base(AsyncAttrs, DeclarativeBase):
    pass

class Membership(Base):
    __tablename__= "membership"

    tracked_entity_id: Mapped[int] = mapped_column(ForeignKey("tracked_entity.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), primary_key=True)

    tracked_entity: Mapped["TrackedEntity"] = relationship(back_populates="groups")
    group: Mapped["Group"] = relationship(back_populates="members")

    joined_date: Mapped[datetime.date]

class TrackedEntity(Base):
    __tablename__ = "tracked_entity"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(utils.NAME_MAXLENGTH))
    created_datetime: Mapped[datetime.datetime]
    devices: Mapped[List["Device"]] = relationship(
        back_populates="tracked_entity",
        cascade="all, delete-orphan"
    )
    groups: Mapped[List["Membership"]] = relationship(back_populates="tracked_entity")

class Device(Base):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(primary_key=True)
    mac_addr: Mapped[str] = mapped_column(String(17))
    name: Mapped[Optional[str]] = mapped_column(String(20))
    tracked_entity_id: Mapped[int] = mapped_column(ForeignKey("tracked_entity.id"))
    tracked_entity: Mapped["TrackedEntity"] = relationship(back_populates="devices")

class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_date: Mapped[datetime.date]
    name: Mapped[str] = mapped_column(String(255))
    members: Mapped[List["Membership"]] = relationship(back_populates="group")
