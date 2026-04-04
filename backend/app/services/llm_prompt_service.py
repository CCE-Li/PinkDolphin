import json

from app.core.config import get_settings
from app.schemas.email import ParsedEmailSchema


class LLMPromptService:
    def build_messages(self, parsed_email: ParsedEmailSchema) -> list[dict[str, str]]:
        settings = get_settings()
        payload = {
            "message_id": parsed_email.message_id,
            "subject": parsed_email.subject,
            "from_email": parsed_email.from_email,
            "reply_to": parsed_email.reply_to,
            "return_path": parsed_email.return_path,
            "authentication_results": parsed_email.authentication_results,
            "links": parsed_email.links,
            "attachments": [
                {
                    "filename": item.get("filename"),
                    "content_type": item.get("content_type"),
                    "size": item.get("size"),
                    "sha256": item.get("sha256"),
                }
                for item in parsed_email.attachments
            ],
            "body_text": (parsed_email.body_text or "")[: settings.llm_max_input_chars],
            "body_html": (parsed_email.body_html or "")[: settings.llm_max_input_chars],
        }
        system_prompt = (
            "You are a phishing email security analyzer. "
            "Return strict JSON with keys: score, severity, summary, signals, evidence. "
            "score must be an integer from 0 to 100. "
            "severity must be one of: info, low, medium, high, critical. "
            "signals must be an array of short strings. "
            "evidence must be an object. "
            "Do not include markdown."
        )
        user_prompt = f"Analyze this email for phishing risk:\n{json.dumps(payload, ensure_ascii=True)}"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
