import base64
import os
from email.mime.text import MIMEText
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json",
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json",
)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


# ============================================================
# AUTHENTICATION
# ============================================================

def get_gmail_service():
    """
    Authenticate with Gmail using OAuth 2.0.

    V1 permissions:
    - gmail.readonly
    - gmail.send

    This module does not:
    - delete messages
    - modify labels
    - mark messages as read
    """

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            "credentials.json was not found at: "
            f"{CREDENTIALS_FILE}"
        )

    credentials: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        credentials = (
            Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES,
            )
        )

    if credentials is None or not credentials.valid:

        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(
                Request()
            )

        else:
            flow = (
                InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES,
                )
            )

            credentials = flow.run_local_server(
                port=0
            )

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8",
        ) as token_file:
            token_file.write(
                credentials.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )


# ============================================================
# CONNECTION TEST
# ============================================================

def test_gmail_connection() -> dict[str, Any]:
    """
    Verify the authenticated Gmail connection.
    """

    service = get_gmail_service()

    profile = (
        service.users()
        .getProfile(
            userId="me"
        )
        .execute()
    )

    return {
        "status": "CONNECTED",
        "email_address": profile.get(
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
# HEADER HELPER
# ============================================================

def _get_header(
    headers: list[dict[str, Any]],
    name: str,
) -> str:
    """
    Return one Gmail message header value.
    """

    target = name.lower()

    for header in headers:

        header_name = str(
            header.get(
                "name",
                "",
            )
        ).lower()

        if header_name == target:
            return str(
                header.get(
                    "value",
                    "",
                )
            )

    return ""


# ============================================================
# BODY DECODER
# ============================================================

def _decode_body_data(
    data: str | None,
) -> str:
    """
    Decode Gmail URL-safe base64 body data.
    """

    if not data:
        return ""

    try:

        decoded = base64.urlsafe_b64decode(
            data + "=" * (
                -len(data) % 4
            )
        )

        return decoded.decode(
            "utf-8",
            errors="replace",
        )

    except (
        ValueError,
        UnicodeDecodeError,
    ):
        return ""


# ============================================================
# MIME BODY EXTRACTION
# ============================================================

def _extract_text_from_part(
    part: dict[str, Any],
) -> str:
    """
    Prefer text/plain, then search nested parts,
    then use text/html as fallback.
    """

    mime_type = str(
        part.get(
            "mimeType",
            "",
        )
    ).lower()

    body = part.get(
        "body",
        {}
    )

    data = body.get(
        "data"
    )

    if (
        mime_type == "text/plain"
        and data
    ):
        return _decode_body_data(
            data
        )

    for child in part.get(
        "parts",
        [],
    ):

        text = _extract_text_from_part(
            child
        )

        if text.strip():
            return text

    if (
        mime_type == "text/html"
        and data
    ):
        return _decode_body_data(
            data
        )

    return ""


# ============================================================
# LIST INBOX
# ============================================================

def list_inbox_messages(
    max_results: int = 10,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return inbox message IDs and thread IDs.

    Read-only.
    """

    if max_results < 1:
        max_results = 1

    if max_results > 100:
        max_results = 100

    service = get_gmail_service()

    request = (
        service.users()
        .messages()
        .list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results,
            q=query,
        )
    )

    result = request.execute()

    return [
        {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
        }
        for message in result.get(
            "messages",
            [],
        )
    ]


# ============================================================
# GET ONE MESSAGE
# ============================================================

def get_gmail_message(
    message_id: str,
) -> dict[str, Any]:
    """
    Retrieve one Gmail message in full format.

    Important reply metadata is also returned:
    - Gmail message ID
    - Gmail thread ID
    - RFC Message-ID header
    - References header
    """

    if not message_id:
        raise ValueError(
            "message_id is required."
        )

    service = get_gmail_service()

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    sender_email = _get_header(
        headers,
        "From",
    )

    to_email = _get_header(
        headers,
        "To",
    )

    subject = _get_header(
        headers,
        "Subject",
    )

    date_header = _get_header(
        headers,
        "Date",
    )

    message_id_header = _get_header(
        headers,
        "Message-ID",
    )

    references_header = _get_header(
        headers,
        "References",
    )

    in_reply_to_header = _get_header(
        headers,
        "In-Reply-To",
    )

    message_body = _extract_text_from_part(
        payload
    )

    if not message_body.strip():
        message_body = str(
            message.get(
                "snippet",
                "",
            )
        )

    return {
        "message_id": message.get(
            "id"
        ),
        "thread_id": message.get(
            "threadId"
        ),
        "rfc_message_id": message_id_header,
        "references": references_header,
        "in_reply_to": in_reply_to_header,
        "sender_email": sender_email,
        "to_email": to_email,
        "subject": subject,
        "date": date_header,
        "email_body": message_body,
        "snippet": message.get(
            "snippet",
            "",
        ),
        "label_ids": message.get(
            "labelIds",
            [],
        ),
    }


# ============================================================
# LATEST MESSAGE
# ============================================================

def get_latest_inbox_message() -> dict[str, Any] | None:
    """
    Retrieve the newest inbox message.
    """

    messages = list_inbox_messages(
        max_results=1
    )

    if not messages:
        return None

    message_id = messages[0].get(
        "id"
    )

    if not message_id:
        return None

    return get_gmail_message(
        message_id
    )


# ============================================================
# BUILD REPLY
# ============================================================

def build_reply_message(
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> dict[str, Any]:
    """
    Build a Gmail reply message.

    For thread replies, we preserve:
    - Subject
    - In-Reply-To
    - References
    - threadId
    """

    if not to_email:
        raise ValueError(
            "Recipient email is required."
        )

    if not subject:
        raise ValueError(
            "Subject is required."
        )

    if not body or not body.strip():
        raise ValueError(
            "Email body is required."
        )

    reply_subject = subject.strip()

    if not reply_subject.lower().startswith(
        "re:"
    ):
        reply_subject = (
            f"Re: {reply_subject}"
        )

    message = MIMEText(
        body,
        _subtype="plain",
        _charset="utf-8",
    )

    message["To"] = to_email
    message["Subject"] = reply_subject

    if in_reply_to:
        message["In-Reply-To"] = in_reply_to

    if references:
        message["References"] = references

    elif in_reply_to:
        message["References"] = in_reply_to

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode(
        "utf-8"
    )

    result = {
        "raw": raw,
        "to_email": to_email,
        "subject": reply_subject,
    }

    if thread_id:
        result["threadId"] = thread_id

    return result


# ============================================================
# SEND GMAIL REPLY
# ============================================================

def send_gmail_message(
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> dict[str, Any]:
    """
    Send an email through Gmail.

    IMPORTANT:
    The caller must enforce the approved Finance Email workflow
    before calling this function.
    """

    service = get_gmail_service()

    message = build_reply_message(
        to_email=to_email,
        subject=subject,
        body=body,
        thread_id=thread_id,
        in_reply_to=in_reply_to,
        references=references,
    )

    request_body = {
        "raw": message["raw"],
    }

    if thread_id:
        request_body["threadId"] = thread_id

    sent_message = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=request_body,
        )
        .execute()
    )

    return {
        "status": "SENT",
        "message_id": sent_message.get(
            "id"
        ),
        "thread_id": sent_message.get(
            "threadId"
        ),
        "to_email": to_email,
        "subject": message["subject"],
    }


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Gmail client loaded successfully."
    )