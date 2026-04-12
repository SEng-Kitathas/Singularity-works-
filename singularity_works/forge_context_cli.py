from __future__ import annotations

# ---------------------------------------------------------------------------
# CLI (backward compat + new commands)
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Singularity Works Context Manager v4.0")
    sub = parser.add_subparsers(dest="cmd")

    for cmd, add_args in [
        ("init",     [("--name", True), ("--root", False, "."), ("--type", False, "unknown"),
                      ("--desc", False, ""), ("--file", False, ".forge-context.json")]),
        ("summary",  [("--file", False, ".forge-context.json")]),
        ("verify",   [("--file", False, ".forge-context.json")]),
        ("context",  [("--file", False, ".forge-context.json"), ("--radical", False, None)]),
        ("task",     [("--file", False, ".forge-context.json"), ("--desc", True), ("--priority", False, "medium")]),
        ("decision", [("--file", False, ".forge-context.json"), ("--text", True), ("--why", True)]),
        ("link-shadow", [("--file", False, ".forge-context.json"), ("--type", True), ("--path", True)]),
    ]:
        p = sub.add_parser(cmd)
        for spec in add_args:
            name, required, *rest = spec
            default = rest[0] if rest else None
            p.add_argument(name, required=required) if required else p.add_argument(name, default=default)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    from .forge_context import ForgeContext
    ctx = ForgeContext(getattr(args, "file", ".forge-context.json"))

    if args.cmd == "init":
        ctx.init(args.name, args.root, args.type, args.desc)
        ctx.save()
        print(f"Initialized: {ctx.path}")
        print(ctx.summary())
    elif args.cmd == "summary":
        ctx.load()
        print(ctx.summary())
    elif args.cmd == "verify":
        ctx.load()
        print("✓ Integrity valid" if ctx.verify() else "✗ Hash mismatch")
    elif args.cmd == "context":
        ctx.load()
        radical = getattr(args, "radical", None)
        hints = [radical] if radical else None
        print(ctx.compile_context(radical_hints=hints))
    elif args.cmd == "task":
        ctx.load()
        tid = ctx.add_task(args.desc, args.priority)
        ctx.save()
        print(f"Task added: {tid}")
    elif args.cmd == "decision":
        ctx.load()
        did = ctx.add_decision(args.text, args.why)
        ctx.save()
        print(f"Decision recorded: {did}")
    elif args.cmd == "link-shadow":
        ctx.load()
        ctx.link_shadow_doc(args.type, args.path)
        ctx.save()
        print(f"Linked {args.type} → {args.path}")


