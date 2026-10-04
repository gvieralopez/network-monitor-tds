from pydantic import BaseModel, ConfigDict, Field


class Lease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True)

    hardware_address: str = Field(alias="hardwareAddress")
    address: str
    host_name: str | None = Field(default=None, alias="hostName")


class LeaseList(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    leases: list[Lease]


class LeaseResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True)

    status: str
    error_message: str | None = Field(default=None, alias="errorMessage")
    response: LeaseList | None = None
