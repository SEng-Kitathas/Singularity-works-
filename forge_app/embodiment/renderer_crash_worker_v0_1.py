from __future__ import annotations

"""Renderer child that dies after receiving a valid render request."""

import json
import os
import sys

from forge_app.render.renderer_host import REQUEST_PROTOCOL


def main() -> int:
    request = json.loads(sys.stdin.read())
    if request.get("protocol") != REQUEST_PROTOCOL:
        return 4
    os._exit(93)


if __name__ == "__main__":
    raise SystemExit(main())
