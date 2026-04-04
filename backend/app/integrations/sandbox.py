class MockSandboxAdapter:
    def inspect_behavior(self, subject: str | None, body_text: str | None) -> dict[str, object]:
        text = f"{subject or ''} {body_text or ''}".lower()
        suspicious_terms = ("urgent", "wire transfer", "password reset", "gift card", "invoice")
        hits = [term for term in suspicious_terms if term in text]
        return {"score": len(hits) * 8, "hits": hits}

