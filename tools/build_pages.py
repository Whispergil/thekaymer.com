#!/usr/bin/env python3
"""Page generator for the Kaymer V1 static site.

Emits the plain static HTML that this repository serves. It is a maintenance
tool, not a build step: the deployed site has no framework, no dependency and
no build pipeline, and the committed HTML is what ships. The generator exists
so the header, footer and page shell are written once instead of being
copy-pasted into sixteen files by hand.

The committed HTML is also the source of truth for legal wording. Every legal
and support document is re-emitted from its own current <div class="legal-body">
and <p class="updated">, so running this cannot alter approved policy text or
roll a date backwards. Regeneration should be a no-op unless layout or shared
copy changed.

    python3 tools/build_pages.py                  # regenerate in place
    python3 tools/build_pages.py --root /tmp/copy  # dry run against a copy

Always diff the result before committing it.
"""
import html
import json
import os
import re

# Repository root. Defaults to the directory containing tools/, so the script
# runs from a checkout anywhere; --root points it at an isolated copy for
# dry-run comparisons.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://whispergil.github.io/thekaymer.com/'
EMAIL = 'support@thekaymer.com'

# NOTE ON THE SOURCE OF TRUTH FOR LEGAL WORDING
#
# This script used to read the legal documents from a pinned commit
# (BASE_REV = '87f8437'), which was correct only while that commit held the
# approved wording. It no longer does: privacy.html has since been corrected by
# hand (GitHub Pages hosting disclosure, the Cookies paragraph, the
# email-contact wording and its date). Reading from that commit would have
# silently reinstated all of it.
#
# The committed HTML in this repository is now the single source of truth.
# Every legal and support document is re-emitted from its own current
# <div class="legal-body"> and <p class="updated">, so regenerating reproduces
# the approved wording byte for byte and can never resurrect an old revision.

# --------------------------------------------------------------------- apps --
APPS = [
    {
        'slug': 'findry',
        'name': 'Findry',
        'status': 'available',
        'badge': 'Available',
        'tagline': 'Save it now. Find it later.',
        'short': 'Field documentation for contractors and trades. Save jobsite records, '
                 'photos, measurements, and reference points to the right project.',
        'long': 'Findry is a field documentation and jobsite memory app for contractors, '
                'utility crews, excavators, plumbers, electricians, inspectors, and anyone '
                'who needs to record important jobsite information and find it again. Every '
                'record belongs to a project, so details stay organised whether you return '
                'to a job next week or in five years.',
        'icon': 'assets/img/findry-icon.png',
        'icon_webp': 'assets/img/findry-icon.webp',
        'platform': 'iPhone — requires iOS 16.4 or later',
        'store_name': 'Apple App Store',
        'store_url': 'https://apps.apple.com/us/app/findry/id6773192473',
        'price': 'Free, with an optional Findry Pro subscription',
        'category': 'Productivity',
        'released': 'August 15, 2026',
        'privacy': 'findry/privacy.html',
        'terms': 'findry/terms.html',
        'shots': [
            ('assets/img/findry-screenshot-1', 'Findry app store screenshot: the Lookup screen, showing emergency lookup shortcuts and recently added records.'),
            ('assets/img/findry-screenshot-2', 'Findry app store screenshot: a record showing the depth and location of a buried utility.'),
            ('assets/img/findry-screenshot-3', 'Findry app store screenshot: the project list, with each project showing its saved record count.'),
        ],
        'features': [
            ('Save records in seconds', 'Capture photos, depths, measurements, pipe sizes, materials, valve locations, reference points, and field notes before they are forgotten.'),
            ('Organise every project', 'Each project keeps its own records, photos, reference points, and notes, from a residential repair to a large infrastructure installation.'),
            ('Find it later', 'Search and browse your saved field information when you come back to a job — next week or next year.'),
        ],
    },
    {
        'slug': 'nos-beleza',
        'name': 'Nôs Beleza',
        'status': 'in-development',
        'badge': 'In development',
        'tagline': 'A local services marketplace for Cape Verde.',
        'short': 'A local services marketplace for Cape Verde, starting with beauty and '
                 'personal care.',
        'long': 'Nôs Beleza is a local services marketplace built for Cape Verde. It is '
                'designed to let people discover nearby businesses, browse the services they '
                'offer, and book an appointment — starting with beauty and personal care, '
                'with room for more categories as the marketplace grows.',
        'icon': None,
        'platform': None,
        'features': [
            ('Discover local businesses', 'Browse businesses and the services they offer, filtered by island.'),
            ('Book an appointment', 'Request a booking, and let the business confirm, decline, or propose a new time.'),
            ('Built for more than beauty', 'The underlying marketplace is category-driven, so new kinds of local services can be added later.'),
        ],
    },
    {
        'slug': 'placely',
        'name': 'Placely',
        'status': 'coming-soon',
        'badge': 'Coming soon',
        'tagline': 'Save places today. Find them later.',
        'short': 'A personal place memory app. Save the places that matter with photos and '
                 'notes, and find them again later.',
        'long': 'Placely is a personal place memory app. Save the places you want to '
                'remember with a photo and your own notes, organise them by country, state, '
                'and city, and come back to them whenever you need them.',
        'icon': None,
        'platform': None,
        'privacy': 'placely-privacy.html',
        'terms': 'placely-terms.html',
        'support_page': 'placely-support.html',
        'features': [
            ('Save a place with context', 'Keep a name, category, notes, and a photo alongside the location itself.'),
            ('Organise by where it is', 'Places are grouped by country, state or province, and city.'),
            ('Come back to it', 'Revisit your saved places and see them on a map when you need them again.'),
        ],
    },
    {
        'slug': 'yardmatch',
        'name': 'YardMatch',
        'status': 'in-development',
        'badge': 'In development',
        'tagline': 'A marketplace for construction sites, hauling, and equipment.',
        'short': 'A marketplace connecting construction contractors, drivers, dump sites, '
                 'and equipment rentals.',
        'long': 'YardMatch is a marketplace for construction work. It is being built to '
                'connect contractors, drivers, dump sites and facilities, equipment rental '
                'listings, and jobs — so a crew can find the site, hauler, or machine a job '
                'needs without working the phone all morning.',
        'icon': None,
        'platform': None,
        'features': [
            ('Find a site', 'Locate dump sites and facilities, including ones that have not been claimed by an owner yet.'),
            ('Match work with capacity', 'Post jobs and availability, so contractors and drivers can find each other.'),
            ('Rent what you need', 'Browse equipment rental listings created by the providers who own them.'),
        ],
    },
]
APP = {a['slug']: a for a in APPS}

