"""Read-only filesystem and enrollment checks for local OCC commissioning."""

import os
from pathlib import Path
from stat import S_ISDIR, S_ISREG, S_ISVTX

from occ_durable_receipt_anchor import DurableReceiptAnchor
from occ_signed_visibility import ReceiptJournal


def _identity(info):
    return info.st_dev, info.st_ino


def _file_state(info):
    return _identity(info), info.st_mode, info.st_uid, info.st_nlink, info.st_size, info.st_ctime_ns


def _protected_state(path, expected_uid):
    if type(expected_uid) is not int or expected_uid < 0:
        raise ValueError("custody owner UID must be explicitly configured")
    path = Path(path).absolute()
    if ".." in path.parts:
        raise ValueError("custody paths may not use parent traversal")
    filesystem_owner = Path(path.anchor).stat().st_uid
    for parent in reversed(path.parent.parents):
        info = parent.lstat()
        if not S_ISDIR(info.st_mode):
            raise ValueError("custody path traverses a link or non-directory")
        if (
            info.st_uid not in (filesystem_owner, expected_uid)
            or info.st_mode & 0o022 and not (info.st_uid == filesystem_owner and info.st_mode & S_ISVTX)
        ):
            raise ValueError("custody path traverses a shared or untrusted directory")
    parent = path.parent.lstat()
    item = path.lstat()
    if (
        not S_ISDIR(parent.st_mode) or parent.st_uid != expected_uid or parent.st_mode & 0o077
        or not S_ISREG(item.st_mode) or item.st_uid != expected_uid
        or item.st_mode & 0o077 or item.st_nlink != 1
    ):
        raise ValueError("custody database and its directory must be owner-private and unaliased")
    for suffix in ("-journal", "-wal", "-shm"):
        try:
            path.with_name(path.name + suffix).lstat()
        except FileNotFoundError:
            continue
        raise ValueError("custody database has a SQLite sidecar")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if _file_state(os.fstat(descriptor)) != _file_state(item):
            raise ValueError("custody database changed during header verification")
        header = os.read(descriptor, 20)
        if not header.startswith(b"SQLite format 3\x00") or header[18:20] != b"\x01\x01":
            raise ValueError("custody database must use the rollback journal format")
    finally:
        os.close(descriptor)
    return _file_state(parent), _file_state(item)


def preflight_protected_custody(
    journal, *, trust, now, expected_enrollment, journal_uid, authority_uid,
):
    """Check protected, quiescent files and aligned enrolled custody, without a write."""
    if not isinstance(journal, ReceiptJournal) or not isinstance(journal.anchor, DurableReceiptAnchor):
        raise ValueError("a durable company custody journal is required")
    paths = ((journal.path, journal_uid), (journal.anchor.path, authority_uid))
    before = tuple(_protected_state(path, owner) for path, owner in paths)
    (journal_dir, journal_file), (authority_dir, authority_file) = before
    if journal_dir[0] == authority_dir[0] or journal_file[0] == authority_file[0]:
        raise ValueError("custody authority and receipt journal need distinct directories and files")
    view = journal.preflight_witnessed_custody(
        trust=trust, now=now, expected_enrollment=expected_enrollment,
    )
    if tuple(_protected_state(path, owner) for path, owner in paths) != before:
        raise ValueError("custody files changed during read-only verification")
    return {**view, "local_file_protection_verified": True}
