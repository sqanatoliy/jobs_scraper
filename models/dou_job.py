"""This module contains the DouJob class, 
which is used to represent a job from the Dou.ua website."""
from dataclasses import dataclass


@dataclass
class DouJob:
    """A dataclass representing a job listing with attributes from the Dou.ua website"""
    date: str
    title: str | None
    link: str | None
    company: str | None
    salary: str | None
    cities: str | None
    sh_info: str | None
    category: str
    experience: str
