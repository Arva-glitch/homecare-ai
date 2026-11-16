from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


def one_of(allowed: list[str], field: str):
    def _check(v):
        if v is not None and v not in allowed:
            raise ValueError(f"{field} must be one of: {', '.join(allowed)}")
        return v

    return AfterValidator(_check)


def choice(allowed: list[str], field: str):
    return Annotated[str, one_of(allowed, field)]


def optional_choice(allowed: list[str], field: str):
    return Annotated[str | None, one_of(allowed, field)]
