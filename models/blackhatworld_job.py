from dataclasses import dataclass


@dataclass
class BlackHatWorldJob:
    """A dataclass representing a job listing with attributes from the Dou.ua website"""
    title: str | None
    link: str | None

