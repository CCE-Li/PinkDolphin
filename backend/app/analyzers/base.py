from abc import ABC, abstractmethod

from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext


class BaseAnalyzer(ABC):
    name: str

    @abstractmethod
    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        raise NotImplementedError

