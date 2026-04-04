import base64
import html
import re
from email import policy
from email.message import Message
from email.parser import BytesParser, Parser
from email.utils import getaddresses, parsedate_to_datetime, parseaddr
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

from app.schemas.email import ParsedEmailSchema, StructuredEmailAddress
from app.utils.hashing import sha256_hex


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


class HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "li", "tr", "table", "section"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw_payload = part.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _extract_links(body_text: str | None, body_html: str | None) -> list[str]:
    text_links = re.findall(r"https?://[^\s'\"<>]+", body_text or "")
    html_parser = LinkExtractor()
    if body_html:
        html_parser.feed(body_html)
    return list(dict.fromkeys([*text_links, *html_parser.links]))


def _extract_attachments(message: Message) -> list[dict[str, Any]]:
    attachments: list[dict[str, Any]] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        content_disposition = part.get_content_disposition()
        filename = part.get_filename()
        if content_disposition != "attachment" and not filename:
            continue
        payload = part.get_payload(decode=True) or b""
        attachments.append(
            {
                "filename": filename,
                "content_type": part.get_content_type(),
                "size": len(payload),
                "sha256": sha256_hex(payload),
                "content_base64": base64.b64encode(payload).decode("ascii") if payload else None,
            }
        )
    return attachments


def _html_to_text(body_html: str | None) -> str | None:
    if not body_html:
        return None
    parser = HtmlTextExtractor()
    parser.feed(body_html)
    text = parser.get_text()
    return text or None


def _text_to_html(body_text: str | None) -> str | None:
    if not body_text:
        return None
    escaped = html.escape(body_text)
    paragraphs = [segment for segment in escaped.splitlines()]
    rendered = "<br/>".join(paragraphs)
    return f"<div>{rendered}</div>"


def _extract_bodies(message: Message) -> tuple[str | None, str | None]:
    body_text: str | None = None
    body_html: str | None = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() == "text/plain" and body_text is None:
                body_text = _decode_payload(part)
            elif part.get_content_type() == "text/html" and body_html is None:
                body_html = _decode_payload(part)
    else:
        if message.get_content_type() == "text/html":
            body_html = _decode_payload(message)
        else:
            body_text = _decode_payload(message)
    if body_text is None and body_html:
        body_text = _html_to_text(body_html)
    if body_html is None and body_text:
        body_html = _text_to_html(body_text)
    return body_text, body_html


class EmailParserService:
    def parse_raw_email(self, raw_email: str) -> ParsedEmailSchema:
        try:
            message = BytesParser(policy=policy.default).parsebytes(raw_email.encode("utf-8", errors="replace"))
        except Exception:
            message = Parser(policy=policy.default).parsestr(raw_email)

        from_name, from_email = parseaddr(message.get("From", ""))
        reply_to = parseaddr(message.get("Reply-To", ""))[1] or None
        return_path = parseaddr(message.get("Return-Path", ""))[1] or None
        send_time = None
        if message.get("Date"):
            try:
                send_time = parsedate_to_datetime(message["Date"])
            except Exception:
                send_time = None

        body_text, body_html = _extract_bodies(message)
        return ParsedEmailSchema(
            message_id=message.get("Message-ID"),
            subject=message.get("Subject"),
            from_name=from_name or None,
            from_email=from_email or None,
            reply_to=reply_to,
            return_path=return_path,
            to_recipients=[
                StructuredEmailAddress(name=name or None, email=address)
                for name, address in getaddresses(message.get_all("To", []))
                if address
            ],
            cc_recipients=[
                StructuredEmailAddress(name=name or None, email=address)
                for name, address in getaddresses(message.get_all("Cc", []))
                if address
            ],
            authentication_results=message.get("Authentication-Results"),
            send_time=send_time,
            raw_headers={key: value for key, value in message.items()},
            body_text=body_text,
            body_html=body_html,
            links=_extract_links(body_text, body_html),
            attachments=_extract_attachments(message),
            raw_email=raw_email,
        )

    def parse_structured_email(self, payload: dict[str, Any]) -> ParsedEmailSchema:
        links = payload.get("links") or _extract_links(payload.get("body_text"), payload.get("body_html"))
        attachments: list[dict[str, Any]] = []
        for attachment in payload.get("attachments", []):
            content_bytes = base64.b64decode(attachment["content_base64"]) if attachment.get("content_base64") else b""
            attachments.append(
                {
                    "filename": attachment.get("filename"),
                    "content_type": attachment.get("content_type"),
                    "size": len(content_bytes),
                    "sha256": sha256_hex(content_bytes) if content_bytes else None,
                    "content_base64": attachment.get("content_base64"),
                }
            )
        return ParsedEmailSchema(
            message_id=payload.get("message_id"),
            subject=payload.get("subject"),
            from_name=payload.get("from_name"),
            from_email=parseaddr(payload.get("from_email", ""))[1] or payload.get("from_email"),
            reply_to=payload.get("reply_to"),
            return_path=payload.get("return_path"),
            to_recipients=[StructuredEmailAddress(**item) for item in payload.get("to_recipients", [])],
            cc_recipients=[StructuredEmailAddress(**item) for item in payload.get("cc_recipients", [])],
            authentication_results=payload.get("authentication_results"),
            send_time=payload.get("send_time"),
            raw_headers=payload.get("raw_headers") or {},
            body_text=payload.get("body_text") or _html_to_text(payload.get("body_html")),
            body_html=payload.get("body_html") or _text_to_html(payload.get("body_text")),
            links=links,
            attachments=attachments,
            raw_email=payload.get("raw_email"),
        )


def url_to_domain_path(url: str) -> tuple[str | None, str | None]:
    parsed = urlparse(url)
    return parsed.netloc.lower() or None, parsed.path or None
