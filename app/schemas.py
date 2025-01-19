from typing import Literal

from pydantic import BaseModel

SummaryLength = Literal["short", "medium", "long"]


class SummarizeRequest(BaseModel):
    text: str
    length: SummaryLength = "medium"


class SummarizeResponse(BaseModel):
    summary: str
    length: SummaryLength
