from __future__ import annotations

import imaplib
import select
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.mail_account import MailAccount


class IMAPClient:
    @staticmethod
    def _wait_for_readable(client: imaplib.IMAP4, timeout_seconds: float) -> bool:
        sock = getattr(client, "sock", None)
        if sock is None:
            raise RuntimeError("imap client socket is unavailable")
        timeout = max(timeout_seconds, 0.0)
        readable, _, _ = select.select([sock], [], [], timeout)
        return bool(readable)

    @staticmethod
    def _readline_when_ready(client: imaplib.IMAP4, timeout_seconds: float) -> bytes | None:
        if not IMAPClient._wait_for_readable(client, timeout_seconds):
            return None
        return client.readline()

    @staticmethod
    def _format_select_error(mailbox_folder: str, status: str, payload: object) -> RuntimeError:
        details = ""
        if isinstance(payload, (list, tuple)):
            parts: list[str] = []
            for item in payload:
                if isinstance(item, bytes):
                    parts.append(item.decode(errors="replace"))
                elif item is not None:
                    parts.append(str(item))
            details = " | ".join(part for part in parts if part)
        elif payload is not None:
            details = str(payload)
        message = f"failed to select mailbox folder {mailbox_folder}"
        if status:
            message += f" (status={status})"
        if details:
            message += f": {details}"
        return RuntimeError(message)

    def connect(self, account: MailAccount, *, readonly: bool = True) -> imaplib.IMAP4:
        if account.use_ssl:
            client: imaplib.IMAP4 = imaplib.IMAP4_SSL(
                account.imap_host,
                account.imap_port,
                timeout=account.connect_timeout_seconds,
            )
        else:
            client = imaplib.IMAP4(
                account.imap_host,
                account.imap_port,
            )
        client.login(account.imap_username, account.imap_password)
        status, payload = client.select(account.mailbox_folder, readonly=readonly)
        if status != "OK":
            raise self._format_select_error(account.mailbox_folder, status, payload)
        return client

    @staticmethod
    def select_mailbox(client: imaplib.IMAP4, mailbox_folder: str, *, readonly: bool = True) -> None:
        status, payload = client.select(mailbox_folder, readonly=readonly)
        if status != "OK":
            raise IMAPClient._format_select_error(mailbox_folder, status, payload)

    @staticmethod
    def get_highest_uid(client: imaplib.IMAP4) -> int | None:
        status, payload = client.uid("search", None, "ALL")
        if status != "OK" or not payload or not payload[0]:
            return None
        items = [int(item) for item in payload[0].split() if item]
        return max(items) if items else None

    @staticmethod
    def search_since_uid(client: imaplib.IMAP4, last_seen_uid: int | None) -> list[int]:
        search_value = f"{(last_seen_uid or 0) + 1}:*"
        status, payload = client.uid("search", None, f"UID {search_value}")
        if status != "OK" or not payload or not payload[0]:
            return []
        return [int(item) for item in payload[0].split() if item]

    @staticmethod
    def fetch_rfc822(client: imaplib.IMAP4, uid: int) -> bytes:
        status, payload = client.uid("fetch", str(uid), "(RFC822)")
        if status != "OK" or not payload:
            raise RuntimeError(f"failed to fetch uid {uid}")
        for part in payload:
            if isinstance(part, tuple) and len(part) > 1:
                return bytes(part[1])
        raise RuntimeError(f"missing email body for uid {uid}")

    @staticmethod
    def uid_exists(client: imaplib.IMAP4, uid: int) -> bool:
        status, payload = client.uid("search", None, f"UID {uid}")
        if status != "OK" or not payload or not payload[0]:
            return False
        return any(item == str(uid).encode("ascii") for item in payload[0].split())

    @staticmethod
    def delete_message(client: imaplib.IMAP4, uid: int) -> None:
        status, _ = client.uid("store", str(uid), "+FLAGS", "(\\Deleted)")
        if status != "OK":
            raise RuntimeError(f"failed to mark uid {uid} as deleted")
        expunge_status, _ = client.expunge()
        if expunge_status != "OK":
            raise RuntimeError(f"failed to expunge uid {uid}")

    @staticmethod
    def noop(client: imaplib.IMAP4) -> None:
        status, _ = client.noop()
        if status != "OK":
            raise RuntimeError("imap noop failed")

    @staticmethod
    def idle_wait_for_activity(client: imaplib.IMAP4, timeout_seconds: int) -> bool:
        if not hasattr(client, "_new_tag") or not hasattr(client, "readline") or not hasattr(client, "send"):
            raise RuntimeError("imap client does not support IDLE")

        tag: bytes = client._new_tag()  # type: ignore[attr-defined]
        client.send(tag + b" IDLE\r\n")
        response = IMAPClient._readline_when_ready(client, min(max(timeout_seconds, 1), 10))
        if response is None:
            raise RuntimeError("imap idle continuation timed out")
        if not response.startswith(b"+"):
            raise RuntimeError(f"imap idle rejected: {response.decode(errors='replace')}")

        activity_detected = False
        deadline = time.monotonic() + max(timeout_seconds, 0)
        try:
            while time.monotonic() < deadline:
                line = IMAPClient._readline_when_ready(client, deadline - time.monotonic())
                if line is None:
                    break
                if not line:
                    break
                decoded = line.decode(errors="replace").strip().upper()
                if "EXISTS" in decoded or "RECENT" in decoded:
                    activity_detected = True
                    break
        finally:
            client.send(b"DONE\r\n")
            done_deadline = time.monotonic() + 10
            while time.monotonic() < done_deadline:
                done_response = IMAPClient._readline_when_ready(client, done_deadline - time.monotonic())
                if done_response is None:
                    raise RuntimeError("imap idle DONE acknowledgement timed out")
                if not done_response:
                    break
                if done_response.startswith(tag):
                    break
        return activity_detected

    @staticmethod
    def close(client: imaplib.IMAP4) -> None:
        try:
            client.close()
        except Exception:
            pass
        try:
            client.logout()
        except Exception:
            pass
