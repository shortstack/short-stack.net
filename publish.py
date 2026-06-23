#!/usr/bin/env python3
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

from ssnet.config import load_config
from ssnet.site import build_site


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    cfg = load_config()
    aws = cfg["aws"]
    # Use the named profile locally; in CI set SSNET_AWS_PROFILE="" to fall back to
    # ambient credentials (e.g. GitHub OIDC).
    profile_name = os.environ.get("SSNET_AWS_PROFILE", aws.get("profile", ""))
    profile = ["--profile", profile_name] if profile_name else []

    local_images = Path("content/images")
    if local_images.is_dir():
        run(["aws", "s3", "sync", str(local_images),
             f"s3://{aws['images_bucket']}/content/images", "--only-show-errors", *profile])

    counts = build_site(cfg)
    print("built:", counts)

    run(["aws", "s3", "sync", "site/", f"s3://{aws['site_bucket']}",
         "--delete", "--only-show-errors", *profile])

    dist = aws.get("cloudfront_distribution_id")
    if dist:
        run(["aws", "cloudfront", "create-invalidation",
             "--distribution-id", dist, "--paths", "/*", *profile])
    else:
        print("WARN: cloudfront_distribution_id not set; skipped invalidation",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
