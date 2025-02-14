from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import MAX_INPUT_LENGTH

SummaryLength = Literal["short", "medium", "long"]


class SummarizeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(
        min_length=1,
        max_length=MAX_INPUT_LENGTH,
        description=f"Text to summarize, up to {MAX_INPUT_LENGTH} characters.",
        examples=["A long article or paragraph..."],
    )
    length: SummaryLength = Field(
        default="medium",
        description="short: 1-2 sentences, medium: 3-5 sentences, long: 5-8 sentences.",
    )


class SummarizeResponse(BaseModel):
    summary: str
    length: SummaryLength
