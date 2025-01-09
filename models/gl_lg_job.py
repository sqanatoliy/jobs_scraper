from dataclasses import dataclass
from typing import Optional


@dataclass
class GlobalLogicJob:
    title: str | None
    link: str | None
    requirements: str | None

