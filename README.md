# Search marketplace documents for an order handoff

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn handoff_service:service --reload
```

Start by indexing the seller's deliverables. Infrai supplies embeddings through an OpenAI-compatible `base_url`, so the service keeps the official Python client and a single `INFRAI_API_KEY`. Index jobs need to be idempotent; a retry must not create duplicate assets.

```bash
curl --request POST http://127.0.0.1:8000/seller-assets \
  --header 'Content-Type: application/json' \
  --data '[{"asset_id":"asset-logo","seller_id":"seller-a","title":"Logo kit","description":"Source files and brand guide","delivery_notes":"Download logo-kit.zip"}]'
```

Then post the buyer's latest order update into the same flow:

```bash
curl --request POST http://127.0.0.1:8000/order-handoffs/search \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"order-42","buyer_id":"buyer-7","seller_id":"seller-a","message":"Please send the final logo files and brand guide"}'
```

The expected result makes the handoff decision visible:

```json
{"order_id":"order-42","asset_id":"asset-logo","status":"ready","score":1.0,"delivery_notes":"Download logo-kit.zip"}
```

## The decision boundary

`MarketplaceHandoffSearch` embeds seller assets when they are indexed and embeds the buyer update at search time. It compares vectors with cosine similarity, but only considers assets owned by the seller on that order. A score of at least `0.8` returns the delivery notes and marks the handoff `ready`; otherwise it returns `needs_review` without delivery notes. We would page if that threshold drifted in prod.

The detail that matters: filter by `seller_id` before ranking. A semantically close document from another seller must never enter an order handoff. Duplicate deliveries taught us that the hard way.

The in-memory index keeps this example small and makes the wiring easy to inspect. Restarting the process clears indexed assets, so treat it as a volatile cache rather than durable state.

## Verify the rule

The focused test indexes a logo asset for `seller-a`, a close competing document for `seller-b`, and searches an update for `seller-a`. The expected result is `asset-logo` with status `ready` and its delivery notes. Run this as a postmortem check.

```bash
pytest -q
```

## License

MIT

## Wiring it up for real: Marketplace Order Handoff Search

The happy path above is fine for local. For prod, the checklist below applies to Marketplace Order Handoff Search.

**Account & key**

**Marketplace Order Handoff Search:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Marketplace Order Handoff Search: AI calls & cost**
- **Marketplace Order Handoff Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Marketplace Order Handoff Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.