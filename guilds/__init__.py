"""Base module for all the guilds code."""

import guilds
from .guilds import guilds_instance, Guild, Party
from .commands import parser as _parser

on_message = _parser.on_message

__all__ = ["guilds_instance", "on_message", "Guild", "Party"]
