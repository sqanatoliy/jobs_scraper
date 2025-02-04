"""This module contains the DouJob class,
which is used to represent a job from the Dou.ua website."""
from dataclasses import dataclass


@dataclass
class DjinniJob:
    """A dataclass representing a job listing with attributes from the djinni.co website"""
    date: str
    title: str | None
    link: str | None
    description: str | None
    category: str | None