NAV = [
    ('index.html', 'Home'),
    ('apps.html', 'Apps'),
    ('about.html', 'About'),
    ('contact.html', 'Support'),
    ('legal.html', 'Legal'),
]


def e(text):
    return html.escape(text, quote=False)


def slugify(text):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s or 'section'


def mailto(subject):
    return 'mailto:{}?subject={}'.format(EMAIL, subject.replace(' ', '%20').replace('ô', '%C3%B4'))


# ------------------------------------------------------------------- shell ---
def head(title, description, canonical, up, og_type='website'):
    p = up
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{SITE}{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Kaymer LLC">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{SITE}{canonical}">
<meta property="og:image" content="{SITE}assets/img/og-kaymer.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Kaymer LLC — practical apps, thoughtfully built.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{SITE}assets/img/og-kaymer.jpg">
<meta name="theme-color" content="#FCFAF6">
<link rel="icon" href="{p}assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{p}assets/img/apple-touch-icon.png">
<link rel="stylesheet" href="{p}assets/css/site.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
'''


def header(current, up):
    desktop = '\n'.join(
        '      <li><a href="{}{}"{}>{}</a></li>'.format(
            up, href, ' aria-current="page"' if href == current else '', label)
        for href, label in NAV)
    mobile = '\n'.join(
        '      <li><a href="{}{}"{}>{}</a></li>'.format(
            up, href, ' aria-current="page"' if href == current else '', label)
        for href, label in NAV)
    return f'''<header class="site-header">
  <div class="shell header-bar">
    <a class="wordmark" href="{up}index.html"><span>KAYMER</span></a>
    <nav class="nav-desktop" aria-label="Primary">
      <ul>
{desktop}
      </ul>
    </nav>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu">
      <span></span><span></span><span></span>
    </button>
  </div>
  <nav class="nav-mobile" id="site-menu" aria-label="Primary, mobile">
    <ul class="shell">
{mobile}
    </ul>
  </nav>
</header>
'''


def footer(up):
    app_links = '\n'.join(
        '        <li><a href="{}apps/{}.html">{}</a></li>'.format(up, a['slug'], e(a['name']))
        for a in APPS)
    return f'''<footer class="site-footer">
  <div class="shell">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="wordmark" href="{up}index.html"><span>KAYMER</span></a>
        <p>An independent mobile app studio building focused tools for everyday work and life.</p>
      </div>
      <div>
        <h2>Apps</h2>
        <ul>
{app_links}
          <li><a href="{up}apps.html">All apps</a></li>
        </ul>
      </div>
      <div>
        <h2>Support</h2>
        <ul>
          <li><a href="{up}contact.html">Get support</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        </ul>
      </div>
      <div>
        <h2>Legal</h2>
        <ul>
          <li><a href="{up}legal.html">All legal documents</a></li>
          <li><a href="{up}privacy.html">Privacy Policy</a></li>
          <li><a href="{up}terms.html">Terms of Service</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-base">
      <span>&copy; 2026 Kaymer LLC. All rights reserved.</span>
      <span>Massachusetts, USA</span>
    </div>
  </div>
</footer>
<script src="{up}assets/js/site.js" defer></script>
</body>
</html>
'''


def page(path, title, description, current, body, structured=None, og_type='website'):
    up = '../' if '/' in path else ''
    canonical = path
    out = head(title, description, canonical, up, og_type)
    out += header(current, up)
    out += body
    out += footer(up)
    if structured:
        out = out.replace('</head>', '<script type="application/ld+json">\n{}\n</script>\n</head>'.format(
            json.dumps(structured, indent=2, ensure_ascii=False)))
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(out)
    return path


# ------------------------------------------------------------- app helpers ---
def icon_markup(app, up='', large=False):
    size = ' app-icon--lg' if large else ''
    px = '84' if large else '62'
    if app.get('icon'):
        return ('<picture class="app-icon{size}">'
                '<source srcset="{up}{webp}" type="image/webp">'
                '<img src="{up}{png}" width="{px}" height="{px}" alt="{name} app icon">'
                '</picture>').format(size=size, up=up, webp=app['icon_webp'], png=app['icon'],
                                     px=px, name=e(app['name']))
    letter = app['name'][0]
    return ('<div class="app-icon{size} app-icon--placeholder" role="img" '
            'aria-label="{name} — app icon not yet available">{letter}</div>').format(
                size=size, name=e(app['name']), letter=e(letter))




BADGE_CLASS = {'available': 'available', 'coming-soon': 'soon', 'in-development': 'dev'}


def badge(app):
    return '<span class="badge badge--{}">{}</span>'.format(
        BADGE_CLASS[app['status']], e(app['badge']))


APPSTORE_SVG = ('<svg width="17" height="20" viewBox="0 0 384 512" fill="currentColor" aria-hidden="true">'
                '<path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>')


def store_button(app, small=False):
    if app['status'] != 'available':
        return ''
    size = ' btn--sm' if small else ''
    return (f'<a class="btn btn--appstore{size}" href="{app["store_url"]}">'
            f'{APPSTORE_SVG}<span>Download on the App Store</span></a>')


def shot(src, alt, up='', lazy=True):
    loading = ' loading="lazy" decoding="async"' if lazy else ' decoding="async"'
    return (f'<picture>\n'
            f'          <source srcset="{up}{src}.webp" type="image/webp">\n'
            f'          <img src="{up}{src}.jpg" width="540" height="1168"{loading} alt="{e(alt)}">\n'
            f'        </picture>')


# =============================================================== home page ===
def build_home():
    findry = APP['findry']
    others = [a for a in APPS if a['slug'] != 'findry']

    cards = []
    for i, a in enumerate(others):
        cards.append(f'''        <article class="app-card rise rise-{min(i + 1, 3)}">
          {icon_markup(a)}
          <h3>{e(a['name'])}</h3>
          <div class="badge-row">{badge(a)}</div>
          <p>{e(a['short'])}</p>
          <div class="card-actions">
            <a class="btn btn--quiet" href="apps/{a['slug']}.html">About {e(a['name'])}</a>
          </div>
        </article>''')
    cards = '\n'.join(cards)

    hero_shot = shot(findry['shots'][0][0], findry['shots'][0][1], lazy=False)

    body = f'''<main id="main">

  <section class="hero shell" aria-labelledby="hero-title">
    <div class="hero-split">

      <div class="hero-copy rise">
        <p class="eyebrow">Independent app studio</p>
        <h1 id="hero-title">Practical apps. Thoughtfully built.</h1>
        <div class="rule"></div>
        <p class="lead">Focused mobile tools that make everyday work and life simpler.</p>
        <div class="btn-row">
          <a class="btn btn--primary" href="apps.html">Explore Our Apps</a>
          <a class="btn btn--quiet" href="contact.html">Get Support</a>
        </div>
      </div>

      <div class="showcase rise rise-2">
        <div class="showcase-head">
          {icon_markup(findry)}
          <div class="showcase-title">
            <h2>{e(findry['name'])}</h2>
            <div class="badge-row">{badge(findry)}</div>
          </div>
        </div>
        <p>{e(findry['short'])}</p>
        <div class="showcase-figure">
          {hero_shot}
        </div>
        <div class="btn-row">
          {store_button(findry, small=True)}
          <a class="btn btn--quiet" href="apps/findry.html">View Findry</a>
        </div>
      </div>

    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="more-apps">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">In the workshop</p>
        <h2 id="more-apps">What we are building next.</h2>
        <p class="lead">Three more apps are in progress. None of them is released yet, and we
          will not pretend otherwise — each one gets a store link the day it earns one.</p>
      </div>
      <div class="card-grid card-grid--three">
{cards}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="values">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">How we work</p>
        <h2 id="values">Small studio. Narrow focus.</h2>
      </div>
      <div class="value-grid">
        <div class="value-item">
          <div class="rule"></div>
          <h3>Built around a real problem</h3>
          <p>Each app starts with a specific job someone actually has to do, not with a
            feature list.</p>
        </div>
        <div class="value-item">
          <div class="rule"></div>
          <h3>Only the data the app needs</h3>
          <p>What each app collects, and where it is stored, is written down in its own
            privacy policy in plain language.</p>
        </div>
        <div class="value-item">
          <div class="rule"></div>
          <h3>Answered by the people who built it</h3>
          <p>Support email goes to the studio. There is no queue and no call centre.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="contact">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <h2 id="contact">Questions about an app?</h2>
          <p>Email the studio directly. We read everything that arrives.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--primary" href="contact.html">Get Support</a>
        </div>
      </div>
    </div>
  </section>

</main>
'''
    structured = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Kaymer LLC",
        "url": SITE,
        "description": "Independent mobile app studio based in Massachusetts, USA.",
        "email": EMAIL,
        "address": {"@type": "PostalAddress", "addressRegion": "MA", "addressCountry": "US"},
    }
    return page('index.html',
                'Kaymer LLC — Independent Mobile App Studio',
                'Kaymer LLC is an independent mobile app studio in Massachusetts building focused tools for everyday work and life, including Findry on the App Store.',
                'index.html', body, structured)


# =============================================================== apps page ===
def build_apps():
    cards = []
    for a in APPS:
        links = []
        if a.get('privacy'):
            links.append(f'<a href="{a["privacy"]}">Privacy</a>')
        if a.get('terms'):
            links.append(f'<a href="{a["terms"]}">Terms</a>')
        if a.get('support_page'):
            links.append(f'<a href="{a["support_page"]}">Support</a>')
        links_html = ('\n            <div class="card-links">' + ''.join(links) + '</div>') if links else ''

        meta = f'\n          <p class="card-meta">{e(a["platform"])}</p>' if a.get('platform') else ''
        store = ('\n            <a class="btn btn--quiet" href="' + a['store_url'] + '">App Store</a>') \
            if a['status'] == 'available' else ''

        cards.append(f'''        <article class="app-card" data-status="{a['status']}">
          {icon_markup(a)}
          <h3>{e(a['name'])}</h3>
          <div class="badge-row">{badge(a)}</div>{meta}
          <p>{e(a['short'])}</p>
          <div class="card-actions">
            <a class="btn btn--secondary btn--sm" href="apps/{a['slug']}.html">View {e(a['name'])}</a>{store}{links_html}
          </div>
        </article>''')
    cards = '\n'.join(cards)

    body = f'''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="apps-title">
    <div class="rise">
      <p class="eyebrow">Our apps</p>
      <h1 id="apps-title">Tools built for real life.</h1>
      <div class="rule"></div>
      <p class="lead">One app is on the App Store today. Three more are in development. This
        page shows exactly where each one stands.</p>
    </div>
  </section>

  <section class="section section--flush-top" aria-labelledby="portfolio">
    <div class="shell">
      <h2 id="portfolio" class="visually-hidden">App portfolio</h2>

      <div class="filter-bar" role="group" aria-label="Filter apps by status" hidden>
        <button type="button" data-filter="all" aria-pressed="true">All</button>
        <button type="button" data-filter="available" aria-pressed="false">Available</button>
        <button type="button" data-filter="coming-soon" aria-pressed="false">Coming soon</button>
        <button type="button" data-filter="in-development" aria-pressed="false">In development</button>
      </div>
      <p id="filter-status" class="visually-hidden" role="status" aria-live="polite"></p>

      <div class="card-grid" id="app-list">
{cards}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="status-key">
    <div class="shell">
      <div class="section-head">
        <h2 id="status-key">What the statuses mean</h2>
      </div>
      <div class="value-grid">
        <div class="value-item">
          <div class="badge-row" style="margin-bottom:var(--s-3)"><span class="badge badge--available">Available</span></div>
          <p>Released and downloadable today. Findry is on the Apple App Store for iPhone. It
            is not on Google Play yet.</p>
        </div>
        <div class="value-item">
          <div class="badge-row" style="margin-bottom:var(--s-3)"><span class="badge badge--soon">Coming soon</span></div>
          <p>Feature work is largely done and the app is being prepared for release. No release
            date is announced.</p>
        </div>
        <div class="value-item">
          <div class="badge-row" style="margin-bottom:var(--s-3)"><span class="badge badge--dev">In development</span></div>
          <p>Actively being built. Screens, icons, and store listings are not final, and no
            platform commitment has been made.</p>
        </div>
      </div>
    </div>
  </section>

</main>
'''
    return page('apps.html', 'Apps — Kaymer LLC',
                'The Kaymer LLC app portfolio: Findry on the App Store, plus Nôs Beleza, Placely, and YardMatch in development.',
                'apps.html', body)


# ========================================================== app detail page ==
def build_app_page(a):
    up = '../'

    if a['status'] == 'available':
        actions = f'''<div class="btn-row">
          {store_button(a)}
          <a class="btn btn--quiet" href="{mailto(a['name'] + ' Support')}">Get {e(a['name'])} Support</a>
        </div>'''
    else:
        actions = f'''<p class="note"><strong>{e(a['name'])} is not released yet.</strong>
          There is no download link, no store listing, no announced release date, and no
          finished screens to show. Rather than mock something up, this page waits for the
          real thing.</p>
        <div class="btn-row">
          <a class="btn btn--secondary" href="{mailto(a['name'] + ' Support')}">Contact the studio</a>
        </div>'''

    if a.get('shots'):
        rail = '\n'.join('        ' + shot(src, alt, up=up) for src, alt in a['shots'])
        aside = f'''
      <div class="rise rise-2">
        <div class="shot-rail" tabindex="0" role="group" aria-label="{e(a['name'])} screenshots">
{rail}
        </div>
      </div>'''
    else:
        aside = ''  

    features = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(t)}</h3>
          <p>{e(d)}</p>
        </div>''' for t, d in a['features'])

    meta = []
    if a.get('platform'):
        meta.append(('Platform', e(a['platform'])))
    if a.get('store_name'):
        meta.append(('Available on', e(a['store_name'])))
    if a.get('category'):
        meta.append(('Category', e(a['category'])))
    if a.get('price'):
        meta.append(('Price', e(a['price'])))
    if a.get('released'):
        meta.append(('Released', e(a['released'])))
    if not meta:
        meta.append(('Status', e(a['badge'])))
        meta.append(('Platform', 'Not announced'))
        meta.append(('Release date', 'Not announced'))
    meta_rows = '\n'.join(f'        <div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in meta)

    legal_links = []
    if a.get('privacy'):
        legal_links.append(f'<a href="{up}{a["privacy"]}">{e(a["name"])} Privacy Policy</a>')
    if a.get('terms'):
        legal_links.append(f'<a href="{up}{a["terms"]}">{e(a["name"])} Terms</a>')
    if a.get('support_page'):
        legal_links.append(f'<a href="{up}{a["support_page"]}">{e(a["name"])} Support</a>')

    if legal_links:
        legal_block = '<div class="legal-footer-links">' + ''.join(legal_links) + '</div>'
    else:
        legal_block = (f'<p class="note" style="margin-top:var(--s-6)">{e(a["name"])} does not have a '
                       'published privacy policy or terms of use yet. Rather than link to a page that '
                       'does not exist, this page links nowhere — the documents will appear here when '
                       'they are written.</p>')

    grid_mod = '' if a.get('shots') else ' app-hero-grid--single'

    structured = None
    if a['status'] == 'available':
        structured = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": a['name'],
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "iOS 16.4",
            "url": a['store_url'],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="{up}apps.html">Back to Apps</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid{grid_mod}">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <div class="badge-row" style="margin-bottom:var(--s-3)">{badge(a)}</div>
        <h1>{e(a['name'])}</h1>
        <p class="tagline">{e(a['tagline'])}</p>
        <p class="lead">{e(a['long'])}</p>
        {actions}
      </div>{aside}
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="features">
    <div class="shell">
      <div class="section-head">
        <h2 id="features">What it does</h2>
      </div>
      <div class="feature-list">
{features}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="details">
    <div class="shell">
      <div class="section-head">
        <h2 id="details">Details</h2>
      </div>
      <dl class="meta-list">
{meta_rows}
      </dl>

      <div class="email-card" style="margin-top:var(--s-7)">
        <div class="email-card-body">
          <h3 class="ui-head">Need help with {e(a['name'])}?</h3>
          <p>Email the studio and mention the app name.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--primary" href="{mailto(a['name'] + ' Support')}">Email {e(a['name'])} Support</a>
        </div>
      </div>

      {legal_block}
    </div>
  </section>

</main>
'''
    return page(f'apps/{a["slug"]}.html', f'{a["name"]} — Kaymer LLC',
                a['short'], 'apps.html', body, structured, og_type='article')


# ============================================================== about page ===
def build_about():
    body = '''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="about-title">
    <div class="rise">
      <p class="eyebrow">About</p>
      <h1 id="about-title">An independent app studio.</h1>
      <div class="rule"></div>
      <p class="lead">Kaymer LLC builds focused mobile tools for everyday work and life.</p>
    </div>
  </section>

  <section class="section section--flush-top">
    <div class="shell prose">
      <p>Kaymer LLC is an independent mobile app studio based in Massachusetts, USA. We design
        and build our own apps rather than taking on client work.</p>
      <p>Every app starts the same way: with a specific, practical problem that someone deals
        with regularly, and that existing software handles badly or not at all. Findry came
        from field crews needing to remember exactly where something was buried. The apps still
        in development each began the same way.</p>
      <p>We keep the catalogue small on purpose. A studio this size can either ship many
        shallow apps or a few that hold up over years of real use, and we would rather do the
        second.</p>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="principles">
    <div class="shell">
      <div class="section-head">
        <h2 id="principles">What that means in practice</h2>
      </div>
      <div class="value-grid">
        <div class="value-item">
          <div class="rule"></div>
          <h3>Practical before clever</h3>
          <p>Features earn their place by making a real task faster, not by being interesting
            to build.</p>
        </div>
        <div class="value-item">
          <div class="rule"></div>
          <h3>Honest about status</h3>
          <p>An app is listed as available only once it is genuinely downloadable. Everything
            else is labelled as what it is.</p>
        </div>
        <div class="value-item">
          <div class="rule"></div>
          <h3>Clear about data</h3>
          <p>Each released app publishes its own privacy policy describing what it collects and
            where that information lives.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <h2>Get in touch</h2>
          <p>Questions about an app, or about the studio.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--primary" href="contact.html">Get Support</a>
        </div>
      </div>
    </div>
  </section>

</main>
'''
    return page('about.html', 'About — Kaymer LLC',
                'Kaymer LLC is an independent mobile app studio based in Massachusetts, USA, building focused tools for everyday work and life.',
                'about.html', body)


# ============================================================ support page ===
def build_support():
    cards = []
    for a in APPS:
        cards.append(f'''        <article class="support-card">
          {icon_markup(a)}
          <div class="support-card-body">
            <h3>{e(a['name'])}</h3>
            <div class="badge-row">{badge(a)}</div>
            <div class="btn-row">
              <a class="btn btn--quiet" href="{mailto(a['name'] + ' Support')}">Email about {e(a['name'])}</a>
            </div>
          </div>
        </article>''')
    cards = '\n'.join(cards)

    def row(href, label, note):
        return f'''        <a href="{href}">
          <span class="row-label">{label}<span class="row-note">{note}</span></span>
          <span class="chevron" aria-hidden="true">&rarr;</span>
        </a>'''

    findry_topics = '\n'.join([
        row('findry/privacy.html#s-1-information-we-collect', 'What Findry collects',
            'Account, project, record, and photo information, in the privacy policy.'),
        row('findry/terms.html#s-4-free-plan-and-findry-pro', 'Free plan and Findry Pro',
            'What each plan includes, in the terms of service.'),
        row('findry/terms.html#s-5-subscriptions-and-billing', 'Subscriptions and billing',
            'Renewals, cancelling, and restoring a purchase.'),
        row('findry/privacy.html#s-8-account-deletion', 'Deleting your Findry account',
            'What happens to your data when you delete an account.'),
    ])

    placely_topics = '\n'.join([
        row('placely-support.html', 'Placely help topics',
            'Sign-in, saving places, location and photos, account deletion.'),
        row('placely-privacy.html', 'What Placely collects',
            'Account data, saved places, location, and photos.'),
    ])

    body = f'''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="support-title">
    <div class="rise">
      <p class="eyebrow">Support</p>
      <h1 id="support-title">How can we help?</h1>
      <div class="rule"></div>
      <p class="lead">Email reaches the studio directly. Tell us which app you are using and
        what happened, and we will take it from there.</p>
      <div class="btn-row">
        <a class="btn btn--primary" href="mailto:{EMAIL}">Email {EMAIL}</a>
      </div>
    </div>
  </section>

  <section class="section section--flush-top" aria-labelledby="by-app">
    <div class="shell">
      <div class="section-head">
        <h2 id="by-app">Choose an app</h2>
        <p class="lead">Each link opens your mail app with the subject filled in, so your
          message lands in the right place.</p>
      </div>
      <div class="support-grid">
{cards}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="topics">
    <div class="shell">
      <div class="section-head">
        <h2 id="topics">Answers already written down</h2>
        <p class="lead">These go straight to the relevant section of a published document — no
          ticket required.</p>
      </div>

      <h3 class="ui-head" style="margin-bottom:var(--s-3)">Findry</h3>
      <div class="link-rows" style="margin-bottom:var(--s-6)">
{findry_topics}
      </div>

      <h3 class="ui-head" style="margin-bottom:var(--s-3)">Placely</h3>
      <div class="link-rows">
{placely_topics}
      </div>

      <p class="note" style="margin-top:var(--s-6)">Nôs Beleza and YardMatch are still in
        development and do not have published help documents yet. Email the studio and we will
        answer directly.</p>
    </div>
  </section>

  <section class="section" aria-labelledby="direct">
    <div class="shell">
      <div class="section-head">
        <h2 id="direct">Contact the studio</h2>
        <p class="lead">There is no contact form here on purpose: a form that silently drops
          messages is worse than no form. Email is the whole support system, and it is read by
          the people who build the apps.</p>
      </div>
      <div class="email-card">
        <div class="email-card-body">
          <h3 class="ui-head">General support</h3>
          <p>Include the app name and a description of the issue. We typically reply within one
            business day.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--primary" href="mailto:{EMAIL}">{EMAIL}</a>
        </div>
      </div>
      <p class="note" style="margin-top:var(--s-5)">Findry's own legal documents list
        <a href="mailto:support@findryapp.com">support@findryapp.com</a> for questions about
        those documents. Both addresses reach Kaymer LLC.</p>
    </div>
  </section>

</main>
'''
    return page('contact.html', 'Support — Kaymer LLC',
                'Get support for Kaymer LLC apps. Email support@thekaymer.com, or jump straight to the published help and legal documents for Findry and Placely.',
                'contact.html', body)


# ============================================================== legal index ==
def build_legal_index():
    def row(href, label, note):
        return f'''        <a href="{href}">
          <span class="row-label">{label}<span class="row-note">{note}</span></span>
          <span class="chevron" aria-hidden="true">&rarr;</span>
        </a>'''

    # Dates come from each document rather than being repeated here, so the
    # index cannot drift out of step with the policy it points at.
    company = '\n'.join([
        row('privacy.html', 'Kaymer LLC Privacy Policy',
            legal_date_note('privacy.html', 'How the thekaymer.com website handles information.')),
        row('terms.html', 'Kaymer LLC Terms of Service',
            legal_date_note('terms.html', 'Terms covering use of this website.')),
    ])
    findry_rows = '\n'.join([
        row('findry/privacy.html', 'Findry Privacy Policy', legal_date_note('findry/privacy.html', '')),
        row('findry/terms.html', 'Findry Terms of Service', legal_date_note('findry/terms.html', '')),
    ])
    placely_rows = '\n'.join([
        row('placely-privacy.html', 'Placely Privacy Policy', legal_date_note('placely-privacy.html', '')),
        row('placely-terms.html', 'Placely Terms of Use', legal_date_note('placely-terms.html', '')),
        row('placely-support.html', 'Placely Support',
            'Help topics for accounts, places, photos, and deletion.'),
    ])

    body = f'''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="legal-title">
    <div class="rise">
      <p class="eyebrow">Legal</p>
      <h1 id="legal-title">Legal documents.</h1>
      <div class="rule"></div>
      <p class="lead">Every published policy for Kaymer LLC and its apps, in one place.</p>
    </div>
  </section>

  <section class="section section--flush-top">
    <div class="shell">

      <h2 class="ui-head" style="margin-bottom:var(--s-3)">Kaymer LLC</h2>
      <div class="link-rows" style="margin-bottom:var(--s-6)">
{company}
      </div>

      <h2 class="ui-head" style="margin-bottom:var(--s-3)">Findry</h2>
      <div class="link-rows" style="margin-bottom:var(--s-6)">
{findry_rows}
      </div>

      <h2 class="ui-head" style="margin-bottom:var(--s-3)">Placely</h2>
      <div class="link-rows" style="margin-bottom:var(--s-6)">
{placely_rows}
      </div>

      <h2 class="ui-head" style="margin-bottom:var(--s-3)">Nôs Beleza and YardMatch</h2>
      <p class="note">Both apps are still in development and have no published privacy policy
        or terms yet. When those documents exist they will be listed here.</p>

    </div>
  </section>

</main>
'''
    return page('legal.html', 'Legal — Kaymer LLC',
                'Privacy policies, terms, and support documents for Kaymer LLC and its apps, including Findry and Placely.',
                'legal.html', body)


# ========================================================== legal rendering ==
def legal_shell(path, title, description, app_name, doc_label, updated_line,
                body_html, toc, related, current='legal.html'):
    up = '../' if '/' in path else ''
    toc_html = ''
    if toc:
        items = '\n'.join(f'      <li><a href="#{i}">{e(t)}</a></li>' for i, t in toc)
        toc_html = f'''  <details class="legal-toc">
    <summary>On this page</summary>
    <ol>
{items}
    </ol>
  </details>
'''
    related_html = ''
    if related:
        related_html = '<div class="legal-footer-links">' + ''.join(related) + '</div>'

    body = f'''<main id="main" class="legal-main">
  <div class="shell">
    <a class="backlink" href="{up}legal.html">All legal documents</a>

    <div class="legal-head rise">
      <p class="eyebrow">{e(doc_label)}</p>
      <h1>{e(title.split(' — ')[0])}</h1>
      <p class="updated">{updated_line}</p>
    </div>

{toc_html}
    <div class="legal-body">
{body_html}
    </div>

    {related_html}
  </div>
</main>
'''
    return page(path, title, description, current, body)


def build_findry_legal():
    """Findry's documents carry wording copied verbatim from findryapp.com.
    They are re-emitted from the committed files, never re-derived, so the
    verbatim text and its effective date survive regeneration untouched."""
    written = []
    for path, title, label, desc in [
        ('findry/privacy.html', 'Findry Privacy Policy — Kaymer LLC', 'Findry legal',
         'The Findry privacy policy: what the app collects, how it is used and stored, and how to delete your account. Effective August 02, 2026.'),
        ('findry/terms.html', 'Findry Terms of Service — Kaymer LLC', 'Findry legal',
         'The Findry terms of service, covering accounts, the free plan and Findry Pro, subscriptions, and safety. Effective August 02, 2026.'),
    ]:
        body_html, effective = read_approved_legal(path)
        # These documents were emitted from plain text, so their contents list
        # is built from the unescaped heading; legal_shell escapes it once.
        heads = [html.unescape(re.sub(r'<[^>]+>', '', t))
                 for t in re.findall(r'<h2 id="[^"]*">(.*?)</h2>', body_html)]
        toc = [(f's-{slugify(t)}', t) for t in heads]
        other = 'terms.html' if path.endswith('privacy.html') else 'privacy.html'
        other_label = 'Findry Terms of Service' if path.endswith('privacy.html') else 'Findry Privacy Policy'
        related = [
            f'<a href="{other}">{other_label}</a>',
            '<a href="../apps/findry.html">About Findry</a>',
            '<a href="../contact.html">Findry support</a>',
        ]
        written.append(legal_shell(path, title, desc, 'Findry', label, effective,
                                   body_html, toc, related))
    return written


LEGACY = {
    'privacy.html': {
        'title': 'Privacy Policy — Kaymer LLC',
        'label': 'Kaymer LLC legal',
        'desc': 'The privacy policy for the Kaymer LLC website.',
        'related': ['<a href="terms.html">Terms of Service</a>',
                    '<a href="legal.html">All legal documents</a>'],
    },
    'terms.html': {
        'title': 'Terms of Service — Kaymer LLC',
        'label': 'Kaymer LLC legal',
        'desc': 'The terms of service for the Kaymer LLC website.',
        'related': ['<a href="privacy.html">Privacy Policy</a>',
                    '<a href="legal.html">All legal documents</a>'],
    },
    'placely-privacy.html': {
        'title': 'Placely Privacy Policy — Kaymer LLC',
        'label': 'Placely legal',
        'desc': 'The Placely privacy policy: account data, saved places, location, photos, storage, and account deletion.',
        'related': ['<a href="placely-terms.html">Placely Terms of Use</a>',
                    '<a href="placely-support.html">Placely Support</a>',
                    '<a href="apps/placely.html">About Placely</a>'],
    },
    'placely-terms.html': {
        'title': 'Placely Terms of Use — Kaymer LLC',
        'label': 'Placely legal',
        'desc': 'The Placely terms of use, covering accounts, user content, acceptable use, and account deletion.',
        'related': ['<a href="placely-privacy.html">Placely Privacy Policy</a>',
                    '<a href="placely-support.html">Placely Support</a>',
                    '<a href="apps/placely.html">About Placely</a>'],
    },
    'placely-support.html': {
        'title': 'Placely Support — Kaymer LLC',
        'label': 'Placely support',
        'desc': 'Help topics for Placely: account and sign-in, saving places, location and photos, and account deletion.',
        'related': ['<a href="placely-privacy.html">Placely Privacy Policy</a>',
                    '<a href="placely-terms.html">Placely Terms of Use</a>',
                    '<a href="contact.html">Contact support</a>'],
        'current': 'contact.html',
    },
}


def read_approved_legal(path):
    """Return (body_html, updated_line) from a document already in the current
    shell. This is the source of truth: whatever wording is committed is what
    gets re-emitted."""
    src = open(os.path.join(ROOT, path), encoding='utf-8').read()
    body = re.search(r'(?s)<div class="legal-body">\n(.*?)\n    </div>', src).group(1)
    updated = re.search(r'(?s)<p class="updated">(.*?)</p>', src).group(1).strip()
    return body, updated


def legal_date_note(path, prefix):
    """The date line shown for a document on the legal index, read from the
    document itself so the index can never disagree with it."""
    _, updated = read_approved_legal(path)
    plain = re.sub(r'<[^>]+>', '', updated)
    plain = plain.replace('&middot;', '\u00b7')
    m = re.search(r'((?:Last updated|Effective Date)[:]?\s*[A-Z][a-z]+ \d{1,2}, \d{4})', plain)
    date = m.group(1).replace('Effective Date:', 'Effective').replace('Last updated:', 'Last updated')
    return f'{prefix} {date}.' if prefix else f'{date}.'


def rebuild_legacy(path):
    """Re-emit a legal or support document into the shared shell, taking its
    wording and its date from the current approved file."""
    cfg = LEGACY[path]
    body_html, updated_line = read_approved_legal(path)

    toc = [(f's-{slugify(re.sub(r"<[^>]+>", "", t))}', re.sub(r'<[^>]+>', '', t))
           for t in re.findall(r'<h2 id="[^"]*">(.*?)</h2>', body_html)]

    return legal_shell(path, cfg['title'], cfg['desc'], None, cfg['label'],
                       updated_line, body_html, toc, cfg['related'],
                       current=cfg.get('current', 'legal.html'))


# ================================================================== extras ===
def build_extras(pages):
    with open(os.path.join(ROOT, '.nojekyll'), 'w') as fh:
        fh.write('')

    with open(os.path.join(ROOT, 'robots.txt'), 'w') as fh:
        fh.write('User-agent: *\nAllow: /\n\nSitemap: {}sitemap.xml\n'.format(SITE))

    urls = '\n'.join(
        '  <url>\n    <loc>{}{}</loc>\n  </url>'.format(SITE, '' if p == 'index.html' else p)
        for p in pages)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 f'{urls}\n</urlset>\n')


def main():
    pages = []
    pages.append(build_home())
    pages.append(build_apps())
    for a in APPS:
        pages.append(build_app_page(a))
    pages.append(build_about())
    pages.append(build_support())
    pages.append(build_legal_index())
    pages.extend(build_findry_legal())
    for p in LEGACY:
        pages.append(rebuild_legacy(p))

    build_extras(pages)

    print('generated {} pages:'.format(len(pages)))
    for p in pages:
        print('  ', p)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', help='repository root to read from and write to')
    args = ap.parse_args()
    if args.root:
        ROOT = os.path.abspath(args.root)
    main()
