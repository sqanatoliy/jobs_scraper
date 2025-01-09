from dataclasses import dataclass
from typing import Optional
from .base_config import BaseConfig


@dataclass
class DouScraperConfig(BaseConfig):
    db_path: str
    telegram_token: str
    chat_id: str
    category: Optional[str] = None
    experience: Optional[str] = None
    city: Optional[str] = None
    remote: bool = False
    relocation: bool = False
    no_exp: bool = False


@dataclass
class GlobalLogicScraperConfig(BaseConfig):
    db_path: str
    telegram_token: str
    chat_id: str
    keywords: str
    experience: str
    locations: str
    freelance: bool = False
    remote: bool = False
    hybrid: bool = False
    on_site: bool = False

