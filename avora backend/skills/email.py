"""
===============================================================
                    AI FRIEND GMAIL SKILL
===============================================================

Advanced Gmail integration for AI Friend.

Features:
    • Multiple Gmail accounts
    • Add/connect Gmail accounts
    • Switch active Gmail account
    • Remove Gmail accounts
    • Persistent OAuth tokens per account
    • Read emails
    • Send emails
    • Reply to emails
    • Forward emails
    • Search emails
    • Mark read/unread
    • Star/unstar
    • Delete/trash
    • Restore from trash
    • Archive
    • Create drafts
    • Attachments
    • Settings integration

Requires:
    settings.py
    credentials.json
"""

from __future__ import annotations

import os
import base64
import mimetypes
import json
import re

from pathlib import Path
from email.message import EmailMessage
from email.utils import parseaddr

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover - optional dependency
    Credentials = None
    InstalledAppFlow = None
    Request = None
    build = None

from settings import (
    get_setting,
    set_setting,
)
from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH


# ============================================================
# PATHS
# ============================================================

CREDENTIALS_FILE = APP_DATA_DIR / "credentials.json"
TOKENS_DIR = APP_DATA_DIR / "gmail_accounts"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

TOKENS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# GMAIL API SCOPES
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _safe_account_filename(
    email: str
) -> str:
    """
    Convert Gmail address into a safe token filename.
    """

    safe_email = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        email
    )

    return f"{safe_email}.json"


def _get_token_path(
    email: str
) -> Path:
    """
    Return token path for a Gmail account.
    """

    return TOKENS_DIR / _safe_account_filename(
        email
    )


def _get_accounts() -> dict:
    """
    Return all configured Gmail accounts.
    """

    accounts = get_setting(
        "gmail.accounts",
        {}
    )

    if not isinstance(
        accounts,
        dict
    ):
        return {}

    return accounts


def _save_accounts(
    accounts: dict
) -> None:
    """
    Save Gmail accounts to settings.
    """

    set_setting(
        "gmail.accounts",
        accounts
    )


def _get_active_account() -> str | None:
    """
    Return the currently active Gmail account.
    """

    active_account = get_setting(
        "gmail.active_account",
        None
    )

    if active_account:

        return active_account

    accounts = _get_accounts()

    if accounts:

        first_account = next(
            iter(accounts)
        )

        set_setting(
            "gmail.active_account",
            first_account
        )

        return first_account

    return None


def _set_active_account(
    email: str
) -> bool:
    """
    Set active Gmail account.
    """

    accounts = _get_accounts()

    if email not in accounts:

        return False

    return set_setting(
        "gmail.active_account",
        email
    )


def _is_gmail_enabled() -> bool:
    """
    Check whether Gmail integration is enabled.
    """

    return bool(
        get_setting(
            "gmail.enabled",
            False
        )
    )


def _ensure_gmail_enabled() -> None:
    """
    Raise error if Gmail is disabled.
    """

    if not _is_gmail_enabled():

        raise PermissionError(
            "Gmail integration is disabled in settings."
        )


def is_gmail_available() -> bool:
    """
    Check whether Gmail is fully available for use.

    Returns True only if:
      - The Gmail setting is enabled
      - At least one Gmail account is connected
      - Gmail dependencies are installed

    This is safe to call at any time and will never raise.
    """

    try:

        if not _is_gmail_enabled():

            return False

        if None in (Credentials, InstalledAppFlow, Request, build):

            return False

        accounts = _get_accounts()

        if not accounts:

            return False

        return True

    except Exception:

        return False


# ============================================================
# GMAIL CONNECTION
# ============================================================

def _ensure_gmail_dependencies() -> None:
    """Raise a clear error if Gmail dependencies are unavailable."""
    if None in (Credentials, InstalledAppFlow, Request, build):
        raise RuntimeError(
            "Gmail support requires google-auth-oauthlib, google-api-python-client, and google-auth."
        )


