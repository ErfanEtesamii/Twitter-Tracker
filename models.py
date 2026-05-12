from dataclasses import dataclass, field
from typing import List

@dataclass
class Project:
    name: str
    enabled: bool = True
    source_sheet_id: str = ""
    source_ws_title: str = ""
    sent_sheet_id: str = ""
    sent_ws_title: str = "sent_all"
    regexes: List[str] = field(default_factory=list)
    chat_ids: List[str] = field(default_factory=list)
    max_age_seconds: int = 10800

@dataclass
class PendingAction:
    action: str
    project: str = ""
    extra: dict = field(default_factory=dict)