from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select # type: ignore
from .lease_monitor import Lease


def get_db_engine():
    SQLITE_FILE = "seuranta.db"
    SQLITE_URL = f"sqlite:///{SQLITE_FILE}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(SQLITE_URL, connect_args=connect_args)
    return engine

def get_session():
    with Session(get_db_engine()) as session:
        yield session


class TrackedEntityBase(SQLModel):
    name: str = Field(index=True, unique=True)


class TrackedEntity(TrackedEntityBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    devices: list["Device"] = Relationship(back_populates="trackedentity", cascade_delete=True)
    created_date: str


class TrackedEntityCreate(TrackedEntityBase):
    pass


class TrackedEntityPublic(TrackedEntityBase):
    id: int
    created_date: str


class DeviceBase(SQLModel):
    name: str = Field(index=True)
    mac: str = Field(index=True, unique=True)
    trackedentity_id: int = Field(index=True, foreign_key="trackedentity.id", ondelete="CASCADE")


class Device(DeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trackedentity: TrackedEntity | None = Relationship(back_populates="devices")


class DeviceCreate(DeviceBase):
    pass


class DevicePublic(DeviceBase):
    id: int


class TrackedEntityPublicWithDevices(TrackedEntityPublic):
    devices: list[DevicePublic]


class DevicePublicWithTrackedEntity(DevicePublic):
    trackedentity: TrackedEntityPublic | None = None


def get_db_device(lease: Lease, session: Session) -> Device | None:
    query = select(Device).where(Device.mac == lease.mac_addr)
    return session.exec(query).first()
