# P07 - Notification Service
#
# Protocol vs ABC choice:
# Protocol is the right pick here because:
#   1. Channels could come from external libraries we do not control.
#      With ABC, every channel must explicitly inherit from our base class.
#      With Protocol, any class that has send(message: str) works automatically.
#   2. Fake test channels need zero imports from production code.
#   3. We are defining what NotificationService NEEDS, not what channels ARE.
#      That is a Protocol's job, not ABC's.
#
# Patterns used: Strategy (each channel is a strategy for sending), DIP, OCP, SRP.

from typing import Protocol
from dataclasses import dataclass


# ------------------------------------------------------------------
# Abstraction: the only thing NotificationService knows about channels
# ------------------------------------------------------------------

class NotificationChannel(Protocol):
    def send(self, message: str) -> None: ...


# ------------------------------------------------------------------
# Configs: pure data, no behavior
# Each config only holds what its channel needs. No shared fat config.
# ------------------------------------------------------------------

@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str


@dataclass
class SMSConfig:
    api_key: str
    sender_number: str


@dataclass
class WhatsAppConfig:
    api_key: str
    phone_number_id: str


# ------------------------------------------------------------------
# Concrete channels: one class, one responsibility, one reason to change
# ------------------------------------------------------------------

class EmailChannel:
    """Owns: sending messages via SMTP email.
    Reason to change: email provider changes (Gmail -> SES -> Sendgrid)."""

    def __init__(self, config: EmailConfig):
        self._config = config

    def send(self, message: str) -> None:
        print(f"[EMAIL] {self._config.host}:{self._config.port} -> {message}")


class SMSChannel:
    """Owns: sending messages via SMS API.
    Reason to change: SMS provider changes (Twilio -> Vonage -> local gateway)."""

    def __init__(self, config: SMSConfig):
        self._config = config

    def send(self, message: str) -> None:
        print(f"[SMS] from {self._config.sender_number} -> {message}")


class WhatsAppChannel:
    """Owns: sending messages via WhatsApp Business API.
    Reason to change: WhatsApp API version or credentials change."""

    def __init__(self, config: WhatsAppConfig):
        self._config = config

    def send(self, message: str) -> None:
        print(f"[WHATSAPP] phone_id={self._config.phone_number_id} -> {message}")


# ------------------------------------------------------------------
# Service: purely fans out a message to all channels. Nothing else.
# ------------------------------------------------------------------

class NotificationService:
    """Owns: fanning out a message to all registered channels.
    Reason to change: fan-out strategy changes (retry logic, parallel sending).

    This class knows nothing about how any channel works.
    No if/elif. No isinstance. It just iterates and delegates.
    OCP: adding SlackChannel requires zero edits here."""

    def __init__(self, channels: list[NotificationChannel]):
        self._channels = channels

    def notify(self, message: str) -> None:
        for channel in self._channels:
            channel.send(message)

    def add_channel(self, channel: NotificationChannel) -> None:
        self._channels.append(channel)


# ------------------------------------------------------------------
# Fake channel for testing: no real network calls, no smtp, no API keys
# ------------------------------------------------------------------

class FakeChannel:
    """Satisfies NotificationChannel Protocol with zero production imports.
    Use this in tests to verify notify() was called with the right message."""

    def __init__(self):
        self.sent: list[str] = []

    def send(self, message: str) -> None:
        self.sent.append(message)


# ------------------------------------------------------------------
# Composition root: the only place that knows about concrete classes
# ------------------------------------------------------------------

if __name__ == "__main__":
    email = EmailChannel(EmailConfig("smtp.gmail.com", 587, "user@gmail.com", "pass"))
    sms = SMSChannel(SMSConfig("sms_api_key_123", "+923001234567"))
    whatsapp = WhatsAppChannel(WhatsAppConfig("wa_key_456", "phone_id_001"))

    service = NotificationService([email, sms, whatsapp])
    service.notify("Your order #1234 has been placed!")

    print()

    # Adding a new channel: one new class, zero edits to NotificationService
    # class SlackChannel:
    #     def __init__(self, webhook_url: str): ...
    #     def send(self, message: str) -> None: ...
    # service.add_channel(SlackChannel("https://hooks.slack.com/..."))

    # Testing without real channels
    fake = FakeChannel()
    test_service = NotificationService([fake])
    test_service.notify("test message")
    assert fake.sent == ["test message"]
    print("Test passed.")