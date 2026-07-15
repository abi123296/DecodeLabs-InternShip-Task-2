"""
models.py
---------
Data shapes for the Movie Discovery API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MovieCreate(BaseModel):
    """What the client sends when adding a new movie."""
    title: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1888, le=2100)
    genre: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)   # e.g. ["mind-bending", "space"]
    rating: Optional[float] = Field(default=None, ge=0, le=10)
    watched: bool = False


class MovieUpdate(BaseModel):
    """What the client can send to update a movie. All optional."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1888, le=2100)
    genre: Optional[str] = None
    tags: Optional[list[str]] = None
    rating: Optional[float] = Field(default=None, ge=0, le=10)
    watched: Optional[bool] = None


class Movie(MovieCreate):
    """What gets sent back to the client."""
    id: int
