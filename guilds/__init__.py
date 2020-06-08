"""Base module for all the guilds code."""

import guilds
from .guilds import guilds_instance, Guild, Party
from .commands import parser, owner_parser

on_message = parser.on_message
on_owner_message = owner_parser.on_message

__all__ = ["guilds_instance", "on_message", "Guild", "Party"]
