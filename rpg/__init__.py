"""Base module for all the RPG code."""

from .rpg import load
from .commands import parser as _parser

on_message = _parser.on_message

__all__ = ["load", "on_message"]
