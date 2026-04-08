from abc import ABC, abstractmethod

from app.models.schemas import CheckResult
from app.services.content_parser import ParsedContent


class BaseCheck(ABC):
    check_id: str
    name: str

    @abstractmethod
    def run(self, content: ParsedContent) -> CheckResult:
        ...
