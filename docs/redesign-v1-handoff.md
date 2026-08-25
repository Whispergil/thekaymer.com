# Kaymer V1 Redesign — Verified Research Handoff

**Status:** Research/discovery complete. **No site code has been written yet.**
**Branch:** `redesign/v1-ivory-gold` (branched from `main` @ `7c881b7`)
**Purpose:** Hand off verified facts to a Claude Code Cloud session so the redesign
implementation does not have to re-derive them — and, more importantly, so it does
not guess at anything that was verified here.

Everything below was confirmed against a primary source (GitHub API, the iTunes
Lookup API, or the live findryapp.com pages). Anything that could **not** be
verified is listed explicitly under "Blockers and missing assets" and must not be
invented.

---

## 1. Repository baseline

| Item | Value |
|---|---|
| Repo | `https://github.com/Whispergil/thekaymer.com.git` (public) |
| Base commit | `7c881b7` on `main`, working tree clean, fully pushed |
| Live URL | `https://whispergil.github.io/thekaymer.com/` |
| Pages source | branch `main`, path `/`, `build_type: legacy` (Jekyll), `cname: null` |
| Build system | none — dependency-free static HTML/CSS/JS |

**Subpath constraint:** the site is served from `/thekaymer.com/`, not from a domain
root. All links and asset paths must stay **relative**. Do not introduce
root-relative `/assets/...` paths.

**Jekyll constraint:** there is no `.nojekyll` file. Legacy Pages runs Jekyll, which
silently drops files and directories beginning with `_`. Add `.nojekyll` as part of
the redesign.

---

## 2. App repository identification (this was not obvious)

The four V1 apps map to repositories whose names do not match the product names:

| App | Repository | Notes |
|---|---|---|
| Findry | `Whispergil/findry` | React Native, private |
| **Nôs Beleza** | **`Whispergil/cape-verde-services-app`** | `app.json` → `"name": "Nôs Beleza"`, bundle `com.nosbeleza.app` |
| Placely | `Whispergil/placely-app` | `app.base.json` → `"name": "Placely"` |
| **YardMatch** | **`Whispergil/whisper`** | `app.json` → `"name": "YardMatch"`, bundle `com.whisper92.yardmatch` |

Repos explicitly **out of V1 scope**: `Loadora`, `Puncho` (PunchGo), `nosride`,
`NowIKnow`. Loadora and PunchGo must appear nowhere in visible V1 content or in
support app-selection lists.

All app repositories are **read-only sources**. Nothing was written to them.

---

## 3. Findry — verified store facts

Source: iTunes Lookup API, `https://itunes.apple.com/lookup?id=6773192473&country=us`

| Field | Verified value |
|---|---|
| Name | Findry |
| Seller | Kaymer LLC |
| Category | Productivity |
| Price | Free |
| Version | 1.0 |
| Released | 2026-08-15 |
| Minimum iOS | 16.4 |
| Age rating | 4+ |
| Ratings | 0 ratings, 0 average — **do not render a rating widget** |
| App Store URL | `https://apps.apple.com/us/app/findry/id6773192473` |

Status: **AVAILABLE**, Apple App Store only. No Google Play badge — Android is not
live.

**Real screenshots exist** on the App Store listing (5 total, 1284×2778 sources).
Thumbnail URLs returned by the lookup API can be re-requested at higher resolution
by swapping the `320x480bb.jpg` suffix. These are Kaymer's own product screenshots
and are the only verified real screenshots available for any V1 app:

- `01_find_it_in_seconds`
- `02_never_lose_hidden_utilities`
- `03_keep_every_project_organized`
- `04_save_what_matters_most`
- `06_everything_about_the_job`

The full verified App Store description is retrievable from the same lookup URL and
should be the source for Findry's app-page copy (condensed, not invented).

---

## 4. App icons — what is real and what is not

Verified by downloading each repo's icon and comparing bytes.

| App | Icon status |
|---|---|
| **Findry** | ✅ **REAL.** `findry/assets/icon.png` — orange "F" map-pin on black. Also already present in this repo as `findry-logo.png`. Use it. |
| Nôs Beleza | ❌ **Default Expo template icon.** |
| YardMatch | ❌ **Default Expo template icon** — byte-identical to the Nôs Beleza file (`md5 cb975bba2216ce10a60e6c0ffe9941a2`). |
| Placely | ❌ **Default Expo icon** (blue Expo chevron). `app.base.json` points iOS at `assets/expo.icon`, which contains only `expo-symbol.svg` + `grid.png` — the Expo icon-composer default. |

**Only Findry has a real app icon.** Nôs Beleza, Placely, and YardMatch must use a
restrained, obviously-temporary treatment (e.g. a gold-on-cream monogram tile).
Do not ship the Expo default as if it were a product icon, and do not reproduce the
AI-generated icons from the mockups (the yellow Placely pin and the Loadora hex in
the reference images are not real assets).

