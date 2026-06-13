"""Local fixture loading for Google Workspace MCP-shaped tools."""

import base64
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class GmailHeader(BaseModel):
    """Gmail API-shaped message header."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    value: str = Field(min_length=1)


class GmailBody(BaseModel):
    """Gmail API-shaped message body."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    size: int
    data: str = Field(min_length=1)


class GmailPayload(BaseModel):
    """Gmail API-shaped message payload."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    mime_type: str = Field(alias="mimeType", min_length=1)
    headers: tuple[GmailHeader, ...]
    body: GmailBody
    parts: tuple["GmailPayload", ...] = ()

    def header(self, name: str) -> str:
        """Return one case-insensitive header value."""
        wanted = name.casefold()
        for header in self.headers:
            if header.name.casefold() == wanted:
                return header.value
        return ""


class GmailMessage(BaseModel):
    """Gmail API-shaped message."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    id: str = Field(min_length=1)
    thread_id: str = Field(alias="threadId", min_length=1)
    label_ids: tuple[str, ...] = Field(alias="labelIds")
    internal_date: str = Field(alias="internalDate", min_length=1)
    snippet: str = ""
    payload: GmailPayload

    @property
    def decoded_body(self) -> str:
        """Return the decoded Gmail body data."""
        return _decode_base64url(self.payload.body.data)


class GmailThread(BaseModel):
    """Synthetic Gmail thread returned by the local Gmail MCP-shaped tool."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    id: str = Field(min_length=1)
    history_id: str = Field(alias="historyId", min_length=1)
    messages: tuple[GmailMessage, ...]

    @property
    def subject(self) -> str:
        """Return the first message subject."""
        return self._first_message().payload.header("Subject")

    @property
    def sender(self) -> str:
        """Return the first message sender."""
        return self._first_message().payload.header("From")

    @property
    def body(self) -> str:
        """Return the first message decoded body."""
        return self._first_message().decoded_body

    def _first_message(self) -> GmailMessage:
        return self.messages[0]


class DrivePrincipal(BaseModel):
    """Drive API-shaped owner principal."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    email_address: str = Field(alias="emailAddress", min_length=3)
    display_name: str = Field(alias="displayName", min_length=1)


class DrivePermission(BaseModel):
    """Drive API-shaped permission entry."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    role: str = Field(min_length=1)
    domain: str | None = None


class DriveCapabilities(BaseModel):
    """Drive API-shaped file capabilities."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    can_download: bool = Field(alias="canDownload")
    can_edit: bool = Field(alias="canEdit")


class DriveFile(BaseModel):
    """Synthetic Drive file returned by the local Drive MCP-shaped tool."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    mime_type: str = Field(alias="mimeType", min_length=1)
    web_view_link: str = Field(alias="webViewLink", min_length=1)
    owners: tuple[DrivePrincipal, ...]
    permissions: tuple[DrivePermission, ...]
    capabilities: DriveCapabilities
    app_properties: dict[str, str] = Field(alias="appProperties")
    exported_text: str = Field(alias="exportedText", min_length=1)

    @property
    def content(self) -> str:
        """Return exported text content used by local read-file tools."""
        return self.exported_text


class GoogleWorkspaceFixture(BaseModel):
    """Loaded Gmail and Drive fixture set."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    gmail_threads: tuple[GmailThread, ...]
    drive_files: tuple[DriveFile, ...]


THREADS_ADAPTER: Final = TypeAdapter(tuple[GmailThread, ...])
FILES_ADAPTER: Final = TypeAdapter(tuple[DriveFile, ...])


def load_google_workspace_fixture(path: Path) -> GoogleWorkspaceFixture:
    """Load local Gmail and Drive fixtures from a fixture directory."""
    threads = THREADS_ADAPTER.validate_json(
        (path / "gmail_threads.json").read_text(encoding="utf-8"),
    )
    files = FILES_ADAPTER.validate_json(
        (path / "drive_files.json").read_text(encoding="utf-8"),
    )
    return GoogleWorkspaceFixture(gmail_threads=threads, drive_files=files)


def _decode_base64url(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8")
