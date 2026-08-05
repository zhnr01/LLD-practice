from typing import Protocol


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...

class EmailNotifier:
    def notify(self, message: str) -> None:
        print(f"Email notification sent: {message}")

class SMSNotifier:
    def notify(self, message: str) -> None:
        print(f"SMS notification sent: {message}")

class PushNotifier:
    def notify(self, message: str) -> None:
        print(f"Push notification sent: {message}")


def notify(notifier: Notifier, message: str):
    notifier.notify(message)


email_notifier = EmailNotifier()
sms_notifier = SMSNotifier()
push_notifier = PushNotifier()


notify(email_notifier, "Welcome!")
notify(sms_notifier, "Hello!")