# Kaymer V1 Redesign — Implementation Record

**Branch:** `redesign/v1-ivory-gold` (from `main` @ `7c881b7`)
**Status:** Implementation complete and verified. Not merged, not published.

This document records what was verified, what was built, and what is still
missing. Everything stated here was checked against a primary source — the
GitHub API, the iTunes Lookup API, or the live findryapp.com pages. Anything that
could not be verified was left out of the site rather than guessed at.

---

## 1. Deployment constraints this build respects

| Item | Value |
|---|---|
| Live URL | `https://whispergil.github.io/thekaymer.com/` |
| Pages source | branch `main`, path `/`, `build_type: legacy` (Jekyll) |
| Custom domain | none (`cname: null`) — Squarespace and DNS are unrelated to this repo |

- **All links and asset paths are relative.** The site is served from the
  `/thekaymer.com/` subpath, so a root-relative `/assets/...` path would break it.
  Verified: zero root-relative internal links.
- **`.nojekyll` added.** Legacy Pages runs Jekyll, which silently drops paths
  beginning with `_`. The file makes deployment predictable regardless of future
  file naming.
- No GitHub Actions workflow was added; Pages keeps building the branch it
  already builds. Pages settings were not touched.

---

## 2. App repository identification

The four V1 apps live in repositories whose names do not match the products:

| App | Repository | Evidence |
|---|---|---|
| Findry | `Whispergil/findry` | — |
| **Nôs Beleza** | **`Whispergil/cape-verde-services-app`** | `app.json` → `"name": "Nôs Beleza"`, bundle `com.nosbeleza.app` |
| Placely | `Whispergil/placely-app` | `app.base.json` → `"name": "Placely"` |
| **YardMatch** | **`Whispergil/whisper`** | `app.json` → `"name": "YardMatch"`, bundle `com.whisper92.yardmatch` |

Out of scope and absent from the site: `Loadora`, `Puncho` (PunchGo), `nosride`,
`NowIKnow`. All app repositories were read only — nothing was written, branched,
built, or deployed in any of them.

---

## 3. Findry — verified store facts

Source: `https://itunes.apple.com/lookup?id=6773192473&country=us`

| Field | Verified value |
|---|---|
| Seller | Kaymer LLC |
| Category | Productivity |
| Price | Free |
| Released | 2026-08-15 |
| Minimum iOS | 16.4 |
| Ratings | 0 ratings — **no rating widget is rendered anywhere** |
| Store URL | `https://apps.apple.com/us/app/findry/id6773192473` |

Findry is shown as **Available**, Apple App Store only. There is no Google Play
badge anywhere on the site, verified by scan.

---

## 4. Assets — real vs temporary

| App | Icon | Screenshots |
|---|---|---|
| **Findry** | ✅ real, from `findry/assets/icon.png` | ✅ 3 real, from the App Store listing |
| Nôs Beleza | ❌ temporary monogram | ❌ none |
| Placely | ❌ temporary monogram | ❌ none |
| YardMatch | ❌ temporary monogram | ❌ none |

**Why the other three have no icon:** each repo ships the unmodified Expo
template icon. The Nôs Beleza and YardMatch files are byte-identical to each
other (`md5 cb975bba2216ce10a60e6c0ffe9941a2`), and Placely's iOS icon points at
`assets/expo.icon`, which contains only the Expo icon-composer default. None of
them is a product mark, so none was used.

The temporary treatment is a cream monogram tile with a serif letterform and a
soft inner ring (`.app-icon--placeholder`). It is deliberately typographic and
flatter than a real app icon, so it reads as a considered placeholder rather
than a finished mark, and it carries an accessible label reading "app icon not
yet available". Each one also sits beside a status badge that says the app is
not released.

**Rejected sources:** the AI-generated icons and app screens in the reference
mockups; the stock photography in `whisper/assets/images/` (`rental*.jpg`,
`construction/dump*.jpg`); the zero-byte placeholder JPEGs in the Nôs Beleza repo.

### Asset provenance and optimisation

| File | Source | Treatment |
|---|---|---|
| `assets/img/findry-icon.png` / `.webp` | `Whispergil/findry` → `assets/icon.png` | resized 1024→256, stripped |
| `assets/img/findry-screenshot-1..3.jpg` / `.webp` | Findry App Store listing | resized to 540px wide, JPEG q82 + WebP q82 |
| `assets/img/og-kaymer.jpg` | generated for this build | 1200×630 ivory/gold social card |
| `assets/img/favicon.svg`, `apple-touch-icon.png` | generated for this build | temporary bronze "K" mark |

