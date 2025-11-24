from pydantic import BaseModel

class TrackedEntityBase(BaseModel):
    name: str

class TrackedEntityCreate(TrackedEntityBase):
    pass

class TrackedEntity(TrackedEntityBase):
    id: int

class DeviceBase(BaseModel):
    pass

class DeviceUpdate(DeviceBase):
    name: str

class DeviceCreate(DeviceBase):
    mac_addr: str
    hostname: str

class Device(DeviceBase):
    id: int
    mac_addr: str

class MembershipBase(BaseModel):
    pass

class MembershipCreate(MembershipBase):
    tracked_entity_id: int
    group_id: int

class MembershipDelete(MembershipBase):
    tracked_entity_id: int
    group_id: int