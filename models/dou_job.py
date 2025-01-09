from dataclasses import dataclass


@dataclass
class DouJob:
    date: str
    title: str | None
    link: str | None
    company: str | None
    salary: str | None
    cities: str | None
    sh_info: str | None
    category: str
    experience: str
