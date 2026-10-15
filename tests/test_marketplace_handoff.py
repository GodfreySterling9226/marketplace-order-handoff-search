from marketplace_handoff import MarketplaceHandoffSearch
from marketplace_models import BuyerUpdate, SellerAsset


def test_only_same_seller_asset_can_make_handoff_ready() -> None:
    vectors = {
        "Logo kit\nSource files and brand guide\nDelivery: Download logo-kit.zip": [1.0, 0.0],
        "Podcast edit\nCleaned audio and show notes\nDelivery: Download episode.wav": [0.0, 1.0],
        "Please send the final logo files and brand guide": [1.0, 0.0],
    }

    def deterministic_embed(texts: list[str]) -> list[list[float]]:
        return [vectors[text] for text in texts]

    search = MarketplaceHandoffSearch(deterministic_embed, ready_threshold=0.8)
    search.replace_assets(
        [
            SellerAsset(
                asset_id="asset-logo",
                seller_id="seller-a",
                title="Logo kit",
                description="Source files and brand guide",
                delivery_notes="Download logo-kit.zip",
            ),
            SellerAsset(
                asset_id="asset-audio",
                seller_id="seller-b",
                title="Podcast edit",
                description="Cleaned audio and show notes",
                delivery_notes="Download episode.wav",
            ),
        ]
    )

    match = search.find_handoff(
        BuyerUpdate(
            order_id="order-42",
            buyer_id="buyer-7",
            seller_id="seller-a",
            message="Please send the final logo files and brand guide",
        )
    )

    assert match.status == "ready"
    assert match.asset_id == "asset-logo"
    assert match.delivery_notes == "Download logo-kit.zip"