Removed: `logo.png`, `icon.png`, `hero-phones.png`, `findry-logo.png` (3.6 MB of
unoptimised, blue-branded, or superseded art), and `write_site.py` (a three-line
leftover with a hardcoded absolute path, referenced by nothing).

Total deployed payload: **3.72 MB → 0.83 MB**.

---

## 5. Legal content

### Findry — replaced with the live wording

The repository copies were outdated. Both live documents were fetched and
re-marked into the new presentation:

| Document | Source | Verified heading | Effective date |
|---|---|---|---|
| `findry/privacy.html` | `https://www.findryapp.com/privacy` | `FINDRY PRIVACY POLICY` | August 02, 2026 |
| `findry/terms.html` | `https://www.findryapp.com/` | `FINDRY TERMS OF SERVICE` | August 02, 2026 |

### Placely and Kaymer — transplanted unchanged

`privacy.html`, `terms.html`, `placely-privacy.html`, `placely-terms.html`, and
`placely-support.html` had their content blocks lifted out of the previous pages
and dropped into the new shell. Wording, inline links, and ordering are
unchanged; only the presentation around them is new.

### Fidelity verification

All seven documents were compared against their approved source after stripping
presentation markup and normalising whitespace. **Every one matched character for
character**, including the Findry documents' `support@findryapp.com` contact
address, which was deliberately not replaced with the studio address.

### Preserved routes

`findry/privacy.html`, `findry/terms.html`, `placely-privacy.html`,
`placely-terms.html`, `placely-support.html`, `privacy.html`, `terms.html` — all
still resolve at their original paths. `index.html`, `apps.html`, `about.html`,
and `contact.html` were also kept at their existing paths.

### ⚠ Open item for the owner

`privacy.html` still states that the website is hosted by **Vercel** and
describes Vercel's data collection. The site runs on GitHub Pages. Per
instruction this sentence was **not** modified — changing a published legal
disclosure is the owner's call. It needs a decision before publishing.

---

## 6. Missing — must not be invented

1. Real app icons for Nôs Beleza, Placely, and YardMatch.
2. Product screenshots for those same three apps.
3. Privacy policy and terms for **Nôs Beleza** and **YardMatch**. Neither repo
   contains any legal document. Their app pages therefore carry no legal links at
   all, and say so in plain language rather than linking somewhere broken.
4. Owner decision on the Vercel sentence above.
5. Release dates for the three unreleased apps — none is claimed anywhere.

---

## 7. Architecture

Still a dependency-free static site: no framework, no package manager, no
lockfile, no build step, no runtime dependency, no backend, no database.

What changed is that the 11 copies of inline CSS and the two divergent mobile
menus collapsed into `assets/css/site.css` and `assets/js/site.js`. Both JS
features — the mobile menu and the apps filter — are progressive enhancements;
every page renders completely with JavaScript disabled, and the filter bar is
hidden until the script reveals it.

Support is email-only by design. The old `mailto:` POST form was removed: most
browsers no longer honour such submissions, so it silently discarded messages.
Per-app links now carry pre-filled subjects.

---

## 8. Visual polish pass

A second pass refined the approved ivory/gold direction without changing it.
The substantive layout decisions, for the record:

- **The home hero and the Findry feature merged.** They were separate sections;
  at desktop the hero filled only the left half of the screen while the feature
  card below it carried 1299px of dead space beside two oversized screenshots.
  Findry now shares the hero as a compact showcase panel, which fills the empty
  half and gives the one shipped app the strongest position on the page.
- **Screenshots became a scrollable rail.** Three stacked phone screenshots ran
  to 2127px on the Findry page alone. The rail is keyboard reachable, labelled,
  and snaps; it stays scrollable at every width because even a wide aside column
  is narrower than three phone shots side by side.
- **Unreleased apps use a single-column hero.** The two-column layout left an
  empty half beside apps with no screenshots, and paired two notices that said
  much the same thing. One notice now covers both facts.
- **The apps grid is 2×2 at desktop** rather than three across with an orphaned
  fourth card, and every card ends with its actions on a shared rule so cards of
  different length align along the same edge.

Accessibility changes made during the pass: the "Available" badge lost its gold
wash, which measured 4.26:1 behind bronze text and now measures 5.15:1; footer
and card links were held at 44px targets; and the single entrance animation is
wrapped in `prefers-reduced-motion: no-preference`.

Page weight fell again as a result — the home page is 4633px tall at 390px wide,
down from 5875px, and the Findry page 3636px, down from 5142px.
