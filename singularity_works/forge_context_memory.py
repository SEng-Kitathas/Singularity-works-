from __future__ import annotations

from .forge_context_semantic import ForgeContextSemanticMixin
from .forge_context_session import ForgeContextSessionMixin


class ForgeContextMemoryMixin(ForgeContextSessionMixin, ForgeContextSemanticMixin):
    """Aggregate mixin preserving the public ForgeContext composition surface."""

    pass
