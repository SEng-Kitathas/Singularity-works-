"""Forge renderer process boundary and backend-neutral contracts."""

from .renderer_host import RenderReceipt, render_snapshot_with_fallback

__all__ = ["RenderReceipt", "render_snapshot_with_fallback"]
