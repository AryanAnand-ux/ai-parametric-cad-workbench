"""
models/__init__.py — SQLAlchemy ORM Model Registry
====================================================
Import all models here so Base.metadata knows about all tables.
"""

from database import Base
from models.user import User
from models.project import Project, Generation, Version

__all__ = ["Base", "User", "Project", "Generation", "Version"]
