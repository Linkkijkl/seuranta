from pydantic import BaseModel

class TrackedEntityBase(BaseModel):
    name: str

class TrackedEntityCreate(TrackedEntityBase):
    pass

class TrackedEntity(TrackedEntityBase):
    id: int

class DeviceBase(BaseModel):
    pass

class DeviceCreate(DeviceBase):
    mac_addr: str

class Device(DeviceBase):
    id: int
    mac_addr: str