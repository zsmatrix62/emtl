# This module is deprecated. Use EMTClient from emtl.client instead.
from warnings import warn

warn(
    "emtl.core is deprecated. Use 'from emtl import EMTClient' or 'from emtl.client import EMTClient' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .client import EMTClient  # noqa: F401

__all__ = ["EMTClient"]
