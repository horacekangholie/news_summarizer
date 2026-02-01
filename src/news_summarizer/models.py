from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NewsItem(BaseModel):
    model_config = ConfigDict(validate_by_name=True, populate_by_name=True)

    Title: str = Field(..., min_length=1)
    News_Summary: str = Field(..., min_length=1, alias="News Summary")
