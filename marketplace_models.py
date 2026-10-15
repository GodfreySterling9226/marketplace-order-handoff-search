from typing import Literal

from pydantic import BaseModel, Field


class SellerAsset(BaseModel):
    asset_id: str = Field(min_length=1)
    seller_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    delivery_notes: str = Field(min_length=1)

    def search_text(self) -> str:
        return f"{self.title}\n{self.description}\nDelivery: {self.delivery_notes}"


class BuyerUpdate(BaseModel):
    order_id: str = Field(min_length=1)
    buyer_id: str = Field(min_length=1)
    seller_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class HandoffMatch(BaseModel):
    order_id: str
    asset_id: str | None
    status: Literal["ready", "needs_review"]
    score: float
    delivery_notes: str | None

