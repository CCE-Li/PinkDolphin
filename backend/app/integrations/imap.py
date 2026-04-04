from __future__ import annotations

import imaplib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.mail_account import MailAccount


class IMAPClient:
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
        status, _ = client.select(account.mailbox_folder, readonly=readonly)
        if status != "OK":
            raise RuntimeError(f"failed to select mailbox folder {account.mailbox_folder}")
        return client

    @staticmethod
    def select_mailbox(client: imaplib.IMAP4, mailbox_folder: str, *, readonly: bool = True) -> None:
        status, _ = client.select(mailbox_folder, readonly=readonly)
        if status != "OK":
            raise RuntimeError(f"failed to select mailbox folder {mailbox_folder}")

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
    def close(client: imaplib.IMAP4) -> None:
        try:
            client.close()
        except Exception:
            pass
        try:
            client.logout()
        except Exception:
            pass