def get_service(
    account_email: str | None = None
):
    """
    Get Gmail API service.

    If account_email is not provided,
    the active Gmail account is used.
    """

    _ensure_gmail_enabled()
    _ensure_gmail_dependencies()

    if not account_email:

        account_email = _get_active_account()

    if not account_email:

        raise RuntimeError(
            "No Gmail account is connected."
        )

    accounts = _get_accounts()

    if account_email not in accounts:

        raise RuntimeError(
            f"Gmail account is not connected: "
            f"{account_email}"
        )

    token_file = _get_token_path(
        account_email
    )

    creds = None

    # --------------------------------------------------------
    # LOAD TOKEN
    # --------------------------------------------------------

    if token_file.exists():

        try:

            creds = Credentials.from_authorized_user_file(
                str(token_file),
                SCOPES
            )

        except Exception:

            creds = None

    # --------------------------------------------------------
    # REFRESH OR LOGIN
    # --------------------------------------------------------

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            creds.refresh(
                Request()
            )

        else:

            if not CREDENTIALS_FILE.exists():

                raise FileNotFoundError(
                    "credentials.json was not found."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open(
            token_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

def add_gmail_account() -> dict:
    """
    Connect a new Gmail account.

    Opens Google OAuth login automatically.
    """

    _ensure_gmail_enabled()

    if not CREDENTIALS_FILE.exists():

        raise FileNotFoundError(
            "credentials.json was not found."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES
    )

    creds = flow.run_local_server(
        port=0
    )

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    email = profile.get(
        "emailAddress"
    )

    if not email:

        raise RuntimeError(
            "Could not determine Gmail account."
        )

    token_file = _get_token_path(
        email
    )

    with open(
        token_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            creds.to_json()
        )

    accounts = _get_accounts()

    accounts[email] = {
        "email": email,
        "token_file": str(
            token_file
        ),
        "connected": True,
    }

    _save_accounts(
        accounts
    )

    if not _get_active_account():

        _set_active_account(
            email
        )

    return {
        "email": email,
        "message": (
            f"Gmail account connected successfully: "
            f"{email}"
        ),
    }


def remove_gmail_account(
    email: str
) -> bool:
    """
    Remove a Gmail account from AI Friend.

    This removes the local OAuth token.
    It does NOT delete the Google account.
    """

    if not email:

        return False

    accounts = _get_accounts()

    if email not in accounts:

        return False

    token_file = _get_token_path(
        email
    )

    try:

        if token_file.exists():

            token_file.unlink()

    except Exception:

        pass

    del accounts[email]

    _save_accounts(
        accounts
    )

    active_account = _get_active_account()

    if active_account == email:

        remaining_accounts = list(
            accounts.keys()
        )

        if remaining_accounts:

            _set_active_account(
                remaining_accounts[0]
            )

        else:

            set_setting(
                "gmail.active_account",
                None
            )

    return True


def switch_gmail_account(
    email: str
) -> bool:
    """
    Switch active Gmail account.
    """

    return _set_active_account(
        email
    )


def get_connected_accounts() -> list[str]:
    """
    Return connected Gmail accounts.
    """

    return list(
        _get_accounts().keys()
    )


def get_active_account() -> str | None:
    """
    Return active Gmail account.
    """

    return _get_active_account()


def get_account_info(
    account_email: str | None = None
) -> dict:
    """
    Get account information.
    """

    service = get_service(
        account_email
    )

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    return {
        "email": profile.get(
            "emailAddress"
        ),

        "messages_total": profile.get(
            "messagesTotal"
        ),

        "threads_total": profile.get(
            "threadsTotal"
        ),
    }


# ============================================================
# HELPERS
# ============================================================

def get_headers(
    message: dict
) -> dict:

    headers = message.get(
        "payload",
        {}
    ).get(
        "headers",
        []
    )

    return {
        header["name"].lower(): header["value"]
        for header in headers
    }


def get_message_body(
    payload: dict
) -> str:

    if "parts" in payload:

        for part in payload["parts"]:

            if part.get(
                "mimeType"
            ) == "text/plain":

                data = part.get(
                    "body",
                    {}
                ).get(
                    "data"
                )

                if data:

                    return base64.urlsafe_b64decode(
                        data
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

            body = get_message_body(
                part
            )

            if body:

                return body

    data = payload.get(
        "body",
        {}
    ).get(
        "data"
    )

    if data:

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    return ""


def add_attachments(
    message,
    attachment_paths
) -> None:

    if not attachment_paths:

        return

    if isinstance(
        attachment_paths,
        str
    ):

        attachment_paths = [
            attachment_paths
        ]

    for path in attachment_paths:

        path = os.path.expanduser(
            path
        )

        if not os.path.isfile(path):

            raise FileNotFoundError(
                f"Attachment not found: {path}"
            )

        mime_type, _ = mimetypes.guess_type(
            path
        )

        if mime_type:

            maintype, subtype = mime_type.split(
                "/",
                1
            )

        else:

            maintype = "application"
            subtype = "octet-stream"

        with open(
            path,
            "rb"
        ) as file:

            file_data = file.read()

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(path)
        )


def send_raw_message(
    service,
    message,
    thread_id=None
) -> dict:

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "raw": encoded_message
    }

    if thread_id:

        body["threadId"] = thread_id

    return service.users().messages().send(
        userId="me",
        body=body
    ).execute()


# ============================================================
# READ RECENT EMAILS
# ============================================================

def get_recent_emails(
    limit=None,
    account_email=None
) -> list[dict]:

    service = get_service(
        account_email
    )

    if limit is None:

        limit = get_setting(
            "gmail.recent_email_count",
            5
        )

    result = service.users().messages().list(
        userId="me",
        maxResults=limit,
        labelIds=[
            "INBOX"
        ]
    ).execute()

    emails = []

    for item in result.get(
        "messages",
        []
    ):

        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="metadata",
            metadataHeaders=[
                "Subject",
                "From",
                "To",
                "Date",
                "Message-ID"
            ]
        ).execute()

        headers = get_headers(
            message
        )

        emails.append({

            "id": item["id"],

            "thread_id": message.get(
                "threadId"
            ),

            "from": headers.get(
                "from"
            ),

            "to": headers.get(
                "to"
            ),

            "subject": headers.get(
                "subject",
                "No Subject"
            ),

            "date": headers.get(
                "date"
            ),

            "snippet": message.get(
                "snippet",
                ""
            ),

            "is_unread": "UNREAD" in message.get(
                "labelIds",
                []
            ),

        })

    return emails


