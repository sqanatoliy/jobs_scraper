"""
This module defines the GlobalLogicJob dataclass.

Classes:
    GlobalLogicJob: A dataclass representing a job listing 
    with attributes for title, link, and requirements.

Attributes:
    title (str | None): The title of the job.
    link (str | None): The URL link to the job listing.
    requirements (str | None): The requirements for the job.
"""
from dataclasses import dataclass


@dataclass
class GlobalLogicJob:
    """A dataclass representing a job listing with attributes for title, link, and requirements."""
    title: str | None
    link: str | None
    requirements: str | None
