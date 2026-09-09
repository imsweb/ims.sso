from dataclasses import dataclass


@dataclass
class BaseIdp:
    name: str = ""
    description: str | None = None
    registration: str | None = None
    logout: str | None = None
    login: str | None = None
    display_login: bool = True
    update_email: bool = True


@dataclass
class Unlinked(BaseIdp):
    name: str = "Not Linked"