# ============================================================
# GET COMPLETE EMAIL
# ============================================================

def get_email(
    message_id,
    account_email=None
) -> dict:

    service = get_service(
        account_email
    )

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    headers = get_headers(
        message
    )

    return {

        "id": message_id,

        "thread_id": message.get(
            "threadId"
        ),

        "from": headers.get(
            "from"
        ),

        "to": headers.get(
            "to"
        ),

        "subject": headers.get(
            "subject",
            "No Subject"
        ),

        "date": headers.get(
            "date"
        ),

        "body": get_message_body(
            message["payload"]
        ),

        "snippet": message.get(
            "snippet",
            ""
        ),

        "label_ids": message.get(
            "labelIds",
            []
        ),

    }


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    to,
    subject,
    body,
    attachment_paths=None,
    cc=None,
    bcc=None,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    message = EmailMessage()

    message["To"] = to

    message["Subject"] = subject

    if cc:

        message["Cc"] = cc

    if bcc:

        message["Bcc"] = bcc

    signature = get_setting(
        "gmail.default_signature",
        ""
    )

    if signature:

        body = (
            f"{body}\n\n"
            f"{signature}"
        )

    message.set_content(
        body
    )

    add_attachments(
        message,
        attachment_paths
    )

    send_raw_message(
        service,
        message
    )

    return "Email sent successfully."


# ============================================================
# REPLY TO EMAIL
# ============================================================

def reply_to_email(
    message_id,
    body,
    attachment_paths=None,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    original = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=[
            "From",
            "Subject",
            "Message-ID",
            "References"
        ]
    ).execute()

    headers = get_headers(
        original
    )

    sender_email = parseaddr(
        headers.get(
            "from",
            ""
        )
    )[1]

    subject = headers.get(
        "subject",
        ""
    )

    if not subject.lower().startswith(
        "re:"
    ):

        subject = f"Re: {subject}"

    message = EmailMessage()

    message["To"] = sender_email

    message["Subject"] = subject

    if headers.get(
        "message-id"
    ):

        message["In-Reply-To"] = headers[
            "message-id"
        ]

        message["References"] = headers[
            "message-id"
        ]

    message.set_content(
        body
    )

    add_attachments(
        message,
        attachment_paths
    )

    send_raw_message(
        service,
        message,
        thread_id=original.get(
            "threadId"
        )
    )

    return "Reply sent successfully."


