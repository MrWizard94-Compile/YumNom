# Spike 2: Cart Deep-Link + Attribution Test

**Question being answered:** does a hand-built multi-item grocery add-to-cart link (a) actually populate a cart on a phone, and (b) credit the affiliate account — including when the Walmart *app* intercepts the link?

**Needs:** approved affiliate account (spike 1), one iPhone + one Android phone, Walmart app installed on at least one of them.

## Procedure

1. Pick 3 grocery item IDs from walmart.com product pages (the number in the URL, e.g. `.../ip/Great-Value-All-Purpose-Flour-5LB/10534869` → `10534869`). Use ordinary groceries: flour, eggs, chicken breast.
2. Build the links (documented forms — verify current syntax at https://walmart.io/docs/affiliates/v1/gm-add-to-cart):
   - Single item: `https://affil.walmart.com/cart/buynow?items=<id>`
   - Multi-item with quantities: `https://affil.walmart.com/cart/addToCart?items=<id1>|<qty1>,<id2>|<qty2>,<id3>|<qty3>`
   - Then wrap with your Impact tracking link so the click is attributed.
3. Test each matrix cell and record what happens:

| Scenario | Cart populated? | Attribution in dashboard? |
|---|---|---|
| iOS Safari, no Walmart app | | |
| iOS, Walmart app installed (link opens app) | | |
| Android Chrome, no app | | |
| Android, Walmart app installed | | |
| User not logged in to Walmart | | |
4. Complete at least one real checkout and confirm the transaction appears in the Impact dashboard (may take up to 72 h).

## Outcome gate

- **Pass:** multi-item grocery links populate carts on both platforms AND at least the browser paths attribute.
- **Partial:** links work but app-intercepted paths don't attribute → spec's Walmart+-first revenue model carries more weight; consider forcing browser checkout for the affiliate path.
- **Fail:** multi-item grocery links rejected → fall back to per-item links or copyable-list-first UX; revise SPEC §14 before building.
