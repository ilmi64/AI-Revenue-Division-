"""Check staged workforce artifact bytes against the repository's offline candidate list."""
import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat


_MANIFEST = Path(__file__).with_name("revenue_native_artifacts.json")
_MAX_ARTIFACT_BYTES = 2 * 1024**3


def _pin(value):
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        return "sha256", bytes.fromhex(value.removeprefix("sha256:"))
    if re.fullmatch(r"sha512-[a-zA-Z0-9+/]{86}==", value):
        return "sha512", base64.b64decode(value.removeprefix("sha512-"), validate=True)
    raise ValueError("invalid artifact digest pin")


def _verify(root_fd, item):
    name = item["file"]
    if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", name):
        raise ValueError("artifact must identify a local basename")
    algorithm, digest = _pin(item["integrity"])
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd)
    except FileNotFoundError:
        return "MISSING"
    except OSError:
        return "UNREADABLE"
    with os.fdopen(fd, "rb", buffering=0) as archive:
        before = os.fstat(archive.fileno())
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= _MAX_ARTIFACT_BYTES:
            return "UNREADABLE"
        if "size_bytes" in item and before.st_size != item["size_bytes"]:
            return "SIZE_MISMATCH"
        result = hashlib.new(algorithm)
        remaining = before.st_size
        while remaining:
            block = archive.read(min(remaining, 1024**2))
            if not block:
                return "CHANGED_DURING_READ"
            result.update(block)
            remaining -= len(block)
        after = os.fstat(archive.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        ):
            return "CHANGED_DURING_READ"
        return "MATCH" if hmac.compare_digest(result.digest(), digest) else "DIGEST_MISMATCH"


def _verify_inventory(directory, inventory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        return {item["file"]: _verify(fd, item) for item in inventory}
    finally:
        os.close(fd)


def verify_staged(directory, manifest, *, source_lock_directory=None):
    """Compare staged bytes without extracting archives, resolving dependencies or running code."""
    result = _verify_inventory(directory, manifest["artifacts"])
    source_locks = None
    if source_lock_directory is not None:
        source_locks = _verify_inventory(source_lock_directory, manifest["source_locks"])
    return {
        "artifact_checks": result,
        "all_candidate_bytes_match": bool(result) and all(status == "MATCH" for status in result.values()),
        "source_lock_checks": source_locks,
        "all_source_lock_bytes_match": bool(source_locks) and all(status == "MATCH" for status in source_locks.values()),
        "distribution_dependency_closure_verified": False,
        "installation_authorized": False,
        "native_execution_verified": False,
        "release_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staged_directory", type=Path)
    parser.add_argument("--source-lock-directory", type=Path, help="also check the pinned upstream build lockfiles")
    args = parser.parse_args()
    try:
        result = verify_staged(args.staged_directory, json.loads(_MANIFEST.read_bytes()),
                               source_lock_directory=args.source_lock_directory)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Artifact check unavailable: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    matches = result["all_candidate_bytes_match"]
    if args.source_lock_directory is not None:
        matches = matches and result["all_source_lock_bytes_match"]
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