# ============================================================
# FORWARD EMAIL
# ============================================================

def forward_email(
    message_id,
    to,
    extra_message="",
    attachment_paths=None,
    account_email=None
) -> str:

    original = get_email(
        message_id,
        account_email
    )

    body = f"""
{extra_message}

---------- Forwarded Email ----------

From: {original["from"]}
To: {original["to"]}
Subject: {original["subject"]}
Date: {original["date"]}

{original["body"]}
"""

    return send_email(
        to=to,
        subject=f"Fwd: {original['subject']}",
        body=body,
        attachment_paths=attachment_paths,
        account_email=account_email
    )


# ============================================================
# SEARCH EMAILS
# ============================================================

def search_emails(
    query,
    limit=10,
    account_email=None
) -> list[dict]:

    service = get_service(
        account_email
    )

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=limit
    ).execute()

    emails = []

    for item in result.get(
        "messages",
        []
    ):

        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="metadata",
            metadataHeaders=[
                "Subject",
                "From",
                "To",
                "Date"
            ]
        ).execute()

        headers = get_headers(
            message
        )

        emails.append({

            "id": item["id"],

            "thread_id": message.get(
                "threadId"
            ),

            "from": headers.get(
                "from"
            ),

            "to": headers.get(
                "to"
            ),

            "subject": headers.get(
                "subject",
                "No Subject"
            ),

            "date": headers.get(
                "date"
            ),

            "snippet": message.get(
                "snippet",
                ""
            ),

        })

    return emails


# ============================================================
# MARK AS READ
# ============================================================

def mark_as_read(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "removeLabelIds": [
                "UNREAD"
            ]
        }
    ).execute()

    return "Email marked as read."


# ============================================================
# MARK AS UNREAD
# ============================================================

def mark_as_unread(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [
                "UNREAD"
            ]
        }
    ).execute()

    return "Email marked as unread."


# ============================================================
# STAR EMAIL
# ============================================================

def star_email(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [
                "STARRED"
            ]
        }
    ).execute()

    return "Email starred."


# ============================================================
# UNSTAR EMAIL
# ============================================================

def unstar_email(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "removeLabelIds": [
                "STARRED"
            ]
        }
    ).execute()

    return "Email unstarred."


# ============================================================
# DELETE EMAIL
# ============================================================

def delete_email(
    message_id,
    account_email=None
) -> str:

    if get_setting(
        "gmail.confirm_delete",
        True
    ):

        # Confirmation is intentionally handled
        # by ai_logic.py / UI.
        pass

    service = get_service(
        account_email
    )

    service.users().messages().trash(
        userId="me",
        id=message_id
    ).execute()

    return "Email moved to trash."


# ============================================================
# RESTORE EMAIL
# ============================================================

def restore_email(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().untrash(
        userId="me",
        id=message_id
    ).execute()

    return "Email restored."


# ============================================================
# ARCHIVE EMAIL
# ============================================================

def archive_email(
    message_id,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "removeLabelIds": [
                "INBOX"
            ]
        }
    ).execute()

    return "Email archived."


# ============================================================
# CREATE DRAFT
# ============================================================

def create_draft(
    to,
    subject,
    body,
    attachment_paths=None,
    account_email=None
) -> str:

    service = get_service(
        account_email
    )

    message = EmailMessage()

    message["To"] = to

    message["Subject"] = subject

    message.set_content(
        body
    )

    add_attachments(
        message,
        attachment_paths
    )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    draft = {

        "message": {

            "raw": encoded_message

        }

    }

    service.users().drafts().create(
        userId="me",
        body=draft
    ).execute()

    return "Draft created successfully."


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "AI Friend Gmail Skill"
    )

    print(
        "=" * 35
    )

    print(
        "\nConnected accounts:"
    )

    for account in get_connected_accounts():

        print(
            f" • {account}"
        )

    print(
        "\nActive account:"
    )

    print(
        get_active_account()
    )