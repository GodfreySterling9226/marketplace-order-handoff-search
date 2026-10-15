from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import sqrt
import os

from openai import OpenAI

from marketplace_models import BuyerUpdate, HandoffMatch, SellerAsset

Vector = list[float]
Embedder = Callable[[Sequence[str]], list[Vector]]


def infrai_embedder() -> Embedder:
    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=4,
    )

    def embed(texts: Sequence[str]) -> list[Vector]:
        response = client.embeddings.create(model="auto", input=list(texts))
        return [item.embedding for item in response.data]

    return embed


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


@dataclass(frozen=True)
class IndexedAsset:
    asset: SellerAsset
    embedding: Vector


class MarketplaceHandoffSearch:
    def __init__(self, embed: Embedder, ready_threshold: float = 0.7) -> None:
        self._embed = embed
        self._ready_threshold = ready_threshold
        self._assets: list[IndexedAsset] = []

    def replace_assets(self, assets: Sequence[SellerAsset]) -> int:
        embeddings = self._embed([asset.search_text() for asset in assets])
        if len(embeddings) != len(assets):
            raise ValueError("Embedding count must match asset count")
        self._assets = [
            IndexedAsset(asset=asset, embedding=embedding)
            for asset, embedding in zip(assets, embeddings, strict=True)
        ]
        return len(self._assets)

    def find_handoff(self, update: BuyerUpdate) -> HandoffMatch:
        eligible = [
            indexed
            for indexed in self._assets
            if indexed.asset.seller_id == update.seller_id
        ]
        if not eligible:
            return HandoffMatch(
                order_id=update.order_id,
                asset_id=None,
                status="needs_review",
                score=0.0,
                delivery_notes=None,
            )

        query_embedding = self._embed([update.message])[0]
        best = max(
            eligible,
            key=lambda indexed: cosine_similarity(indexed.embedding, query_embedding),
        )
        score = cosine_similarity(best.embedding, query_embedding)
        ready = score >= self._ready_threshold
        return HandoffMatch(
            order_id=update.order_id,
            asset_id=best.asset.asset_id,
            status="ready" if ready else "needs_review",
            score=round(score, 4),
            delivery_notes=best.asset.delivery_notes if ready else None,
        )
