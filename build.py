#!/usr/bin/env python3
from ssnet.config import load_config
from ssnet.site import build_site


def main() -> int:
    counts = build_site(load_config())
    print("built: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
