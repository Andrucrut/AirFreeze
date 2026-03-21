"""
Pydantic layer base.

`SchemaBase` centralizes ORM mode and common config for API schemas.
"""


from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    """Base Pydantic model: allow building from ORM objects (`from_attributes`)."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )
