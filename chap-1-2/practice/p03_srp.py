import hashlib
from typing import Protocol


# FIX 1: The original UserManager is gone. It was the problem, not part of the solution.
# FIX 2: Three responsibilities = three classes. Auth, Email, Logging.
# FIX 3: Each class can be described in one sentence with zero "and"s.


# Responsibility 1: auth logic and hashing.
# One reason to change: auth rules change (e.g. switch to bcrypt, add 2FA).
class AuthService:
    def __init__(self, db_conn):
        self.db = db_conn

    def register(self, email: str, password: str) -> None:
        hashed = self._hash(password)
        self.db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed)
        )

    def login(self, email: str, password: str) -> bool:
        row = self.db.execute("SELECT password FROM users WHERE email=?", (email,))
        return row and row[0] == self._hash(password)

    def _hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


# Protocol: defines the shape any notifier must satisfy.
# notify() takes only message: str so all notifiers have the same signature.
class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


# Responsibility 2: sending emails.
# One reason to change: email provider changes (Sendgrid, SES, etc).
# FIX 3: notify() now matches the Protocol signature exactly (message: str only).
# FIX 4: recipient is stored at construction time, not passed into notify().
# FIX 5: the [LOG] print that was here does not belong. Logging is a separate responsibility.
class EmailNotifier:
    def __init__(self, smtp_client, recipient: str):
        self.smtp = smtp_client
        self.recipient = recipient

    def notify(self, message: str) -> None:
        self.smtp.send(
            to=self.recipient,
            subject="Welcome!",
            body=message
        )


# Responsibility 3: logging events.
# One reason to change: log format or destination changes (file, Datadog, etc).
# FIX 6: logging is now its own class, not a stray print() buried in another class.
class EventLogger:
    def notify(self, message: str) -> None:
        print(f"[LOG] {message}")


# --- How all three work together ---
# The caller wires them up and passes them into AuthService as needed.
# AuthService itself knows nothing about email or logging.

# db_conn = ...
# smtp_client = ...
# auth = AuthService(db_conn)
# mailer = EmailNotifier(smtp_client, recipient="user@example.com")
# logger = EventLogger()
#
# auth.register("user@example.com", "password123")
# mailer.notify("Your account has been created.")
# logger.notify("User registered: user@example.com")