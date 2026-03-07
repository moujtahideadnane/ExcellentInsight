import math
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel
from sqlalchemy.types import JSON, TypeDecorator


def serialize_for_db(value: Any) -> Any:
    """Recursively convert *value* into JSON-safe primitives.

    The goal is to create a **serialization boundary** between our domain
    objects and the persistence layer.  Every custom class we expect to
    place into a JSON column should be converted into a combination of
    ``dict``, ``list``, ``str``, ``int``, ``float``, ``bool`` or ``None``.

    This helper is intentionally broad: it handles

    * ``pydantic.BaseModel`` instances via ``model_dump``
    * ``dataclasses`` (using ``asdict``)
    * objects exposing ``to_dict``, ``dict`` or ``__json__`` helpers
    * common primitives (dates/UUIDs/numbers/iterables)
    * numpy/polars scalar wrappers via ``.item()``

    Anything unknown is converted with ``str()`` as a last resort to avoid
    database errors; this keeps the transaction from failing due to an
    unanticipated custom class and encourages developers to add explicit
    serialization support when necessary.
    """

    # short-circuit for common immutable primitives
    if value is None:
        return None
    if isinstance(value, (str, int, bool)):
        return value
    # Handle floats specially because NaN/Inf are not JSON-safe
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    # pydantic models
    if isinstance(value, BaseModel):
        return serialize_for_db(value.model_dump())

    # dataclasses
    if is_dataclass(value):
        return serialize_for_db(asdict(value))

    # built-in containers
    if isinstance(value, dict):
        return {k: serialize_for_db(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_for_db(v) for v in value]

    # datetime-like
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    # uuid
    if isinstance(value, uuid.UUID):
        return str(value)

    # numpy/polars scalar wrappers
    if hasattr(value, "item") and callable(value.item):
        try:
            return serialize_for_db(value.item())
        except Exception:
            pass

    # duck-types: helpful conversion helpers
    for attr in ("to_dict", "dict", "__json__"):
        if hasattr(value, attr) and callable(getattr(value, attr)):
            try:
                return serialize_for_db(getattr(value, attr)())
            except Exception:
                pass

    # Fallback: convert to string to avoid blowing up the bind phase.
    return str(value)


class JSONSafe(TypeDecorator):
    """SQLAlchemy type which automatically runs ``serialize_for_db`` when
    binding parameters.

    Any column declared with this type will never see raw Python objects;
    ``process_bind_param`` is called by the dialect before sending the value
    to the database driver.  This keeps the serialization logic close to the
    database schema and ensures future domain classes are handled uniformly.
    """

    impl = JSON

    cache_ok = True

    def process_bind_param(self, value: Any, dialect):
        return serialize_for_db(value)

    def process_result_value(self, value: Any, dialect):
        # nothing special on load; JSON returns primitives already
        return value
