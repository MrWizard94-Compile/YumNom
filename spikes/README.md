# YumNom De-Risking Spikes

Four spikes that must produce results **before app code is written** (per the approved spec review). Each has a binary outcome that either confirms the v1.1 architecture or forces a revision.

| # | Spike | Outcome gate | Needs |
|---|-------|--------------|-------|
| 1 | [Walmart affiliate application](1-walmart-affiliate-application.md) | Affiliate + API access granted; storeId/rate-raise requests filed | Your action (longest lead time — start now) |
| 2 | [Cart deep-link test](2-cart-deeplink-test.md) | Multi-item grocery link opens a populated cart on iOS & Android AND attribution appears in the dashboard | Affiliate account from spike 1, two phones |
| 3 | [SKU matching prototype](3-sku-matching/) | ≥90% of ingredients across 10 recipes match a purchasable SKU | walmart.io API credentials from spike 1 |
| 4 | [Grok plan generation prototype](4-grok-plan-generation/) | Valid JSON plan, all constraints honored, first-day content < 5 s / full plan < 30 s | xAI API key (console.x.ai) |

Python spikes (3 and 4):

```
pip install -r requirements.txt
python 3-sku-matching/match_skus.py
python 4-grok-plan-generation/generate_plan.py
```

Both scripts print exactly which environment variables they need if credentials are missing.
