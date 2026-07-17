# Spike 1: Walmart Affiliate + API Access Application

**Why first:** every other spike and the app itself depend on this, and approval lead times are unknown. File everything today; the rest can proceed in parallel.

## Checklist

1. **Join the Walmart affiliate program** (runs on the Impact network): https://affiliates.walmart.com/register
   - You'll need a website or app property to list. A simple landing page describing YumNom is sufficient.
2. **Register on walmart.io** and apply for the **Affiliate / Content Provider API**: https://www.walmart.io/
   - Generate an RSA key pair during onboarding; upload the public key. Keep the private key for API signing (spike 3 uses it).
   - Note your **Consumer ID** and **Key Version**.
3. **Request storeId lookup approval** (store-level price/availability requires extra business-team approval):
   - Email affilops@wal-mart.com describing the use case (below) and requesting `storeId` access on Product Lookup.
4. **Request a rate-limit raise** in the same email: default is 5,000 calls/day; explain the shared-cache architecture and projected volume.
5. **Confirm the use case is within terms**: the API license reads "solely for the purpose of advertising Walmart.com products online." Ask explicitly whether a free meal-planning app that links every product to Walmart.com/Walmart app checkout qualifies.

## Use-case blurb (paste into the email)

> YumNom is a free mobile app that builds weekly meal plans for working parents and converts every plan into a Walmart shopping list with affiliate add-to-cart links. All product discovery routes users to Walmart.com / the Walmart app for purchase, and the app promotes Walmart+ sign-ups contextually. We request: (a) Product Lookup access with storeId so plans reflect the user's actual store, and (b) a daily rate limit above the 5,000-call default — we cache product data server-side per store/ingredient, so calls scale with regions, not users.

## Outcome to record

- [ ] Affiliate account approved (Impact)
- [ ] walmart.io API keys issued (Consumer ID + private key → spike 3)
- [ ] storeId approval: granted / denied / pending — **if denied, v1 ships ZIP-baseline only (already the spec's plan)**
- [ ] Rate-limit raise: granted amount ________
- [ ] Use-case confirmation received in writing
