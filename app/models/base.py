from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TenantMixin:
    """All tenant-scoped models inherit this.

    Note: Models should define org_id explicitly with ForeignKey.
    This mixin is for future tenant-related logic.
    """

    pass
