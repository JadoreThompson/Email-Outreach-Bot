from pydantic import BaseModel
from typing import Optional


class Email(BaseModel):
    email_sender: str
    email_password: str
    email_recipient: str
    body: str
    subject: Optional[str] = None
