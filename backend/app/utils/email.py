from email.utils import parseaddr


def normalize_email_address(value: str | None) -> str | None:
    if not value:
        return None
    _, address = parseaddr(value)
    address = address.strip().lower()
    return address or None


def extract_domain_from_email(value: str | None) -> str | None:
    address = normalize_email_address(value)
    if not address or "@" not in address:
        return None
    return address.split("@", maxsplit=1)[1]

