from fastapi import FastAPI

from marketplace_handoff import MarketplaceHandoffSearch, infrai_embedder
from marketplace_models import BuyerUpdate, HandoffMatch, SellerAsset

service = FastAPI(title="Marketplace handoff search")
search = MarketplaceHandoffSearch(infrai_embedder())


@service.post("/seller-assets")
def index_seller_assets(assets: list[SellerAsset]) -> dict[str, int]:
    return {"indexed": search.replace_assets(assets)}


@service.post("/order-handoffs/search", response_model=HandoffMatch)
def search_order_handoff(update: BuyerUpdate) -> HandoffMatch:
    return search.find_handoff(update)

