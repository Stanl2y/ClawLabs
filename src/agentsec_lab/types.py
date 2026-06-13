"""Shared domain types for the controlled agent environment."""

from enum import StrEnum


class ToolName(StrEnum):
    """Tools exposed to the controlled target agent."""

    READ_FILE = "read_file"
    VENDOR_SEARCH = "vendor_search"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    SEND_TO_LOCAL_SINK = "send_to_local_sink"
    GMAIL_SEARCH_THREADS = "gmail.search_threads"
    GMAIL_GET_THREAD = "gmail.get_thread"
    DRIVE_SEARCH_FILES = "drive.search_files"
    DRIVE_READ_FILE_CONTENT = "drive.read_file_content"
    GMAIL_CREATE_DRAFT = "gmail.create_draft"


class DefenseMode(StrEnum):
    """Defense policy for one controlled scenario run."""

    BASELINE = "baseline"
    DEFENDED = "defended"
