"""Local Google Workspace MCP-shaped tool implementations."""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel, ConfigDict

from agentsec_lab.google_workspace.fixtures import (
    DriveFile,
    GmailThread,
    GoogleWorkspaceFixture,
)


@dataclass(slots=True)
class GoogleWorkspaceToolError(Exception):
    """Typed error raised by local Google Workspace MCP-shaped tools."""

    reason: str

    @override
    def __str__(self) -> str:
        """Return the execution failure reason."""
        return self.reason


class GmailDraft(BaseModel):
    """Local Gmail draft sink record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    to: str
    subject: str
    body: str


@dataclass(slots=True)
class GoogleWorkspaceToolbox:
    """Local-only Gmail and Drive tool surface with draft evidence."""

    fixture: GoogleWorkspaceFixture
    draft_path: Path
    draft_count: int = 0

    def gmail_search_threads(self, query: str) -> tuple[GmailThread, ...]:
        """Search local Gmail threads by subject text."""
        query_lower = query.casefold()
        return tuple(
            thread
            for thread in self.fixture.gmail_threads
            if query_lower in thread.subject.casefold()
        )

    def gmail_get_thread(self, thread_id: str) -> GmailThread:
        """Read one local Gmail thread by id."""
        for thread in self.fixture.gmail_threads:
            if thread.id == thread_id:
                return thread
        raise GoogleWorkspaceToolError(reason=f"gmail thread not found: {thread_id}")

    def drive_search_files(self, query: str) -> tuple[DriveFile, ...]:
        """Search local Drive files by title."""
        return tuple(
            file
            for file in self.fixture.drive_files
            if _drive_file_matches_query(file, query)
        )

    def drive_read_file_content(self, file_id: str) -> DriveFile:
        """Read one local Drive file by id."""
        for file in self.fixture.drive_files:
            if file.id == file_id:
                return file
        raise GoogleWorkspaceToolError(reason=f"drive file not found: {file_id}")

    def gmail_create_draft(self, to: str, subject: str, body: str) -> GmailDraft:
        """Create one local Gmail draft evidence record."""
        self.draft_count += 1
        draft = GmailDraft(
            id=f"draft-local-{self.draft_count:03d}",
            to=to,
            subject=subject,
            body=body,
        )
        self.draft_path.parent.mkdir(parents=True, exist_ok=True)
        with self.draft_path.open("a", encoding="utf-8") as draft_file:
            _ = draft_file.write(f"{draft.model_dump_json()}\n")
        return draft


def _drive_file_matches_query(file: DriveFile, query: str) -> bool:
    haystack = "\n".join(
        (
            file.name,
            file.exported_text,
            file.app_properties.get("classification", ""),
            file.app_properties.get("source", ""),
        ),
    ).casefold()
    query_lower = query.casefold()
    if query_lower in haystack:
        return True

    tokens = {
        token
        for token in "".join(
            char if char.isalnum() else " "
            for char in query_lower
        ).split()
        if len(token) >= 3
    }
    if not tokens:
        return False
    matches = sum(1 for token in tokens if token in haystack)
    return matches >= min(2, len(tokens))
