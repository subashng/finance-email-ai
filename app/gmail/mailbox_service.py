from typing import Any

from app.gmail.gmail_client import (
    get_gmail_message,
    get_gmail_service,
)


INBOX_QUERY = "in:inbox -from:me"


def list_business_inbox_messages(
    max_messages: int | None = None,
) -> list[dict[str, Any]]:
    """
    Return real incoming inbox messages.

    Business definition:
    - Message is in INBOX.
    - Message is not sent by the authenticated account.

    Development/self-send test emails are therefore excluded.
    """

    service = get_gmail_service()

    messages: list[dict[str, Any]] = []

    page_token: str | None = None

    while True:

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                q=INBOX_QUERY,
                maxResults=100,
                pageToken=page_token,
            )
            .execute()
        )

        for message in response.get(
            "messages",
            [],
        ):

            message_id = message.get(
                "id"
            )

            if not message_id:
                continue

            messages.append(
                get_gmail_message(
                    message_id
                )
            )

            if (
                max_messages is not None
                and len(messages)
                >= max_messages
            ):

                return messages

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return messages


def get_business_mailbox_summary(
    recent_limit: int = 25,
) -> dict[str, Any]:
    """
    Return real business mailbox information.

    The full inbox is used for the received count.
    Only the newest messages are returned for dashboard display.
    """

    messages = list_business_inbox_messages()

    messages.sort(
        key=lambda item: item.get(
            "date",
            "",
        ),
        reverse=True,
    )

    return {
        "status": "CONNECTED",
        "emails_received": len(messages),
        "recent_messages": messages[
            :recent_limit
        ],
    }


if __name__ == "__main__":

    summary = get_business_mailbox_summary()

    print(
        "BUSINESS EMAILS RECEIVED:",
        summary.get(
            "emails_received"
        ),
    )

    for message in summary.get(
        "recent_messages",
        [],
    ):

        print(
            message.get("message_id"),
            "|",
            message.get("sender_email"),
            "|",
            message.get("subject"),
        )