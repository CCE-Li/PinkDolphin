from app.analyzers.attachment import AttachmentAnalyzer
from app.analyzers.base import BaseAnalyzer
from app.analyzers.behavior import BehaviorAnalyzer
from app.analyzers.content_rule import ContentRuleAnalyzer
from app.analyzers.header_auth import HeaderAuthAnalyzer
from app.analyzers.llm import LLMAnalyzer
from app.analyzers.url import UrlAnalyzer
from app.core.config import get_settings


def get_enabled_analyzers() -> list[BaseAnalyzer]:
    settings = get_settings()
    registry: dict[str, BaseAnalyzer] = {
        "header_auth": HeaderAuthAnalyzer(),
        "content_rule": ContentRuleAnalyzer(),
        "url": UrlAnalyzer(),
        "attachment": AttachmentAnalyzer(),
        "behavior": BehaviorAnalyzer(),
        "llm": LLMAnalyzer(),
    }
    return [registry[name] for name in settings.enabled_analyzers if name in registry]