---

## 5. Screenshots

| App | Screenshots |
|---|---|
| Findry | ✅ 5 real ones on the App Store listing (above) |
| Nôs Beleza | ❌ none — repo holds only zero-byte placeholder JPGs (`hair1.jpg`, `barber1.jpg`, `lashes1.jpg`, `spa1.jpg` are all 0 bytes) |
| Placely | ❌ none — only Expo template art and `tutorial-web.png` |
| YardMatch | ❌ none — `rental*.jpg` and `construction/dump*.jpg` are generic stock photography, explicitly excluded by the brief |

Findry is the only app that can show real product screens. The other three get a
screenshot-free card/detail layout.

---

## 6. Verified app descriptions (derived from repo sources, not invented)

- **Findry** — field documentation / jobsite memory app for contractors, utility
  crews, and trades. Tagline: "Save it now. Find it later." Full copy available
  from the App Store description.
- **Nôs Beleza** — Cape Verde local services marketplace, beauty-first with
  generic category support (source: `cape-verde-services-app/README.md`). Booking
  flow, business profiles, island preference. **In development.**
- **Placely** — personal place memory app; save places with photos and notes,
  organize by country/state/city, revisit saved locations (source: repo description
  + the existing Placely legal/support pages already in this repo). **Coming soon.**
- **YardMatch** — marketplace connecting construction contractors, drivers, dump
  sites/facilities, equipment rental listings, and jobs (source:
  `whisper/CLAUDE.md` and `lib/schema/types.ts`). **In development.**

---

## 7. Legal content — findings and rules

### Findry (must be replaced with live wording)

The repository copies at `findry/privacy.html` and `findry/terms.html` are
**outdated**. The current live sources were fetched and verified:

| Document | Live URL | Verified heading | Verified effective date |
|---|---|---|---|
| Privacy | `https://www.findryapp.com/privacy` | `FINDRY PRIVACY POLICY` | **August 02, 2026** ✅ |
| Terms | `https://www.findryapp.com/` | `FINDRY TERMS OF SERVICE` | **August 02, 2026** ✅ |

Both pages returned HTTP 200 and both headings and the effective date match what
the brief specified. The pages are Squarespace-rendered, so the implementer must
strip presentation markup and re-mark the content semantically — copying the
**complete wording verbatim**, with no rewriting, summarizing, shortening, added
or removed clauses, no date change, and no replacement of `support@findryapp.com`.

Text extraction was started but **not finished** — the Cloud session should
re-fetch both URLs and extract from the `<main>` region.

### Routes that must not move

`findry/privacy.html`, `findry/terms.html`, `placely-privacy.html`,
`placely-terms.html`, `placely-support.html`, `privacy.html`, `terms.html`.

### Nôs Beleza and YardMatch

**No legal documents exist in either repository** (verified by code search and by
listing `docs/`). Do not generate policies, do not create legal links that lead
nowhere. Their app pages must be usable without legal buttons.

### Kaymer privacy policy — open item for the owner

`privacy.html` states the site is hosted by Vercel and describes Vercel's data
collection. The site is on GitHub Pages. Per the brief this sentence was **left
unchanged** and is flagged for owner approval rather than silently edited.

---

## 8. Blockers and missing assets

1. Real app icons for Nôs Beleza, Placely, YardMatch.
2. Product screenshots for Nôs Beleza, Placely, YardMatch.
3. Privacy policy and terms for Nôs Beleza and YardMatch.
4. Owner decision on the Vercel hosting sentence in `privacy.html`.

None of these may be filled in by invention. Each one that remains open should be
reported, not guessed.

---

## 9. Work remaining

Nothing in section 9 has been started.

- Shared `assets/css/site.css` and `assets/js/site.js`; de-duplicate the 11 copies
  of inline CSS and the two divergent mobile-menu implementations.
- Ivory/cream/gold brand system; retire the dark `#0A0A0F` theme and blue accents.
- Rebuild: home, apps portfolio (4 apps, filterable), 4 app-detail pages, about,
  support (`contact.html` route preserved, mailto POST form removed), legal index.
- Re-mark all preserved legal pages in the new presentation, wording untouched.
- Replace `findry/privacy.html` and `findry/terms.html` with verbatim live wording.
- Optimize assets (current PNGs total ~3.7 MB, all wildly oversized).
- Accessibility pass, metadata, Open Graph, `robots.txt`, `sitemap.xml`, favicons,
  `.nojekyll`.
- Remove `write_site.py` (confirmed unused leftover) and document the removal.
- Responsive verification at 320/375/390/430/768/1024/1440.
