"""Base module for all the RPG code."""

from .rpg import rpg_instance
from .commands import parser as _parser

on_message = _parser.on_message

__all__ = ["rpg_instance", "on_message"]
