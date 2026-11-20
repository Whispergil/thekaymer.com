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
from urllib.parse import urljoin, urlsplit, urlunsplit

# Repository root. Defaults to the directory containing tools/, so the script
# runs from a checkout anywhere; --root points it at an isolated copy for
# dry-run comparisons.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://thekaymer.com/'
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
        'short': 'Jobsite documentation for contractors and field crews. Save photos, depths, '
                 'measurements, buried utility details, and notes by project.',
        'long': 'Findry is a jobsite record and field documentation app for contractors, '
                'utility crews, excavators, plumbers, electricians, municipalities, and '
                'inspectors. Document buried pipes and utility installations with photos, '
                'depths, measurements, materials, valves, reference points, and field notes. '
                'Every record belongs to a project, so important details are easier to find '
                'when you return to a job days, months, or years later.',
        'icon': 'assets/img/findry-icon.png',
        'icon_webp': 'assets/img/findry-icon.webp',
        'platform': 'iPhone (iOS 16.4 or later) and Android (7.0 or later)',
        'store_name': 'Apple App Store and Google Play',
        'store_url': 'https://apps.apple.com/us/app/findry/id6773192473',
        'play_url': 'https://play.google.com/store/apps/details?id=com.whisper92.findry',
        'operating_system': 'iOS 16.4 or later; Android 7.0 or later',
        'price': 'Free, with an optional Findry Pro subscription',
        'category': 'Productivity and tools',
        'released': 'iPhone: August 15, 2026; Android: September 18, 2026',
        'privacy': 'findry/privacy.html',
        'terms': 'findry/terms.html',
        'shots': [
            ('assets/img/findry-screenshot-1', 'Findry app store screenshot: the Lookup screen, showing emergency lookup shortcuts and recently added records.'),
            ('assets/img/findry-screenshot-2', 'Findry app store screenshot: a record showing the depth and location of a buried utility.'),
            ('assets/img/findry-screenshot-3', 'Findry app store screenshot: the project list, with each project showing its saved record count.'),
        ],
        'detail_shots': [
            ('assets/img/findry/findry-home.webp',
             'Findry home screen with a work overview, the Material Calculator, the Truck Load Calculator, and a list of projects.'),
            ('assets/img/findry/findry-projects.webp',
             'Findry projects screen listing jobsite projects with their records and photos.'),
            ('assets/img/findry/findry-records.webp',
             'A Findry project screen showing notes, contact details, and a recent record with a depth measurement.'),
        ],
        'features': [
            ('Document buried pipes and utilities', 'Save photos, depths, measurements, pipe sizes, materials, valve locations, reference points, warnings, and field notes after installation.'),
            ('Keep jobsite records by project', 'Organise field information for residential repairs, commercial work, municipal utilities, and infrastructure projects instead of leaving it scattered across notebooks and camera rolls.'),
            ('Find field information later', 'Search by project, record title, utility type, keywords, notes, and locations when you return to a job — next week or years later.'),
        ],
        'safety_note': ('Findry stores information entered by its users. It does not detect, '
                        'verify, or professionally locate underground utilities, and it does '
                        'not replace 811 or local utility-marking requirements.'),
        'guides': [
            ('Material Calculator',
             'Calculate material volume in Imperial or Metric units, view an estimated material weight, and estimate truck trips from a capacity you enter. Saved calculations can be reopened from Calculator History.',
             '/apps/findry/material-calculator/',
             'See the Material Calculator'),
            ('Truck Load Calculator',
             'Estimate how many truck trips a material quantity may take from the quantity and the truck capacity you enter. Saved estimates can be reopened from Calculator History.',
             '/apps/findry/truck-load-calculator/',
             'See the Truck Load Calculator'),
            ('Underground utility records',
             'Document buried pipes and utility installations with photos, measurements, reference points, and field notes, kept with the project they belong to.',
             '/apps/findry/underground-utility-records/',
             'See underground utility records'),
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
        'icon': 'assets/img/nos-beleza-icon.png',
        'icon_webp': 'assets/img/nos-beleza-icon.webp',
        'platform': None,
        'privacy': 'nos-beleza/privacy.html',
        'terms': 'nos-beleza/terms.html',
        'support_page': 'nos-beleza/support.html',
        'features': [
            ('Discover local businesses', 'Browse businesses and the services they offer, filtered by island.'),
            ('Book an appointment', 'Request a booking, and let the business confirm, decline, or propose a new time.'),
            ('Built for more than beauty', 'The underlying marketplace is category-driven, so new kinds of local services can be added later.'),
        ],
    },
]
APP = {a['slug']: a for a in APPS}

NAV = [
    ('apps.html', 'Apps'),
    ('about.html', 'About'),
    ('contact.html', 'Support'),
]


def e(text):
    return html.escape(text, quote=False)


def slugify(text):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s or 'section'


def mailto(subject):
    return 'mailto:{}?subject={}'.format(EMAIL, subject.replace(' ', '%20').replace('ô', '%C3%B4'))


# ------------------------------------------------------------------- shell ---
def head(title, description, canonical, up, og_type='website', og_image=None, og_alt=None):
    p = up
    image = SITE + (og_image or 'assets/img/og-kaymer.jpg')
    image_alt = html.escape(og_alt or 'Kaymer LLC — practical apps, thoughtfully built.')
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
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{image_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{image}">
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


def app_route(app):
    return f"apps/{app['slug']}/"


def canonical_route(path):
    if path == 'index.html':
        return ''
    if path.endswith('/index.html'):
        return path[:-len('index.html')]
    return path[:-len('.html')] + '/' if path.endswith('.html') else path


def footer(up):
    app_links = '\n'.join(
        '        <li><a href="{}{}">{}</a></li>'.format(up, app_route(a), e(a['name']))
        for a in APPS)
    return f'''<footer class="site-footer">
  <div class="shell">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="wordmark" href="{up}index.html"><span>KAYMER</span></a>
        <p>Practical mobile products for real work and everyday life.</p>
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
      <span>United States</span>
    </div>
  </div>
</footer>
<script src="{up}assets/js/site.js" defer></script>
</body>
</html>
'''


def clean_links(markup, source_path):
    """Resolve local references against their original page before moving it.
    Root-relative links also make legal-body regeneration safe on later runs.
    External URLs and fragment-only links are preserved verbatim.
    """
    def replace(match):
        prefix, value, quote = match.groups()
        decoded = html.unescape(value)
        parsed = urlsplit(decoded)
        if not parsed.path or parsed.scheme or parsed.netloc:
            return match.group(0)
        resolved = urlsplit(urljoin(SITE + source_path, decoded))
        route = canonical_route(resolved.path.lstrip('/'))
        target = urlunsplit(('', '', '/' + route, resolved.query, resolved.fragment))
        return prefix + html.escape(target, quote=True) + quote
    return re.sub(r'((?:href|src|srcset)=["\'])([^"\']+)(["\'])', replace, markup)


def write_redirect(path, route, *, meta_refresh=False):
    target = '/' + route
    # GitHub Pages returns HTTP 200 for an existing HTML file, so it cannot
    # send a 301. An immediate meta refresh is the crawler-visible equivalent,
    # and it has to live outside <noscript> or non-JS crawlers still index the
    # stub as a second URL. Other aliases keep the original noscript refresh.
    refresh = f'<meta http-equiv="refresh" content="0; url={target}">\n' if meta_refresh else ''
    noscript = '' if meta_refresh else f'<noscript><meta http-equiv="refresh" content="0; url={target}"></noscript>\n'
    out = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page moved — Kaymer LLC</title>
<link rel="canonical" href="{SITE}{route}">
{refresh}<script>window.location.replace({json.dumps(target)} + window.location.search + window.location.hash);</script>
{noscript}</head>
<body><p>This page has moved. <a href="{target}">Continue to the page</a>.</p></body>
</html>
'''
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(out)


def page(path, title, description, current, body, structured=None, og_type='website', og_image=None, og_alt=None):
    up = '../' * path.count('/')
    canonical = canonical_route(path)
    out = head(title, description, canonical, up, og_type, og_image, og_alt)
    out += header(current, up)
    out += body
    page_footer = footer(up)
    out += page_footer
    if structured:
        out = out.replace('</head>', '<script type="application/ld+json">\n{}\n</script>\n</head>'.format(
            json.dumps(structured, indent=2, ensure_ascii=False)))
    # Also clean explicit /index.html URLs without redirecting normal visits.
    out = out.replace('</head>',
                      '<script>if (window.location.pathname.endsWith("/index.html")) { '
                      'window.location.replace(window.location.pathname.slice(0, -10) + '
                      'window.location.search + window.location.hash); }</script>\n</head>')
    out = clean_links(out, path)
    output_path = canonical + 'index.html'
    full = os.path.join(ROOT, output_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(out)
    if path != output_path:
        write_redirect(path, canonical)
    return output_path


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

PLAYSTORE_SVG = ('<svg width="16" height="18" viewBox="0 0 28.99 31.99" aria-hidden="true">'
                 '<path fill="#4285F4" d="M.12 2.66a3.57 3.57 0 0 0-.12.92v24.84a3.57 3.57 0 0 0 .12.92L14 15.64Z"/>'
                 '<path fill="#34A853" d="m13.64 16 6.94-6.85L5.5.51A3.73 3.73 0 0 0 3.63 0 3.64 3.64 0 0 0 .12 2.65Z"/>'
                 '<path fill="#FBBC04" d="m27.11 12.89-6.53-3.74-7.35 6.45 7.38 7.28 6.48-3.7a3.54 3.54 0 0 0 1.5-4.79 3.62 3.62 0 0 0-1.5-1.5z"/>'
                 '<path fill="#EA4335" d="M13.54 15.28.12 29.34a3.66 3.66 0 0 0 5.33 2.16l15.1-8.6Z"/>'
                 '</svg>')


def store_buttons(app, small=False):
    if app['status'] != 'available':
        return ''
    size = ' btn--sm' if small else ''
    buttons = [f'<a class="btn btn--appstore{size}" href="{app["store_url"]}">'
               f'{APPSTORE_SVG}<span>Download on the App Store</span></a>']
    if app.get('play_url'):
        buttons.append(f'<a class="btn btn--playstore{size}" href="{app["play_url"]}">'
                       f'{PLAYSTORE_SVG}<span>Get it on Google Play</span></a>')
    return '\n          '.join(buttons)


def shot(src, alt, up='', lazy=True, width=540, height=1168):
    loading = ' loading="lazy" decoding="async"' if lazy else ' decoding="async"'
    # Supplied screenshots are WebP only. Do not invent a JPEG stand-in.
    if src.endswith('.webp'):
        return (f'<picture>\n'
                f'          <img src="{up}{src}" width="{width}" height="{height}"{loading} alt="{e(alt)}">\n'
                f'        </picture>')
    return (f'<picture>\n'
            f'          <source srcset="{up}{src}.webp" type="image/webp">\n'
            f'          <img src="{up}{src}.jpg" width="{width}" height="{height}"{loading} alt="{e(alt)}">\n'
            f'        </picture>')


def shot_gallery(label, shots, up):
    """A sideways rail when there is more than one screenshot, so phone
    posters stay a readable size instead of stacking down the page."""
    frames = []
    for i, (src, alt) in enumerate(shots):
        frames.append('          ' + shot(src, alt, up=up, lazy=i > 0, width=1080, height=1920))
    rail = '\n'.join(frames)
    if len(shots) == 1:
        return f'''<figure class="shot-figure">
{rail}
        </figure>'''
    return f'''<div class="shot-rail-wrap">
          <div class="shot-rail" tabindex="0" role="group" aria-label="{e(label)}">
{rail}
          </div>
          <div class="shot-rail-ui">
            <button class="shot-nav shot-prev" type="button" aria-label="Previous screenshot" disabled>
              <span aria-hidden="true">&larr;</span>
            </button>
            <p class="shot-count" aria-live="polite"><span class="shot-index">1</span> of {len(shots)}</p>
            <button class="shot-nav shot-next" type="button" aria-label="Next screenshot">
              <span aria-hidden="true">&rarr;</span>
            </button>
          </div>
        </div>'''


# =============================================================== home page ===
def build_home():
    findry = APP['findry']
    others = [a for a in APPS if a['slug'] != 'findry']

    cards = []
    for i, a in enumerate(others):
        cards.append(f'''        <article class="app-card rise-in">
          {icon_markup(a)}
          <h3>{e(a['name'])}</h3>
          <div class="badge-row">{badge(a)}</div>
          <p>{e(a['short'])}</p>
          <div class="card-actions">
            <a class="btn btn--quiet" href="{app_route(a)}">About {e(a['name'])}</a>
          </div>
        </article>''')
    cards = '\n'.join(cards)

    hero_shot = shot(
        'assets/img/findry/findry-home.webp',
        'Findry home screen with the heading “YOUR JOBSITE. ALL IN ONE PLACE.”, the Material Calculator, the Truck Load Calculator, and a list of projects.',
        lazy=False,
        width=1080,
        height=1920,
    )

    body = f'''<main id="main">

  <section class="hero shell" aria-labelledby="hero-title">
    <div class="hero-split">

      <div class="hero-copy rise">
        <p class="eyebrow">PRACTICAL MOBILE PRODUCTS</p>
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
        <div class="btn-row btn-row--stores">
          {store_buttons(findry, small=True)}
          <a class="btn btn--quiet" href="apps/findry/">View Findry</a>
        </div>
      </div>

    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="more-apps">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">In the workshop</p>
        <h2 id="more-apps">What we are building next.</h2>
        <p class="lead">Nôs Beleza is in progress and is not released yet. It will get a store
          link when it is ready to launch.</p>
      </div>
      <div class="card-grid{' card-grid--solo' if len(others) == 1 else ''}">
{cards}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="values">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">How we work</p>
        <h2 id="values">Focused products. Practical purpose.</h2>
      </div>
      <div class="value-grid">
        <div class="value-item rise-in">
          <div class="rule"></div>
          <h3>Built around a real problem</h3>
          <p>Each app starts with a specific job someone actually has to do, not with a
            feature list.</p>
        </div>
        <div class="value-item rise-in">
          <div class="rule"></div>
          <h3>Only the data the app needs</h3>
          <p>What each app collects, and where it is stored, is written down in its own
            privacy policy in plain language.</p>
        </div>
        <div class="value-item rise-in">
          <div class="rule"></div>
          <h3>Answered by the people who built it</h3>
          <p>Questions and feedback go directly to the people who build and improve our apps.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="contact">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <h2 id="contact">Questions about an app?</h2>
          <p>Email Kaymer directly. We read everything that arrives.</p>
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
        "description": "Mobile app company based in the United States.",
        "email": EMAIL,
        "address": {"@type": "PostalAddress", "addressCountry": "US"},
    }
    return page('index.html',
                'Kaymer LLC — Practical Mobile Apps',
                'Kaymer LLC builds practical mobile apps for real work and everyday life, including Findry for iPhone and Android.',
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
        store = ''
        if a['status'] == 'available':
            store += '\n            <a class="btn btn--quiet" href="' + a['store_url'] + '">App Store</a>'
            if a.get('play_url'):
                store += '\n            <a class="btn btn--quiet" href="' + a['play_url'] + '">Google Play</a>'

        cards.append(f'''        <article class="app-card" data-status="{a['status']}">
          {icon_markup(a)}
          <h3>{e(a['name'])}</h3>
          <div class="badge-row">{badge(a)}</div>{meta}
          <p>{e(a['short'])}</p>
          <div class="card-actions">
            <a class="btn btn--secondary btn--sm" href="{app_route(a)}">View {e(a['name'])}</a>{store}{links_html}
          </div>
        </article>''')
    cards = '\n'.join(cards)

    body = f'''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="apps-title">
    <div class="rise">
      <p class="eyebrow">Our apps</p>
      <h1 id="apps-title">Tools built for real life.</h1>
      <div class="rule"></div>
      <p class="lead">Findry is available for iPhone and Android today. Nôs Beleza is in
        development. This page shows exactly where each app stands.</p>
    </div>
  </section>

  <section class="section section--flush-top" aria-labelledby="portfolio">
    <div class="shell">
      <h2 id="portfolio" class="visually-hidden">App portfolio</h2>

      <div class="filter-bar" role="group" aria-label="Filter apps by status" hidden>
        <button type="button" data-filter="all" aria-pressed="true">All</button>
        <button type="button" data-filter="available" aria-pressed="false">Available</button>
        <button type="button" data-filter="in-development" aria-pressed="false">In development</button>
      </div>
      <p id="filter-status" class="visually-hidden" role="status" aria-live="polite"></p>

      <div class="card-grid" id="app-list">
{cards}
      </div>
    </div>
  </section>

</main>
'''
    return page('apps.html', 'Apps — Kaymer LLC',
                'The Kaymer LLC app portfolio: Findry for iPhone and Android, plus Nôs Beleza in development.',
                'apps.html', body)


# ========================================================== app detail page ==
def build_app_page(a):
    path = 'apps/findry/index.html' if a['slug'] == 'findry' else f"apps/{a['slug']}.html"
    up = '../' * path.count('/')

    if a['status'] == 'available':
        actions = f'''<div class="btn-row btn-row--stores">
          {store_buttons(a)}
          <a class="btn btn--quiet" href="{mailto(a['name'] + ' Support')}">Get {e(a['name'])} Support</a>
        </div>'''
    else:
        actions = f'''<p class="note"><strong>{e(a['name'])} is not released yet.</strong>
          There is no download link, no store listing, no announced release date, and no
          finished screens to show. Rather than mock something up, this page waits for the
          real thing.</p>
        <div class="btn-row">
          <a class="btn btn--secondary" href="{mailto(a['name'] + ' Support')}">Contact Kaymer</a>
        </div>'''

    gallery = a.get('detail_shots') or a.get('shots')
    if gallery:
        aside = f'''
      <div class="rise rise-2">
        {shot_gallery(a['name'] + ' screenshots', gallery, up)}
      </div>'''
    else:
        aside = ''  

    features = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(t)}</h3>
          <p>{e(d)}</p>
        </div>''' for t, d in a['features'])

    safety_block = ''
    if a.get('safety_note'):
        safety_block = f'''\n      <p class="note" style="margin-top:var(--s-6)"><strong>Documentation, not utility detection.</strong> {e(a["safety_note"])}</p>'''
        if a['slug'] == 'findry':
            safety_block += ('\n      <p style="margin-top:var(--s-4)">New to keeping records? Read '
                             '<a href="/apps/findry/how-to-document-buried-utilities/">how to document buried utilities</a>.</p>')

    calc_links_block = ''
    if a['slug'] == 'findry':
        calc_links_block = '''  <section class="section section--flush-top" aria-labelledby="free-calculators">
    <div class="shell">
      <div class="section-head">
        <h2 id="free-calculators">Free Findry calculators</h2>
        <p class="lead">Use them free in your browser. No app download required.</p>
      </div>
      <div class="card-grid card-grid--three">
        <article class="app-card">
          <h3>Material Calculator</h3>
          <p>Estimate volume for gravel, stone, soil, and more.</p>
          <div class="card-actions">
            <a class="btn btn--secondary" href="/apps/findry/material-calculator/">Open the Material Calculator</a>
          </div>
        </article>
        <article class="app-card">
          <h3>Truck Load Calculator</h3>
          <p>Estimate cubic yards and how many trips a load may take.</p>
          <div class="card-actions">
            <a class="btn btn--secondary" href="/apps/findry/truck-load-calculator/">Open the Truck Load Calculator</a>
          </div>
        </article>
        <article class="app-card">
          <h3>Trench Backfill Calculator</h3>
          <p>Estimate backfill, tons, and truck trips for a trench and pipe.</p>
          <div class="card-actions">
            <a class="btn btn--secondary" href="/apps/findry/trench-backfill-calculator/">Open the Trench Calculator</a>
          </div>
        </article>
      </div>
    </div>
  </section>

'''

    guides = a.get('guides', [])
    if guides:
        guide_items = '\n'.join(
            f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(t)}</h3>
          <p>{e(d)}</p>
          <p><a href="{href}">{e(label)}</a></p>
        </div>''' for t, d, href, label in guides)
        guides_block = f'''  <section class="section" aria-labelledby="field-tools">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Included in Findry</p>
        <h2 id="field-tools">Calculators and field records.</h2>
        <p class="lead">The Material Calculator and Truck Load Calculator are included in Findry 1.0.2, available on iPhone and Android. Calculator results are estimates. They do not set legal payload, vehicle ratings, or safe hauling limits.</p>
      </div>
      <div class="feature-list">
{guide_items}
      </div>
    </div>
  </section>

'''
        details_class = 'section section--tinted'
    else:
        guides_block = ''
        details_class = 'section'

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

    # Findry only: decorative "record saved" animation beside the app icon
    # (self-hosted Lottie player; see assets/js/lottie-anim.js).
    hero_col_class = 'rise'
    hero_anim = ''
    hero_anim_script = ''
    if a['slug'] == 'findry':
        hero_col_class = 'rise records-anim-host'
        hero_anim = f'''
        <style>
          .app-hero .records-anim-host {{ position: relative; }}
          .app-hero .records-anim {{
            position: absolute;
            top: -0.5rem;
            right: 0;
            width: min(13.5rem, calc(100% - 84px - 2rem));
            max-width: 100%;
            aspect-ratio: 320 / 200;
            pointer-events: none;
          }}
          .app-hero .records-anim img,
          .app-hero .records-anim-stage {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
          .app-hero .records-anim-stage {{ visibility: hidden; }}
          .app-hero .records-anim.is-playing .records-anim-stage {{ visibility: visible; }}
          .app-hero .records-anim.is-playing img {{ visibility: hidden; }}
        </style>
        <div class="records-anim" data-lottie-anim data-player="{up}assets/js/lottie_light.min.js" data-src="{up}assets/animations/findry-records.json" aria-hidden="true">
          <img src="{up}assets/img/findry/findry-records-animation-still.svg" alt="" width="320" height="200" decoding="async">
          <div class="records-anim-stage" data-lottie-stage></div>
        </div>'''
        hero_anim_script = f'''
  <script src="{up}assets/js/lottie-anim.js" defer></script>'''

    structured = None
    if a['status'] == 'available':
        structured = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": a['name'],
            "applicationCategory": "BusinessApplication",
            "operatingSystem": a.get('operating_system', a.get('platform', '')),
            "url": SITE + app_route(a),
            "downloadUrl": [url for url in (a.get('store_url'), a.get('play_url')) if url],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="{up}apps.html">Back to Apps</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid{grid_mod}">
      <div class="{hero_col_class}">
        {icon_markup(a, up=up, large=True)}
        <div class="badge-row" style="margin-bottom:var(--s-3)">{badge(a)}</div>{hero_anim}
        <h1>{e(a['name'])}</h1>
        <p class="tagline">{e(a['tagline'])}</p>
        <p class="lead">{e(a['long'])}</p>
        {actions}
      </div>{aside}
    </div>
  </section>{hero_anim_script}

{calc_links_block}  <section class="section section--tinted" aria-labelledby="features">
    <div class="shell">
      <div class="section-head">
        <h2 id="features">What it does</h2>
      </div>
      <div class="feature-list">
{features}
      </div>{safety_block}
    </div>
  </section>

{guides_block}  <section class="{details_class}" aria-labelledby="details">
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
          <p>Email Kaymer and mention the app name.</p>
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
    title = f'{a["name"]} — Kaymer LLC'
    description = a['short']
    if a['slug'] == 'findry':
        title = 'Findry — Jobsite & Underground Utility Records'
        description = ('Document buried pipes, utility installations, depths, measurements, '
                       'photos, and field notes by project with Findry for iPhone and Android.')
    og_image = None
    og_alt = None
    if a['slug'] == 'findry':
        og_image = 'assets/img/og-findry.jpg'
        og_alt = 'Findry — save it now, find it later.'
    return page(path, title,
                description, 'apps.html', body, structured, og_type='article',
                og_image=og_image, og_alt=og_alt)


def _findry_tool_page(path, title, description, body, structured):
    return page(path, title, description, 'apps.html', body, structured, og_type='article',
                og_image='assets/img/og-findry.jpg',
                og_alt='Findry — save it now, find it later.')



# ============================================== Findry material calculator widget
def material_calculator_widget(up, store_html):
    """In-page Material Calculator markup, scoped CSS, and script tag.

    JS lives in assets/js/material-calculator.js (same math as the Findry
    1.0.2 app). The form stays hidden until that script runs, so the existing
    copy and store links remain usable if JavaScript is off.
    """
    script_src = f'{up}assets/js/material-calculator.js'
    material_options = '\n'.join(
        f'              <option value="{key}"{" selected" if key == "gravel" else ""}>{label}</option>'
        for key, label in (
            ('gravel', 'Gravel'),
            ('crushed-stone', 'Crushed Stone'),
            ('sand', 'Sand'),
            ('topsoil', 'Topsoil'),
            ('fill-dirt', 'Fill Dirt'),
            ('mulch', 'Mulch'),
            ('concrete', 'Concrete'),
            ('asphalt-millings', 'Asphalt Millings'),
        )
    )
    yard_options = '\n'.join(
        f'              <option value="{n}"{" selected" if n == 10 else ""}>{n} yd³</option>'
        for n in (5, 6, 8, 10, 12, 14, 16, 18, 20)
    )
    return (
        '  <section id="material-calc" class="section" aria-labelledby="material-calc-heading">\n'
        '    <style>\n'
        '      #material-calc .material-calc-card {\n'
        '        background: var(--ivory-lift);\n'
        '        border: 1px solid var(--border);\n'
        '        border-radius: var(--radius-lg);\n'
        '        box-shadow: var(--shadow-md);\n'
        '        padding: var(--s-5);\n'
        '        max-width: 36rem;\n'
        '      }\n'
        '      #material-calc .material-calc-card > * + * { margin-top: var(--s-4); }\n'
        '      #material-calc fieldset { border: 0; min-width: 0; }\n'
        '      #material-calc legend,\n'
        '      #material-calc .material-calc-label {\n'
        '        display: block;\n'
        '        font-weight: 600;\n'
        '        color: var(--charcoal);\n'
        '        margin-bottom: var(--s-2);\n'
        '      }\n'
        '      #material-calc .material-calc-hint {\n'
        '        color: var(--muted, #5c564c);\n'
        '        font-size: 0.92rem;\n'
        '        margin-top: var(--s-1);\n'
        '      }\n'
        '      #material-calc .material-calc-seg {\n'
        '        display: flex;\n'
        '        flex-wrap: wrap;\n'
        '        gap: var(--s-1);\n'
        '      }\n'
        '      #material-calc .material-calc-seg label {\n'
        '        flex: 1 1 8rem;\n'
        '        display: flex;\n'
        '        align-items: center;\n'
        '        justify-content: center;\n'
        '        min-height: 44px;\n'
        '        padding: 0 var(--s-3);\n'
        '        border: 1px solid var(--border-strong);\n'
        '        border-radius: var(--radius-sm);\n'
        '        background: var(--ivory);\n'
        '        color: var(--charcoal);\n'
        '        cursor: pointer;\n'
        '        text-align: center;\n'
        '      }\n'
        '      #material-calc .material-calc-seg label:has(input:checked) {\n'
        '        background: var(--charcoal);\n'
        '        color: var(--ivory);\n'
        '        border-color: var(--charcoal);\n'
        '      }\n'
        '      #material-calc .material-calc-seg input {\n'
        '        position: absolute;\n'
        '        width: 1px;\n'
        '        height: 1px;\n'
        '        padding: 0;\n'
        '        margin: -1px;\n'
        '        overflow: hidden;\n'
        '        clip: rect(0, 0, 0, 0);\n'
        '        white-space: nowrap;\n'
        '        border: 0;\n'
        '      }\n'
        '      #material-calc .material-calc-field input[type="text"],\n'
        '      #material-calc .material-calc-field select {\n'
        '        width: 100%;\n'
        '        min-height: 44px;\n'
        '        border: 1px solid var(--border-strong);\n'
        '        border-radius: var(--radius-sm);\n'
        '        background: var(--ivory);\n'
        '        color: var(--charcoal);\n'
        '        padding: 0.55rem 0.8rem;\n'
        '        font: inherit;\n'
        '      }\n'
        '      #material-calc .material-calc-input-row {\n'
        '        display: flex;\n'
        '        align-items: center;\n'
        '        border: 1px solid var(--border-strong);\n'
        '        border-radius: var(--radius-sm);\n'
        '        background: var(--ivory);\n'
        '        min-height: 44px;\n'
        '      }\n'
        '      #material-calc .material-calc-input-row input[type="text"] {\n'
        '        border: 0;\n'
        '        min-height: 42px;\n'
        '        background: transparent;\n'
        '        flex: 1;\n'
        '        width: auto;\n'
        '      }\n'
        '      #material-calc .material-calc-unit {\n'
        '        padding: 0 0.8rem;\n'
        '        color: var(--muted, #5c564c);\n'
        '        white-space: nowrap;\n'
        '      }\n'
        '      #material-calc .material-calc-dims {\n'
        '        display: grid;\n'
        '        gap: var(--s-3);\n'
        '      }\n'
        '      #material-calc .material-calc-error {\n'
        '        color: #8B2E1E;\n'
        '        font-size: 0.92rem;\n'
        '        min-height: 1.25em;\n'
        '        margin-top: var(--s-1);\n'
        '      }\n'
        '      #material-calc .material-calc-actions {\n'
        '        display: flex;\n'
        '        flex-wrap: wrap;\n'
        '        gap: var(--s-2);\n'
        '      }\n'
        '      #material-calc .material-calc-results {\n'
        '        border-top: 1px solid var(--border);\n'
        '        padding-top: var(--s-4);\n'
        '      }\n'
        '      #material-calc .material-calc-results[hidden],\n'
        '      #material-calc [hidden] { display: none; }\n'
        '      #material-calc .material-calc-context {\n'
        '        color: var(--muted, #5c564c);\n'
        '        margin-bottom: var(--s-3);\n'
        '      }\n'
        '      #material-calc .material-calc-kicker {\n'
        '        text-transform: uppercase;\n'
        '        letter-spacing: 0.04em;\n'
        '        font-size: 0.8rem;\n'
        '        font-weight: 700;\n'
        '        margin-bottom: var(--s-1);\n'
        '      }\n'
        '      #material-calc .material-calc-hero {\n'
        '        font-size: 2rem;\n'
        '        font-weight: 800;\n'
        '        line-height: 1.15;\n'
        '        margin: 0 0 var(--s-3);\n'
        '      }\n'
        '      #material-calc .material-calc-rows {\n'
        '        display: grid;\n'
        '        gap: var(--s-2);\n'
        '        margin: 0;\n'
        '      }\n'
        '      #material-calc .material-calc-rows > div {\n'
        '        display: flex;\n'
        '        justify-content: space-between;\n'
        '        gap: var(--s-3);\n'
        '        border-top: 1px solid var(--border);\n'
        '        padding-top: var(--s-2);\n'
        '      }\n'
        '      #material-calc .material-calc-rows dt { margin: 0; flex: 1; }\n'
        '      #material-calc .material-calc-rows dd { margin: 0; font-weight: 700; text-align: right; }\n'
        '      #material-calc .material-calc-measure {\n'
        '        margin-top: var(--s-4);\n'
        '      }\n'
        '      #material-calc .material-calc-measure dl {\n'
        '        display: grid;\n'
        '        gap: var(--s-1);\n'
        '        margin: 0;\n'
        '      }\n'
        '      #material-calc .material-calc-measure div {\n'
        '        display: flex;\n'
        '        justify-content: space-between;\n'
        '        gap: var(--s-3);\n'
        '      }\n'
        '      #material-calc .material-calc-measure dt { margin: 0; }\n'
        '      #material-calc .material-calc-measure dd { margin: 0; text-align: right; }\n'
        '      #material-calc .material-calc-safety {\n'
        '        margin-top: var(--s-3);\n'
        '        color: var(--muted, #5c564c);\n'
        '        font-size: 0.92rem;\n'
        '      }\n'
        '      #material-calc .material-calc-cta { margin-top: var(--s-6); }\n'
        '      #material-calc .material-calc-cta p {\n'
        '        margin-bottom: var(--s-3);\n'
        '      }\n'
        '      #material-calc .material-calc-status:empty { display: none; }\n'
        '    </style>\n'
        '    <div class="shell">\n'
        '      <div class="section-head">\n'
        '        <p class="eyebrow">On this page</p>\n'
        '        <h2 id="material-calc-heading">Estimate material volume here</h2>\n'
        '        <p class="lead">Use the same measurements, densities, and trip math as the Findry app. The default is Gravel, Imperial units, and a 10 yd³ truck. Trips are based on volume only, and this calculator does not add a waste or compaction allowance.</p>\n'
        '      </div>\n'
        '      <noscript>\n'
        '        <p class="note">This on-page calculator needs JavaScript. The formula and examples below still work, and you can get the same tool in the Findry app.</p>\n'
        '      </noscript>\n'
        '      <form class="material-calc-card" data-material-form hidden novalidate>\n'
        '        <div class="material-calc-field">\n'
        '          <label class="material-calc-label" for="material-calc-material">Material</label>\n'
        '          <select id="material-calc-material" name="material">\n'
        f'{material_options}\n'
        '          </select>\n'
        '        </div>\n'
        '        <fieldset>\n'
        '          <legend>Truck capacity</legend>\n'
        '          <div class="material-calc-seg">\n'
        '            <label>\n'
        '              <input type="radio" name="material-calc-capacity-unit" value="cubic-yards" checked>\n'
        '              Cubic Yards\n'
        '            </label>\n'
        '            <label>\n'
        '              <input type="radio" name="material-calc-capacity-unit" value="cubic-metres">\n'
        '              Cubic Metres\n'
        '            </label>\n'
        '          </div>\n'
        '        </fieldset>\n'
        '        <div class="material-calc-field" data-capacity-presets>\n'
        '          <label class="material-calc-label" for="material-calc-capacity-preset">Truck capacity (yd³)</label>\n'
        '          <select id="material-calc-capacity-preset" name="capacity-preset" aria-describedby="material-calc-capacity-error">\n'
        f'{yard_options}\n'
        '              <option value="custom">Custom</option>\n'
        '          </select>\n'
        '        </div>\n'
        '        <div class="material-calc-field" data-capacity-entry hidden>\n'
        '          <label class="material-calc-label" for="material-calc-capacity" data-capacity-entry-label>Custom truck capacity (yd³)</label>\n'
        '          <div class="material-calc-input-row">\n'
        '            <input id="material-calc-capacity" name="capacity" type="text" inputmode="decimal" maxlength="12" autocomplete="off" spellcheck="false" placeholder="e.g. 24" aria-describedby="material-calc-capacity-error">\n'
        '            <span class="material-calc-unit" data-capacity-entry-unit>yd³</span>\n'
        '          </div>\n'
        "          <p class=\"material-calc-hint\" data-capacity-hint hidden>Enter your truck's capacity in cubic metres.</p>\n"
        '        </div>\n'
        '        <p id="material-calc-capacity-error" class="material-calc-error" role="alert"></p>\n'
        '        <fieldset>\n'
        '          <legend>Dimension units</legend>\n'
        '          <div class="material-calc-seg">\n'
        '            <label>\n'
        '              <input type="radio" name="material-calc-units" value="imperial" checked>\n'
        '              Imperial\n'
        '            </label>\n'
        '            <label>\n'
        '              <input type="radio" name="material-calc-units" value="metric">\n'
        '              Metric\n'
        '            </label>\n'
        '          </div>\n'
        '          <p class="material-calc-hint">Changing units clears entered measurements.</p>\n'
        '        </fieldset>\n'
        '        <fieldset>\n'
        '          <legend>Measurements</legend>\n'
        '          <div class="material-calc-dims">\n'
        '            <div class="material-calc-field">\n'
        '              <label class="material-calc-label" for="material-calc-length">Length</label>\n'
        '              <div class="material-calc-input-row">\n'
        '                <input id="material-calc-length" name="length" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="e.g. 40" aria-describedby="material-calc-length-error">\n'
        '                <span class="material-calc-unit" data-length-unit>ft</span>\n'
        '              </div>\n'
        '              <p id="material-calc-length-error" class="material-calc-error" role="alert"></p>\n'
        '            </div>\n'
        '            <div class="material-calc-field">\n'
        '              <label class="material-calc-label" for="material-calc-width">Width</label>\n'
        '              <div class="material-calc-input-row">\n'
        '                <input id="material-calc-width" name="width" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="e.g. 20" aria-describedby="material-calc-width-error">\n'
        '                <span class="material-calc-unit" data-width-unit>ft</span>\n'
        '              </div>\n'
        '              <p id="material-calc-width-error" class="material-calc-error" role="alert"></p>\n'
        '            </div>\n'
        '            <div class="material-calc-field">\n'
        '              <label class="material-calc-label" for="material-calc-depth">Depth</label>\n'
        '              <div class="material-calc-input-row">\n'
        '                <input id="material-calc-depth" name="depth" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="e.g. 6" aria-describedby="material-calc-depth-error">\n'
        '                <span class="material-calc-unit" data-depth-unit>in</span>\n'
        '              </div>\n'
        '              <p id="material-calc-depth-error" class="material-calc-error" role="alert"></p>\n'
        '            </div>\n'
        '          </div>\n'
        '        </fieldset>\n'
        '        <div class="material-calc-actions">\n'
        '          <button type="submit" class="btn">Calculate</button>\n'
        '          <button type="button" class="btn btn--secondary" data-material-reset>Reset</button>\n'
        '        </div>\n'
        '        <div class="material-calc-results" data-material-results hidden aria-live="polite">\n'
        '          <p class="material-calc-context" data-result-context></p>\n'
        '          <p class="material-calc-kicker" data-result-hero-label>Cubic yards</p>\n'
        '          <p class="material-calc-hero" data-result-hero></p>\n'
        '          <dl class="material-calc-rows">\n'
        '            <div><dt data-result-secondary-label>Cubic Metres</dt><dd data-result-secondary></dd></div>\n'
        '            <div><dt data-result-mass-label>Estimated US Short Tons</dt><dd data-result-mass></dd></div>\n'
        '            <div><dt>Load Equivalent by Volume</dt><dd data-result-loads></dd></div>\n'
        '            <div><dt>Estimated Trips by Volume</dt><dd data-result-trips></dd></div>\n'
        '          </dl>\n'
        '          <div class="material-calc-measure">\n'
        '            <p class="material-calc-kicker">Measurements</p>\n'
        '            <dl data-result-measurements></dl>\n'
        '          </div>\n'
        '          <p class="material-calc-safety" data-result-safety></p>\n'
        '          <div class="material-calc-actions" style="margin-top:var(--s-4)">\n'
        '            <button type="button" class="btn btn--secondary" data-material-edit>Edit Measurements</button>\n'
        '            <button type="button" class="btn btn--secondary" data-material-reset>Start New Calculation</button>\n'
        '          </div>\n'
        '        </div>\n'
        '        <p class="note material-calc-status" data-material-status role="status" aria-live="polite"></p>\n'
        '      </form>\n'
        '      <div class="material-calc-cta">\n'
        '        <p>Get the same calculator in the Findry app, along with Calculator History and the rest of your field tools.</p>\n'
        '        <div class="btn-row btn-row--stores">\n'
        '          ' + store_html + '\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>\n'
        f'    <script src="{script_src}" defer></script>\n'
        '  </section>\n'
    )


# =============================================== Findry material calculator ===
def build_findry_material_calculator():
    a = APP['findry']
    path = 'apps/findry/material-calculator/index.html'
    up = '../' * path.count('/')
    title = 'Gravel, Sand & Material Calculator (Yards & Tons) | Findry'
    description = ('Estimate cubic yards, tons, and truck trips for gravel, sand, topsoil, '
                   'fill dirt, mulch, concrete, and more. Free Findry app for iPhone and Android.')
    gallery = shot_gallery('Material Calculator screenshots', [
        ('assets/img/findry/findry-material-calculator-input.webp',
         'Material Calculator screen for entering measurements, a material, and truck capacity.'),
        ('assets/img/findry/findry-material-calculator-results.webp',
         'Material Calculator estimate showing volume, weight, and truck trips from the measurements entered.'),
    ], up)
    # Visible FAQ and FAQPage JSON-LD are built from the same strings.
    faqs = [
        ('How do I calculate cubic yards of material?',
         'Multiply length in feet by width in feet by depth in feet, then divide by 27. '
         'If your depth is in inches, divide it by 12 first. For example, 150 ft × 55 ft × 3 in '
         'is 150 × 55 × 0.25 = 2,062.5 cubic feet, or about 76.39 cubic yards.'),
        ('How much gravel, sand, or topsoil do I need?',
         'Measure the length, width, and finished depth of the area and work out the cubic yards. '
         'Then convert to tons if your supplier sells by weight. Findry’s Material Calculator does '
         'both for gravel, crushed stone, sand, topsoil, fill dirt, mulch, concrete, and asphalt '
         'millings. Confirm the final quantity with your supplier.'),
        ('How does Findry estimate tons of material?',
         'Findry applies a built-in weight for the material you choose to the calculated volume and '
         'shows the result in US short tons. It is an estimate. Actual weight depends on the exact '
         'product, moisture, and supplier, so check with your supplier before ordering by the ton.'),
        ('How many truck loads will I need?',
         'Divide the cubic yards by your truck’s capacity in cubic yards, then round up to a whole '
         'number of trips. In Findry you can pick a truck size from 5 to 20 cubic yards or enter a '
         'custom capacity, and it shows both the load equivalent and the estimated trips. Results '
         'are estimates and do not set legal payload or safe hauling limits.'),
        ('Does the calculator add extra for waste or compaction?',
         'No. The Material Calculator uses exactly the measurements you enter. If your job needs '
         'extra material for waste, compaction, or uneven ground, ask your supplier or engineer '
         'how much to add.'),
        ('Is the Material Calculator free, and what phones does it work on?',
         'Yes. The Material Calculator and the Truck Load Calculator are completely free for all '
         'users, on both the free plan and Findry Pro, and no subscription is needed. Findry is '
         'free to download for iPhone (iOS 16.4 or later) and Android (7.0 or later). You can save '
         'calculations to Calculator History and reopen them later.'),
    ]
    faq_items = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(question)}</h3>
          <p>{e(answer)}</p>
        </div>'''
        for question, answer in faqs)
    faq_ld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer},
            }
            for question, answer in faqs
        ],
    }, indent=2, ensure_ascii=False)

    widget = material_calculator_widget(up, store_buttons(a))

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="/apps/findry/">Back to Findry</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <p class="eyebrow">Findry field tools</p>
        <h1>Material Calculator for Gravel, Sand, Topsoil, and More</h1>
        <p class="tagline">Estimate material quantities from jobsite measurements.</p>
        <p class="lead">Findry’s Material Calculator helps contractors and field crews estimate
          material volume, weight, and volume-based truck trips from jobsite measurements. Enter
          the length, width, and depth, pick a material and a truck capacity, and Findry shows
          cubic yards, cubic metres, estimated weight, and how many truck trips the job may take.
          The default material is Gravel, measurements start in Imperial (feet and inches), and
          the default truck capacity is 10 yd³. In Metric, length and width are in metres and
          depth is in centimetres. Imperial results show estimated US short tons; Metric results
          show estimated metric tonnes. Trips are based on volume only, and the calculator does
          not add a waste or compaction allowance. The Material Calculator is part of the Findry
          app for iPhone and Android, and it is free for all users. You can also run the same
          estimate in the calculator on this page.</p>
        <div class="btn-row btn-row--stores">
          {store_buttons(a)}
        </div>
      </div>
      <div class="rise rise-2">
        {gallery}
      </div>
    </div>
  </section>

  {widget}

  <section class="section section--tinted" aria-labelledby="material-features">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Construction material estimates</p>
        <h2 id="material-features">From measurements to a usable field estimate.</h2>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Calculate material volume</h3>
          <p>Enter project measurements and calculate material volume using Imperial or Metric units.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>View estimated material weight</h3>
          <p>Use the selected material and calculated quantity to view an estimated material weight.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Estimate truck trips</h3>
          <p>Enter a truck capacity to estimate how many trips may be needed for the calculated quantity.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="materials">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Materials</p>
        <h2 id="materials">Materials included in the calculator</h2>
        <p class="lead">Choose one of eight common jobsite and landscape materials. Findry applies a built-in weight for each material to estimate tons.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Gravel</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Crushed Stone</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Sand</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Topsoil</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Fill Dirt</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Mulch</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Concrete</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Asphalt Millings</h3>
        </div>
      </div>
      <div class="prose" style="margin-top:var(--s-6)">
        <p>Weights are estimates. The actual weight of a load depends on the exact product, moisture, and supplier, so check with your supplier before you order by the ton.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="how-to">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Step by step</p>
        <h2 id="how-to">How to use the Material Calculator</h2>
        <p class="lead">Open Findry and tap Material Calculator on the Home screen. A typical estimate takes five steps.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 1: Choose the material</h3>
          <p>Pick Gravel, Crushed Stone, Sand, Topsoil, Fill Dirt, Mulch, Concrete, or Asphalt Millings. The default is Gravel. The material you choose sets the estimated weight.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 2: Choose a truck capacity</h3>
          <p>Work in cubic yards or cubic metres. For cubic yards, pick a common truck size from 5 to 20 yd³, or enter a custom capacity for your own truck, such as 24 yd³.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 3: Pick Imperial or Metric</h3>
          <p>Choose your measurement units before you type anything. Changing units clears the measurements you have already entered.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 4: Enter length, width, and depth</h3>
          <p>In Imperial, enter length and width in feet and depth in inches. In Metric, enter length and width in metres and depth in centimetres. Measure the area you need to fill or cover, and use the depth of the finished layer.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 5: Calculate, then save or adjust</h3>
          <p>Tap Calculate to see cubic yards, cubic metres, estimated weight, the load equivalent, and the estimated number of trips. Imperial measurements show US short tons; Metric measurements show metric tonnes. Use Edit Measurements to change a number, Reset or Start New Calculation to clear the measurements (material and truck capacity stay the same), or save the result to Calculator History in the app to reopen it later. You can also run the same estimate in the calculator on this page.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="formula">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">The formula</p>
        <h2 id="formula">How to calculate cubic yards and tons of material</h2>
        <p class="lead">The Material Calculator uses the same math you would do by hand. Here it is in plain words, so you can check any estimate.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Volume in cubic yards</h3>
          <p>Multiply length (ft) × width (ft) × depth (ft) to get cubic feet. Depth is usually measured in inches, so divide inches by 12 first. Then divide cubic feet by 27, because one cubic yard is 3 ft × 3 ft × 3 ft = 27 cubic feet.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Cubic metres</h3>
          <p>Findry converts cubic feet to cubic metres using 35.314666721 cubic feet per cubic metre, so one cubic yard is about 0.7646 cubic metres. The result is shown in m³.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Estimated weight in tons</h3>
          <p>Findry applies a built-in weight for the material you selected. With Imperial measurements, it shows estimated US short tons (2,000 lb). With Metric measurements, it shows estimated metric tonnes. Gravel, sand, topsoil, mulch, and the other materials all weigh different amounts, and real weights vary by product and moisture. Check with your supplier before you order by the ton.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Truck loads and trips</h3>
          <p>The load equivalent is the volume divided by your truck’s capacity. Trips is that number rounded up to whole trucks, because a partly full truck still makes a trip. Trips are based on volume only, not on weight.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="example-crushed-stone">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="example-crushed-stone">Example: crushed stone for a 150 ft × 55 ft lot</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example using the same numbers as the app screenshot on this page.)</p>
        <p>A crew needs a 3-inch layer of crushed stone over an area 150 ft long and 55 ft wide, using a 20 yd³ truck.</p>
        <ul>
          <li><strong>Cubic feet:</strong> 150 × 55 × (3 ÷ 12) = 2,062.5 ft³</li>
          <li><strong>Cubic yards:</strong> 2,062.5 ÷ 27 = <strong>76.39 yd³</strong></li>
          <li><strong>Cubic metres:</strong> <strong>58.4 m³</strong></li>
          <li><strong>Estimated weight:</strong> the app estimates <strong>114.58 US short tons</strong> for crushed stone</li>
          <li><strong>Loads:</strong> 76.39 ÷ 20 = <strong>3.82 loads</strong>, so <strong>4 trips</strong></li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="example-gravel">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="example-gravel">Example: gravel for an 80 ft × 40 ft pad</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example with made-up sample values.)</p>
        <p>A contractor is placing a 4-inch layer of gravel on an 80 ft × 40 ft pad and has a 10 yd³ truck.</p>
        <ul>
          <li><strong>Cubic feet:</strong> 80 × 40 × (4 ÷ 12) = 1,066.67 ft³</li>
          <li><strong>Cubic yards:</strong> 1,066.67 ÷ 27 = <strong>39.51 yd³</strong></li>
          <li><strong>Cubic metres:</strong> <strong>30.2 m³</strong></li>
          <li><strong>Loads:</strong> 39.51 ÷ 10 = <strong>3.95 loads</strong>, so <strong>4 trips</strong></li>
          <li><strong>Weight:</strong> <strong>55.31 US short tons</strong> for gravel. Confirm the weight with your supplier.</li>
          <li><strong>Custom truck:</strong> with a 24 yd³ truck entered as a custom capacity, the same pad is 39.51 ÷ 24 = <strong>1.65 loads</strong>, so <strong>2 trips</strong>.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="order-tips">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Before you order</p>
        <h2 id="order-tips">Tips before you order gravel, soil, or fill</h2>
      </div>
      <div class="prose">
        <ul>
          <li><strong>Measure the finished depth.</strong> Use the depth of the layer after it is placed and compacted, not the loose pile.</li>
          <li><strong>Break odd shapes into rectangles.</strong> Run one calculation per rectangle, save each to Calculator History, and add the yards together.</li>
          <li><strong>Plan for extra.</strong> The calculator uses exactly the measurements you enter and doesn’t add a waste or compaction allowance. Fill dirt, topsoil, and base materials often settle, so ask your supplier or engineer how much extra to order for your job.</li>
          <li><strong>Ask how it’s sold.</strong> Some suppliers sell by the cubic yard and others by the ton. Findry shows both, so you can compare against the quote.</li>
          <li><strong>Confirm weight and truck limits.</strong> Trips are based on volume. Legal hauling limits depend on the vehicle and the load weight, so check them before you rely on an estimate.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="history">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Calculator History</p>
        <h2 id="history">Save a calculation and come back to it.</h2>
        <p class="lead">Completed calculations can be saved to Calculator History and reopened
          later, making it easier to reuse field estimates without starting over.</p>
      </div>
      <p class="note"><strong>Estimates only.</strong> Calculator results are estimates. Findry
        does not determine legal payload, vehicle ratings, axle compliance, or safe hauling
        capacity. Verify project requirements and hauling limits before relying on an estimate.</p>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="material-faq">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">FAQ</p>
        <h2 id="material-faq">Material calculator FAQ</h2>
      </div>
      <div class="feature-list">
{faq_items}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="findry-material">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <p class="eyebrow">Part of Findry</p>
          <h2 id="findry-material">Keep the estimate with the rest of your field workflow.</h2>
          <p>Findry combines field calculators with project records, measurements, photos,
            reference points, notes, search, and jobsite documentation.</p>
          <p>Already know your quantity? Use the <a href="/apps/findry/truck-load-calculator/">Truck Load Calculator</a> to estimate trips. And keep <a href="/apps/findry/underground-utility-records/">underground utility records</a> for the same project.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--secondary" href="/apps/findry/">Explore Findry</a>
        </div>
      </div>
    </div>
  </section>

  <script type="application/ld+json">
{faq_ld}
  </script>

</main>
'''

    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": SITE + "apps/findry/material-calculator/",
        "description": description,
        "about": {
            "@type": "SoftwareApplication",
            "name": "Findry",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": a.get('operating_system', a.get('platform', '')),
            "url": SITE + app_route(a),
            "downloadUrl": [url for url in (a.get('store_url'), a.get('play_url')) if url],
            "featureList": [
                "Material volume estimates",
                "Estimated material weight",
                "Estimated truck trips",
                "Calculator History",
                "Gravel, crushed stone, sand, topsoil, fill dirt, mulch, concrete, and asphalt millings",
                "Preset and custom truck capacities",
            ],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
    }

    return _findry_tool_page(path, title, description, body, structured)


# ============================================== Findry truck load calculator ===
def truck_load_calculator_widget(up, store_html):
    """In-page Truck Load Calculator markup, scoped CSS, and script tag.

    JS lives in assets/js/truck-load-calculator.js (same math as the Findry
    1.0.2 app). The form stays hidden until that script runs, so the existing
    copy and store links remain usable if JavaScript is off.
    """
    script_src = f'{up}assets/js/truck-load-calculator.js'
    # Decorative loading animation (self-hosted Lottie player; see assets/js/lottie-anim.js).
    anim_script_src = f'{up}assets/js/lottie-anim.js'
    anim_player_src = f'{up}assets/js/lottie_light.min.js'
    anim_json_src = f'{up}assets/animations/truck-load.json'
    anim_still_src = f'{up}assets/img/findry/truck-load-animation-still.svg'
    yard_options = '\n'.join(
        f'              <option value="{n}"{" selected" if n == 10 else ""}>{n} yd³</option>'
        for n in (5, 6, 8, 10, 12, 14, 16, 18, 20)
    )
    return (
        '  <section id="truck-calc" class="section" aria-labelledby="truck-calc-heading">\n'
        '    <style>\n'
        '      #truck-calc .truck-calc-card {\n'
        '        background: var(--ivory-lift);\n'
        '        border: 1px solid var(--border);\n'
        '        border-radius: var(--radius-lg);\n'
        '        box-shadow: var(--shadow-md);\n'
        '        padding: var(--s-5);\n'
        '        max-width: 36rem;\n'
        '      }\n'
        '      #truck-calc .truck-calc-card > * + * { margin-top: var(--s-4); }\n'
        '      #truck-calc fieldset { border: 0; min-width: 0; }\n'
        '      #truck-calc legend,\n'
        '      #truck-calc .truck-calc-label {\n'
        '        display: block;\n'
        '        font-weight: 600;\n'
        '        color: var(--charcoal);\n'
        '        margin-bottom: var(--s-2);\n'
        '      }\n'
        '      #truck-calc .truck-calc-seg {\n'
        '        display: flex;\n'
        '        flex-wrap: wrap;\n'
        '        gap: var(--s-1);\n'
        '      }\n'
        '      #truck-calc .truck-calc-seg label {\n'
        '        flex: 1 1 8rem;\n'
        '        display: flex;\n'
        '        align-items: center;\n'
        '        justify-content: center;\n'
        '        min-height: 44px;\n'
        '        padding: 0 var(--s-3);\n'
        '        border: 1px solid var(--border-strong);\n'
        '        border-radius: var(--radius-sm);\n'
        '        background: var(--ivory);\n'
        '        color: var(--charcoal);\n'
        '        cursor: pointer;\n'
        '        text-align: center;\n'
        '      }\n'
        '      #truck-calc .truck-calc-seg label:has(input:checked) {\n'
        '        background: var(--charcoal);\n'
        '        color: var(--ivory);\n'
        '        border-color: var(--charcoal);\n'
        '      }\n'
        '      #truck-calc .truck-calc-seg input {\n'
        '        position: absolute;\n'
        '        width: 1px;\n'
        '        height: 1px;\n'
        '        padding: 0;\n'
        '        margin: -1px;\n'
        '        overflow: hidden;\n'
        '        clip: rect(0, 0, 0, 0);\n'
        '        white-space: nowrap;\n'
        '        border: 0;\n'
        '      }\n'
        '      #truck-calc .truck-calc-field input[type="text"],\n'
        '      #truck-calc .truck-calc-field select {\n'
        '        width: 100%;\n'
        '        min-height: 44px;\n'
        '        border: 1px solid var(--border-strong);\n'
        '        border-radius: var(--radius-sm);\n'
        '        background: var(--ivory);\n'
        '        color: var(--charcoal);\n'
        '        padding: 0.55rem 0.8rem;\n'
        '        font: inherit;\n'
        '      }\n'
        '      #truck-calc .truck-calc-error {\n'
        '        color: #8B2E1E;\n'
        '        font-size: 0.92rem;\n'
        '        min-height: 1.25em;\n'
        '        margin-top: var(--s-1);\n'
        '      }\n'
        '      #truck-calc .truck-calc-actions {\n'
        '        display: flex;\n'
        '        flex-wrap: wrap;\n'
        '        gap: var(--s-2);\n'
        '        margin-top: var(--s-5);\n'
        '      }\n'
        '      #truck-calc .truck-calc-results {\n'
        '        margin-top: var(--s-5);\n'
        '        padding: var(--s-4);\n'
        '        border: 1px solid var(--border);\n'
        '        border-radius: var(--radius);\n'
        '        background: var(--cream);\n'
        '      }\n'
        '      #truck-calc .truck-calc-results[hidden],\n'
        '      #truck-calc [hidden] { display: none; }\n'
        '      #truck-calc .truck-calc-context {\n'
        '        color: var(--warm-gray);\n'
        '        font-size: 0.95rem;\n'
        '        margin-bottom: var(--s-3);\n'
        '      }\n'
        '      #truck-calc .truck-calc-kicker {\n'
        '        font-size: 0.75rem;\n'
        '        letter-spacing: 0.08em;\n'
        '        text-transform: uppercase;\n'
        '        color: var(--bronze);\n'
        '        font-weight: 650;\n'
        '      }\n'
        '      #truck-calc .truck-calc-trips {\n'
        '        font-size: clamp(2rem, 4vw, 2.5rem);\n'
        '        font-weight: 650;\n'
        '        line-height: 1.15;\n'
        '        color: var(--charcoal);\n'
        '        margin: 0 0 var(--s-3);\n'
        '      }\n'
        '      #truck-calc .truck-calc-loads-label {\n'
        '        font-weight: 600;\n'
        '        margin-bottom: var(--s-1);\n'
        '      }\n'
        '      #truck-calc .truck-calc-safety {\n'
        '        margin-top: var(--s-3);\n'
        '        color: var(--warm-gray);\n'
        '        font-size: 0.95rem;\n'
        '      }\n'
        '      #truck-calc .truck-calc-cta { margin-top: var(--s-6); }\n'
        '      #truck-calc .truck-calc-cta p {\n'
        '        max-width: var(--measure-lead);\n'
        '        margin-bottom: var(--s-3);\n'
        '      }\n'
        '      #truck-calc .truck-calc-status:empty { display: none; }\n'
        '      #truck-calc .truck-anim {\n'
        '        position: relative;\n'
        '        max-width: 36rem;\n'
        '        aspect-ratio: 680 / 300;\n'
        '        margin-top: calc(var(--s-3) - var(--s-7));\n'
        '        margin-bottom: var(--s-4);\n'
        '      }\n'
        '      #truck-calc .truck-anim img,\n'
        '      #truck-calc .truck-anim-stage {\n'
        '        position: absolute;\n'
        '        inset: 0;\n'
        '        width: 100%;\n'
        '        max-width: 100%;\n'
        '        height: 100%;\n'
        '      }\n'
        '      #truck-calc .truck-anim-stage { visibility: hidden; }\n'
        '      #truck-calc .truck-anim.is-playing .truck-anim-stage { visibility: visible; }\n'
        '      #truck-calc .truck-anim.is-playing img { visibility: hidden; }\n'
        '    </style>\n'
        '    <div class="shell">\n'
        '      <div class="section-head">\n'
        '        <p class="eyebrow">On this page</p>\n'
        '        <h2 id="truck-calc-heading">Estimate truck trips here</h2>\n'
        '        <p class="lead">Use the same quantity ÷ capacity math as the Findry app. Quantity and capacity stay in one unit — this calculator does not convert volume to weight, or weight to volume.</p>\n'
        '      </div>\n'
        f'      <div class="truck-anim" data-lottie-anim data-player="{anim_player_src}" data-src="{anim_json_src}" aria-hidden="true">\n'
        f'        <img src="{anim_still_src}" alt="" width="680" height="300" decoding="async">\n'
        '        <div class="truck-anim-stage" data-lottie-stage></div>\n'
        '      </div>\n'
        '      <noscript>\n'
        '        <p class="note">This on-page calculator needs JavaScript. The formula and examples below still work, and you can get the same tool in the Findry app.</p>\n'
        '      </noscript>\n'
        '      <form class="truck-calc-card" data-truck-form hidden novalidate>\n'
        '        <fieldset>\n'
        '          <legend>Calculation type</legend>\n'
        '          <div class="truck-calc-seg">\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-category" value="volume" checked>\n'
        '              Volume\n'
        '            </label>\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-category" value="weight">\n'
        '              Weight\n'
        '            </label>\n'
        '          </div>\n'
        '        </fieldset>\n'
        '        <fieldset data-units-volume>\n'
        '          <legend>Unit</legend>\n'
        '          <div class="truck-calc-seg">\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-unit" value="cubic-yards" checked>\n'
        '              Cubic Yards (yd³)\n'
        '            </label>\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-unit" value="cubic-metres">\n'
        '              Cubic Metres (m³)\n'
        '            </label>\n'
        '          </div>\n'
        '        </fieldset>\n'
        '        <fieldset data-units-weight hidden>\n'
        '          <legend>Unit</legend>\n'
        '          <div class="truck-calc-seg">\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-unit" value="us-short-tons">\n'
        '              US Short Tons\n'
        '            </label>\n'
        '            <label>\n'
        '              <input type="radio" name="truck-calc-unit" value="metric-tonnes">\n'
        '              Metric Tonnes\n'
        '            </label>\n'
        '          </div>\n'
        '        </fieldset>\n'
        '        <div class="truck-calc-field">\n'
        '          <label class="truck-calc-label" for="truck-calc-quantity">Material quantity (<span data-quantity-unit>yd³</span>)</label>\n'
        '          <input id="truck-calc-quantity" name="quantity" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="e.g. 85" aria-describedby="truck-calc-quantity-error">\n'
        '          <p id="truck-calc-quantity-error" class="truck-calc-error" role="alert"></p>\n'
        '        </div>\n'
        '        <div class="truck-calc-field" data-capacity-presets>\n'
        '          <label class="truck-calc-label" for="truck-calc-capacity-preset">Truck capacity (<span data-capacity-unit>yd³</span>)</label>\n'
        '          <select id="truck-calc-capacity-preset" name="capacity-preset" aria-describedby="truck-calc-capacity-error">\n'
        + yard_options + '\n'
        '              <option value="custom">Custom</option>\n'
        '          </select>\n'
        '        </div>\n'
        '        <div class="truck-calc-field" data-capacity-custom hidden>\n'
        '          <label class="truck-calc-label" for="truck-calc-capacity">Truck capacity (<span data-capacity-unit-custom>yd³</span>)</label>\n'
        '          <input id="truck-calc-capacity" name="capacity" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="e.g. 24.5" aria-describedby="truck-calc-capacity-error">\n'
        '        </div>\n'
        '        <p id="truck-calc-capacity-error" class="truck-calc-error" role="alert"></p>\n'
        '        <div class="truck-calc-actions">\n'
        '          <button type="submit" class="btn btn--primary">Calculate</button>\n'
        '          <button type="button" class="btn btn--secondary" data-truck-reset>Start New Calculation</button>\n'
        '        </div>\n'
        '        <div class="truck-calc-results" data-truck-results hidden aria-live="polite">\n'
        '          <p class="truck-calc-context" data-result-context></p>\n'
        '          <p class="truck-calc-kicker">Estimated trips</p>\n'
        '          <p class="truck-calc-trips"><span data-result-trips></span></p>\n'
        '          <p class="truck-calc-loads-label" data-result-loads-label>Load Equivalent by Volume</p>\n'
        '          <p data-result-loads></p>\n'
        '          <p class="truck-calc-safety" data-result-safety></p>\n'
        '        </div>\n'
        '        <p class="note truck-calc-status" data-truck-status role="status" aria-live="polite"></p>\n'
        '      </form>\n'
        '      <div class="truck-calc-cta">\n'
        '        <p>Get the same calculator in the Findry app, along with Calculator History and the rest of your field tools.</p>\n'
        '        <div class="btn-row btn-row--stores">\n'
        '          ' + store_html + '\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>\n'
        f'    <script src="{script_src}" defer></script>\n'
        f'    <script src="{anim_script_src}" defer></script>\n'
        '  </section>\n'
    )


def build_findry_truck_load_calculator():
    a = APP['findry']
    path = 'apps/findry/truck-load-calculator/index.html'
    up = '../' * path.count('/')
    title = 'Truck Load Calculator: Cubic Yards & Trips | Findry'
    description = ('Estimate dump truck trips from a volume or weight quantity and matching truck capacity. '
                   'Volume in yd³ or m³; weight in US short tons or metric tonnes. Free Findry app for iPhone and Android.')
    gallery = shot_gallery('Truck Load Calculator screenshots', [
        ('assets/img/findry/findry-truck-load-input.webp',
         'Truck Load Calculator screen for entering a material quantity and truck capacity.'),
        ('assets/img/findry/findry-truck-load-results.webp',
         'Truck Load Calculator estimate showing the trips for the quantity and truck capacity entered.'),
    ], up)
    # Visible FAQ and FAQPage JSON-LD are built from the same strings.
    faqs = [
        ('How do I calculate how many truck loads I need?',
         'Divide the material quantity by the truck’s capacity, using the same unit for both, '
         'then round up to a whole number of trips. For example, 400 cubic yards ÷ 24 yd³ = '
         '16.67 loads, which is 17 trips.'),
        ('How many truck loads of gravel or dirt will I need?',
         'Once you know the cubic yards of gravel, fill dirt, or another material, divide by '
         'your dump truck’s capacity in cubic yards and round up. Findry’s Truck Load Calculator '
         'does that math for you. If you still need the cubic yards from a length, width, and '
         'depth, use the Material Calculator first.'),
        ('What dump truck capacities does Findry include?',
         'For cubic yards, Findry includes presets of 5, 6, 8, 10, 12, 14, 16, 18, and 20 yd³, '
         'plus a custom capacity field for other sizes. The default is 10 yd³. You can also work in '
         'cubic metres, US short tons, or metric tonnes, and enter the capacity in that same unit.'),
        ('Does the Truck Load Calculator use volume or weight?',
         'You can choose Volume or Weight. For volume, pick cubic yards or cubic metres. For weight, '
         'pick US short tons or metric tonnes. Quantity and capacity use the same unit, and the '
         'calculator does not convert volume to weight or weight to volume. When you work in volume, '
         'trips are based on volume. When you work in weight, trips are based on that weight quantity. '
         'Results are estimates and do not set legal payload or safe hauling limits.'),
        ('Why does Findry round trips up?',
         'A partly full truck still makes a trip. The load equivalent can be a decimal (for '
         'example 16.67 loads), and Estimated Trips is that number rounded up to a whole truck '
         'count.'),
        ('Is the Truck Load Calculator free, and what phones does it work on?',
         'Yes. The Truck Load Calculator and the Material Calculator are completely free for all '
         'users, on both the free plan and Findry Pro, and no subscription is needed. Findry is '
         'free to download for iPhone (iOS 16.4 or later) and Android (7.0 or later). You can save '
         'calculations to Calculator History and reopen them later.'),
    ]
    faq_items = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(question)}</h3>
          <p>{e(answer)}</p>
        </div>'''
        for question, answer in faqs)
    faq_ld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer},
            }
            for question, answer in faqs
        ],
    }, indent=2, ensure_ascii=False)

    widget = truck_load_calculator_widget(up, store_buttons(a))
    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="/apps/findry/">Back to Findry</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <p class="eyebrow">Findry field tools</p>
        <h1>Truck Load Calculator for Gravel, Dirt, and Jobsite Hauling</h1>
        <p class="tagline">Estimate truck trips from quantity and truck capacity.</p>
        <p class="lead">Findry’s Truck Load Calculator helps contractors and field crews
          estimate how many truck trips a material quantity may take. Enter the quantity,
          choose Volume or Weight, and pick a unit. For volume, use cubic yards or cubic metres.
          For weight, use US short tons or metric tonnes. Quantity and capacity use the same
          unit — the calculator does not convert volume to weight, or weight to volume. When you
          work in cubic yards, the default truck capacity is 10 yd³, or you can choose another
          preset or a custom size. Findry then shows the load equivalent and the estimated number
          of trips. The Truck Load Calculator is part of the Findry app for iPhone and Android,
          and it is free for all users. You can also run the same estimate in the calculator on this page.</p>
        <div class="btn-row btn-row--stores">
          {store_buttons(a)}
        </div>
      </div>
      <div class="rise rise-2">
        {gallery}
      </div>
    </div>
  </section>

  {widget}

  <section class="section section--tinted" aria-labelledby="truck-features">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Truck trip estimates</p>
        <h2 id="truck-features">Turn a material quantity into a quick trip estimate.</h2>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Enter the material quantity</h3>
          <p>Start with the amount of material you need to move using a supported volume or weight unit.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Set the truck capacity</h3>
          <p>Use a truck capacity that matches the vehicle or hauling setup you are estimating.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Estimate the number of trips</h3>
          <p>Findry calculates the estimated trips required from the quantity and capacity you entered.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="truck-capacities">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Truck sizes</p>
        <h2 id="truck-capacities">Dump truck capacity presets (cubic yards)</h2>
        <p class="lead">Choose a common dump truck size, or enter the capacity of the truck you actually have. When you work in cubic yards, Findry includes presets for:</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>5 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>6 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>8 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>10 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>12 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>14 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>16 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>18 yd³</h3>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>20 yd³</h3>
        </div>
      </div>
      <div class="prose" style="margin-top:var(--s-6)">
        <p>The default cubic-yard capacity is <strong>10 yd³</strong>. Need a different size? Use <strong>Custom Capacity</strong> (for example 24 yd³). You can also work in cubic metres, US short tons, or metric tonnes, and enter the capacity in that same unit. Changing the calculation type or unit clears the quantity and capacity you already entered, so set those first.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="how-to">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Step by step</p>
        <h2 id="how-to">How to use the Truck Load Calculator</h2>
        <p class="lead">Open Findry and tap Truck Load Calculator on the Home screen. A typical estimate takes four steps.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 1: Enter the material quantity</h3>
          <p>Type the amount of material you need to move. Use a quantity you already know from a supplier quote, a takeoff, or Findry’s Material Calculator.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 2: Choose Volume or Weight, then the unit</h3>
          <p>Pick Volume to work in cubic yards or cubic metres, or Weight to work in US short tons or metric tonnes. Quantity and capacity must use the same unit; the calculator does not convert between volume and weight. Set the calculation type and unit before you finish the other fields, because changing them clears quantity and capacity.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 3: Set the truck capacity</h3>
          <p>When you work in cubic yards, the default capacity is 10 yd³. Pick a preset from 5 to 20 cubic yards, enter a custom capacity for your own truck, or switch to cubic metres, US short tons, or metric tonnes if that matches how you measure the vehicle.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 4: Calculate, then save or adjust</h3>
          <p>Tap Calculate to see the load equivalent and the estimated number of trips. In volume units the load equivalent is shown by volume; in weight units it is shown by weight quantity. In the Findry app, use Edit Inputs to change a number, or save the result to Calculator History to reopen it later.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="formula">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">The formula</p>
        <h2 id="formula">How to calculate truck loads and trips</h2>
        <p class="lead">The Truck Load Calculator uses the same math you would do by hand. Here it is in plain words, so you can check any estimate.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Load equivalent</h3>
          <p>Divide the material quantity by the truck’s capacity, using the same unit for both. For volume work: quantity (yd³) ÷ truck capacity (yd³) = load equivalent. For weight work: quantity (US short tons) ÷ truck capacity (US short tons) = load equivalent, or the same division in metric tonnes. The calculator does not convert volume to weight or weight to volume.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Estimated trips</h3>
          <p>Round the load equivalent <strong>up</strong> to a whole number of trips. A partly full truck still makes a trip, so 3.1 loads is 4 trips, and 16.67 loads is 17 trips.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Volume-based trips</h3>
          <p>When you work in volume units, trips are based on volume only, not on weight. When you work in weight units, trips are based on the weight quantity and capacity you entered; the calculator does not convert that weight into volume. Real trucks also have legal payload and volume limits. Findry does not set legal payload or safe hauling capacity, so verify the vehicle and the load before you haul.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Don’t know the quantity yet?</h3>
          <p>Use the <a href="/apps/findry/material-calculator/">Material Calculator</a> to estimate cubic yards from length, width, and depth for gravel, crushed stone, sand, topsoil, fill dirt, mulch, concrete, and asphalt millings. Then bring that quantity here to plan trips.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="example-400">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="example-400">Example: 400 cubic yards with a 24 yd³ truck</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example using the same numbers as the app screenshot on this page.)</p>
        <p>A crew has <strong>400 yd³</strong> of material to move and a dump truck with a <strong>24 yd³</strong> custom capacity.</p>
        <ul>
          <li><strong>Load equivalent:</strong> 400 ÷ 24 = <strong>16.67 loads</strong></li>
          <li><strong>Estimated trips:</strong> round up → <strong>17 trips</strong></li>
        </ul>
        <p>That is the same result shown on the Truck Load Estimate screen in the Findry screenshots on this page.</p>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="example-fill-dirt">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="example-fill-dirt">Example: how many truck loads of fill dirt</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example with made-up sample values.)</p>
        <p>A contractor has <strong>85 yd³</strong> of fill dirt to haul and wants to compare two dump trucks.</p>
        <ul>
          <li><strong>With a 12 yd³ truck:</strong> 85 ÷ 12 = <strong>7.08 loads</strong>, so <strong>8 trips</strong></li>
          <li><strong>With a 20 yd³ truck:</strong> 85 ÷ 20 = <strong>4.25 loads</strong>, so <strong>5 trips</strong></li>
        </ul>
        <p>Same quantity of fill dirt; the larger truck cuts the trip count from 8 to 5. If the quantity came from a pad or trench measurement, run it first in the Material Calculator, then use those cubic yards here.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="trip-tips">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Before you haul</p>
        <h2 id="trip-tips">Tips for planning truck trips</h2>
      </div>
      <div class="prose">
        <ul>
          <li><strong>Match the unit to the quote.</strong> If the supplier sells by the cubic yard, work in cubic yards. If the quote is in US short tons or metric tonnes, switch to Weight and that unit before you enter numbers. If your takeoff is in cubic metres, switch the unit before you enter numbers.</li>
          <li><strong>Use the truck you will actually load.</strong> Presets cover common sizes from 5 to 20 yd³. For a different body size, enter a custom capacity instead of forcing a preset.</li>
          <li><strong>Round trips up, not down.</strong> A leftover 0.2 load still needs another run to the site or the dump.</li>
          <li><strong>Plan staging and turnaround.</strong> Trip count is only the hauling math. Access, dump time, and whether trucks can pass each other on site also affect the day.</li>
          <li><strong>Confirm weight and legal limits.</strong> Volume trips are not the same as a legal load. Moisture, material type, and the vehicle’s ratings can reduce how full you should load. Always verify before you haul.</li>
          <li><strong>Still need the yards?</strong> For gravel, dirt, sand, topsoil, and similar materials measured on site, start with the Material Calculator, then return here for trips.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="truck-history">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Calculator History</p>
        <h2 id="truck-history">Save estimates and reuse them later.</h2>
        <p class="lead">Completed truck-load calculations can be saved to Calculator History
          and reopened later when you need to review or reuse the estimate.</p>
      </div>
      <p class="note"><strong>Estimates only.</strong> Findry does not determine legal payload,
        gross vehicle weight ratings, axle compliance, road restrictions, or safe hauling
        capacity. Always verify the actual vehicle, material, and legal requirements before hauling.</p>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="truck-faq">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">FAQ</p>
        <h2 id="truck-faq">Truck load calculator FAQ</h2>
      </div>
      <div class="feature-list">
{faq_items}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="findry-truck">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <p class="eyebrow">Part of Findry</p>
          <h2 id="findry-truck">Keep truck estimates with the rest of your field workflow.</h2>
          <p>Findry combines field calculators with project records, measurements, photos,
            reference points, notes, search, and jobsite documentation.</p>
          <p>Don’t know the quantity yet? Start with the <a href="/apps/findry/material-calculator/">Material Calculator</a>.</p>
          <p>And keep <a href="/apps/findry/underground-utility-records/">underground utility records</a> for the same project.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--secondary" href="/apps/findry/">Explore Findry</a>
        </div>
      </div>
    </div>
  </section>

  <script type="application/ld+json">
{faq_ld}
  </script>

</main>
'''

    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": SITE + "apps/findry/truck-load-calculator/",
        "description": description,
        "about": {
            "@type": "SoftwareApplication",
            "name": "Findry",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": a.get('operating_system', a.get('platform', '')),
            "url": SITE + app_route(a),
            "downloadUrl": [url for url in (a.get('store_url'), a.get('play_url')) if url],
            "featureList": [
                "Truck trip estimates",
                "Preset truck capacities from 5 to 20 cubic yards",
                "Custom truck capacity",
                "Volume and weight calculation types",
                "US short tons and metric tonnes",
                "Calculator History",
            ],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
        "mainEntity": {
            "@type": "WebApplication",
            "name": "Findry Truck Load Calculator",
            "url": SITE + "apps/findry/truck-load-calculator/",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Any",
            "browserRequirements": "Requires JavaScript",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "featureList": [
                "Truck trip estimates from quantity and capacity",
                "Volume units: cubic yards and cubic metres",
                "Weight units: US short tons and metric tonnes",
                "Preset truck capacities from 5 to 20 cubic yards",
                "Custom truck capacity",
            ],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
        },
    }

    return _findry_tool_page(path, title, description, body, structured)


# ============================================ Findry underground utility records ===
def build_findry_underground_utility_records():
    a = APP['findry']
    path = 'apps/findry/underground-utility-records/index.html'
    up = '../' * path.count('/')
    title = 'Utility Locating Software for Field Records | Findry'
    description = ('Utility locating software for records, not detection. Save depths, '
                   'photos, reference points, and notes by project. '
                   'Free Findry app for iPhone and Android.')
    gallery = shot_gallery('Underground utility record screenshot', [
        ('assets/img/findry/findry-underground-documentation.webp',
         'A Findry record for a buried storm-drain cleanout, with depth, length, reference points, and photos.'),
    ], up)
    # Visible FAQ and FAQPage JSON-LD are built from the same strings.
    faqs = [
        ('What should an underground utility record include?',
         'At minimum: the utility type, size and material, depth, location tied to fixed '
         'reference points, photos, the date, and who did the work. Adding the locate ticket '
         'number and any warnings makes the record much more useful to the next crew.'),
        ('Can Findry locate or detect underground utilities?',
         'No. Findry is a documentation app. It stores the information you enter, such as '
         'depths, measurements, reference points, and photos. It does not detect, verify, or '
         'professionally locate underground utilities, and it does not replace 811 or local '
         'utility-marking requirements. Always check your local 811 rules before you dig.'),
        ('Can I use Findry to keep my own as-built notes?',
         'Yes. You can keep your own notes on what was actually installed and where. Findry '
         'lets you save that information as records under each project, with depths, '
         'measurements, reference points, materials, and photos. Check with your project '
         'owner or local authority for any official as-built drawing requirements.'),
        ('How do I find a record later?',
         'Search by project, record title, utility type, keywords, or notes. You can also '
         'mark records with Find Later and use Emergency Lookup for quick access to '
         'important records.'),
        ('Is Findry free, and what phones does it work on?',
         'Findry is free to download for iPhone (iOS 16.4 or later) and Android (7.0 or '
         'later). An optional Findry Pro subscription adds extra features, including cloud '
         'backup.'),
        ('Is Findry utility locating software?',
         'Yes, if you mean software to document utility locates and buried installations. '
         'Findry is an iPhone and Android app for jobsite and underground utility records. '
         'You can save depths, measurements, photos, reference points, materials, warnings, '
         'and notes, organized by project, and search them later. Findry is not a locating '
         'device and not a utility locating service. It does not detect, verify, or '
         'professionally locate underground utilities, and it does not replace 811 or local '
         'utility-marking requirements.'),
        ('What is the difference between utility locating software and a utility locator?',
         'A utility locator is typically a physical device, or a professional locating '
         'service, used to detect or mark buried lines. Utility locating software can mean '
         'that kind of detection tool, or it can mean an app for keeping the records after '
         'a locate or installation. Findry is the records app. It stores information you '
         'enter. For detection and marking, use proper locating equipment and always call '
         '811 before you dig.'),
        ('Can I use Findry with an 811 locate?',
         'Yes. After a locate, or after you install or expose a line, you can add the locate '
         'ticket number, work date, and crew in the record title or notes, along with depths, '
         'photos, reference points, and any warnings. Findry does not replace 811 or local '
         'utility-marking requirements. Always call 811 before you dig.'),
    ]
    faq_items = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(question)}</h3>
          <p>{e(answer)}</p>
        </div>'''
        for question, answer in faqs)
    faq_ld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer},
            }
            for question, answer in faqs
        ],
    }, indent=2, ensure_ascii=False)

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="/apps/findry/">Back to Findry</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <p class="eyebrow">Findry field records</p>
        <h1>Utility Locating Software for Field Records</h1>
        <p class="tagline">Document the work now so the details are easier to find later.</p>
        <p class="lead">Findry is an iPhone and Android app that helps contractors, excavators, plumbers, and utility crews document buried pipes and underground utility installations. If you are looking for utility locating software, use Findry to save depths, measurements, pipe sizes, materials, reference points, warnings, photos, and field notes in one record, organized by project, so the details are easy to find when you or your crew come back to the site.</p>
        <div class="btn-row btn-row--stores">
          {store_buttons(a)}
        </div>
      </div>
      <div class="rise rise-2">
        {gallery}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="utility-record-features">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Field documentation</p>
        <h2 id="utility-record-features">Keep buried utility details with the project they belong to.</h2>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Document buried pipes and utilities</h3>
          <p>Save pipe sizes, materials, depths, measurements, valve information, warnings,
            photos, and notes after installation or repair work.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Save reference measurements</h3>
          <p>Record distances and reference points from visible jobsite features so a saved
            location is easier to understand when the project is revisited.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Organize records by project</h3>
          <p>Keep field records attached to the correct project instead of scattering
            measurements, photos, and notes across notebooks and camera rolls.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="what-to-record">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">What to record</p>
        <h2 id="what-to-record">What to record for every underground utility</h2>
        <p class="lead">A good utility record answers one question for the next person on site: what is down there, and exactly where? These are the details worth saving every time a line is installed, repaired, or exposed.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Utility type and what was installed</h3>
          <p>Note the utility type (water, sewer, storm, gas, electric, telecom, irrigation, or other), the pipe or conduit size, the material, and any fittings, valves, or cleanouts. Give the record a clear title, like “6 in PVC sewer lateral – rear yard”, so it is easy to search later.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Depth and measurements</h3>
          <p>Record the depth to the top of the pipe or conduit, plus lengths and run distances you measured. Say where the depth was taken, for example “at the cleanout” or “10 ft from the house wall”, since depth can change along a run.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Location and reference points</h3>
          <p>Tie the location to things that will still be there later: building corners, curbs, hydrants, manholes, valve boxes, or property pins. Two measurements from two fixed points are easier to re-find than one. Add the project address so the record is connected to the right site. If your crew records coordinates with a separate GPS device, you can type them into the notes.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Photos</h3>
          <p>Take photos while the trench is open: the pipe in place, the depth with a tape or rod visible, and a wider shot that shows nearby landmarks. Photos of the backfilled area from the same spot help match the record to the site later.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Locate ticket number, date, and crew</h3>
          <p>Add the locate (811) ticket number, the work date, and who did the work in the record title or notes. That makes it easier to connect the record to the job paperwork and to know who to ask if questions come up.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Warnings and anything unusual</h3>
          <p>Note anything the next crew should know: shallow sections, nearby lines that were exposed, abandoned pipe, unmarked crossings, or tie-ins. Findry records include a warnings field for this.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="how-to-document">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Step by step</p>
        <h2 id="how-to-document">How to document underground utilities with Findry</h2>
        <p class="lead">The best time to document a buried line is before it is covered. Here is a simple routine your crew can follow on every job.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 1: Create or open the project</h3>
          <p>Add the project in Findry with its name, address, and project manager contact details. Every record you save goes under this project.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 2: Add a record while the line is exposed</h3>
          <p>Create a new record with a clear title and category. Enter the depth, measurements, pipe size, material, and any valve or cleanout details.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 3: Measure from fixed reference points</h3>
          <p>Save the distances from at least two permanent features on site so someone can find the spot again without guessing.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 4: Attach photos and notes</h3>
          <p>Add photos of the open trench and the surrounding area. Use the notes for the locate ticket number, work date, crew, and anything unusual. Add a warning if the next crew needs to know something before digging.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>Step 5: Find it when you return</h3>
          <p>Next week or years later, search by project, record title, utility type, keywords, or notes. Mark records with Find Later when you know you will need them again, and use Emergency Lookup for quick access to important records.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="storm-drain-example">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="storm-drain-example">Example: recording a storm-drain cleanout</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example only — not a real customer or job.)</p>
        <p>A crew installs a new storm-drain cleanout at the back of a commercial lot. Before backfilling, the foreman opens the project in Findry and adds a record:</p>
        <ul>
          <li><strong>Title:</strong> Storm-drain cleanout – NE corner of rear lot</li>
          <li><strong>Category / utility type:</strong> Storm drain</li>
          <li><strong>Details:</strong> 4 in PVC, cleanout cap at grade</li>
          <li><strong>Depth:</strong> 3 ft 2 in to top of pipe at the wye</li>
          <li><strong>Length:</strong> 18 ft run from the wye to the catch basin</li>
          <li><strong>Reference points:</strong> 12 ft from the NE building corner; 7 ft 6 in from the curb face</li>
          <li><strong>Photos:</strong> open trench with tape at the wye; wide shot toward the building corner; finished cleanout after backfill</li>
          <li><strong>Notes:</strong> Locate ticket #(your ticket number). Installed (date) by (crew). Water line crosses about 2 ft north of the cleanout, roughly 18 in shallower.</li>
          <li><strong>Warning:</strong> Water crossing nearby — hand dig within 2 ft.</li>
        </ul>
        <p>Eight months later the owner calls about a backup. The foreman searches “cleanout” in the project, opens the record, and uses the two reference measurements and photos to go straight to the spot. Before any digging, the crew still calls 811 and follows local marking rules.</p>
        <p>(This matches the existing page screenshot, which shows a storm-drain cleanout record with depth, length, reference points, and photos. The numbers above are made-up sample values.)</p>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="find-later">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Find it later</p>
        <h2 id="find-later">Search the record when the job brings you back.</h2>
        <p class="lead">Use project details, record titles, utility types, keywords, notes,
          and saved jobsite information to locate the record you need without relying on memory.</p>
      </div>
      <p class="note"><strong>Documentation, not utility detection.</strong> Findry stores
        information entered by its users. It does not detect, verify, or professionally locate
        underground utilities, and it does not replace 811 or local utility-marking requirements.</p>
    </div>
  </section>

  <section class="section" aria-labelledby="utility-locating-software">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Utility locating software</p>
        <h2 id="utility-locating-software">Is Findry utility locating software?</h2>
        <p class="lead">Findry is software for documenting utility locates and buried installations, not a tool that detects what is in the ground.</p>
      </div>
      <div class="prose">
        <p>People looking for utility locating software, a utility locator app, or underground utility locating software often want one of two things: a device or service that finds buried lines, or a place to keep what was found and installed. Findry is the second.</p>
        <p>Findry is an iPhone and Android app for underground utilities, construction, and jobsite records. After a line is installed, repaired, or exposed — including after an 811 locate — you can document the work in a project record. Save the utility type, pipe or conduit size, material, depths, measurements, valve or cleanout details, photos, warnings, and field notes. Tie the location to visible jobsite features with reference points, and add the locate ticket number, work date, and crew in the record title or notes. If your crew records coordinates with a separate GPS device, you can type them into the notes.</p>
        <p>That is also what people mean when they search for utility locator software, utilities locator software, utility locate software, or buried utility location software and want a record they can come back to. Findry keeps those as-built notes with the project they belong to, so the next person on site can see what is down there, and where, without digging through notebooks or a camera roll.</p>
        <p>Findry is not a physical locating device and not a utility locating service. It stores information entered by its users. It does not detect, verify, or professionally locate underground utilities, and it does not replace 811 or local utility-marking requirements. Always call 811 before you dig, and use proper locating equipment and qualified locators where the job requires them.</p>
        <p>When you return to the job, search by project, record title, utility type, keywords, or notes. Mark records with Find Later when you know you will need them again, and use Emergency Lookup for quick access to important records.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="utility-faq">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">FAQ</p>
        <h2 id="utility-faq">Underground utility records FAQ</h2>
      </div>
      <div class="feature-list">
{faq_items}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="findry-records">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <p class="eyebrow">Part of Findry</p>
          <h2 id="findry-records">Field records, reference points, photos, and calculators in one app.</h2>
          <p>Findry combines project-based jobsite documentation with search, Find Later,
            Emergency Lookup, the <a href="/apps/findry/material-calculator/">Material Calculator</a>, and the <a href="/apps/findry/truck-load-calculator/">Truck Load Calculator</a>.</p>
          <p>Before you backfill, follow the step-by-step guide on <a href="/apps/findry/how-to-document-buried-utilities/">how to document buried utilities</a>.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--secondary" href="/apps/findry/">Explore Findry</a>
        </div>
      </div>
    </div>
  </section>

  <script type="application/ld+json">
{faq_ld}
  </script>

</main>
'''

    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": SITE + "apps/findry/underground-utility-records/",
        "description": description,
        "about": {
            "@type": "SoftwareApplication",
            "name": "Findry",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": a.get('operating_system', a.get('platform', '')),
            "url": SITE + app_route(a),
            "downloadUrl": [url for url in (a.get('store_url'), a.get('play_url')) if url],
            "featureList": [
                "Underground utility records",
                "Project-based jobsite documentation",
                "Photos and measurements",
                "Reference points and field notes",
                "Search and Find Later",
            ],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
    }

    return _findry_tool_page(path, title, description, body, structured)


# ============================================ Findry trench backfill calculator
TRENCH_CALC_PATH = 'apps/findry/trench-backfill-calculator/index.html'
BURIED_GUIDE_PATH = 'apps/findry/how-to-document-buried-utilities/index.html'


def trench_backfill_calculator_widget(up, store_html):
    """In-page Trench Backfill Calculator markup, scoped CSS, and script tags.

    Styling is copied from the Material Calculator widget (re-scoped to
    #trench-calc) so both calculators look the same. JS lives in
    assets/js/trench-backfill-calculator.js and reuses the Material Calculator
    densities from assets/js/material-calculator.js, which loads first. The
    form stays hidden until the script runs.
    """
    material_widget = material_calculator_widget(up, '')
    css = material_widget[material_widget.index('    <style>\n'):
                          material_widget.index('    </style>\n') + len('    </style>\n')]
    css = css.replace('#material-calc ', '#trench-calc ')
    material_options = '\n'.join(
        f'              <option value="{key}"{" selected" if key == "gravel" else ""}>{label}</option>'
        for key, label in (
            ('gravel', 'Gravel'),
            ('crushed-stone', 'Crushed Stone'),
            ('sand', 'Sand'),
            ('topsoil', 'Topsoil'),
            ('fill-dirt', 'Fill Dirt'),
            ('mulch', 'Mulch'),
            ('concrete', 'Concrete'),
            ('asphalt-millings', 'Asphalt Millings'),
        )
    )
    yard_options = '\n'.join(
        f'              <option value="{n}"{" selected" if n == 10 else ""}>{n} yd³</option>'
        for n in (5, 6, 8, 10, 12, 14, 16, 18, 20)
    )

    def dim_field(key, label, unit, placeholder, hint=''):
        hint_html = (f'\n              <p class="material-calc-hint">{hint}</p>' if hint else '')
        return (
            f'            <div class="material-calc-field">\n'
            f'              <label class="material-calc-label" for="trench-calc-{key}">{label}</label>\n'
            f'              <div class="material-calc-input-row">\n'
            f'                <input id="trench-calc-{key}" name="{key}" type="text" inputmode="decimal" maxlength="16" autocomplete="off" spellcheck="false" placeholder="{placeholder}" aria-describedby="trench-calc-{key}-error">\n'
            f'                <span class="material-calc-unit" data-{key}-unit>{unit}</span>\n'
            f'              </div>{hint_html}\n'
            f'              <p id="trench-calc-{key}-error" class="material-calc-error" role="alert"></p>\n'
            f'            </div>\n'
        )

    dims = (dim_field('length', 'Trench length', 'ft', 'e.g. 100')
            + dim_field('width', 'Trench width', 'ft', 'e.g. 2')
            + dim_field('depth', 'Trench depth', 'ft', 'e.g. 4')
            + dim_field('pipe', 'Pipe diameter (optional)', 'in', 'e.g. 6',
                        'Leave blank for no pipe. The pipe volume is subtracted from the trench.'))

    return f'''  <section id="trench-calc" class="section" aria-labelledby="trench-calc-heading">
{css}    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">On this page</p>
        <h2 id="trench-calc-heading">Estimate trench backfill here</h2>
        <p class="lead">Enter the trench size, an optional pipe diameter, a material, and your truck capacity. The default is Gravel, Imperial units, and a 10 yd³ truck. Material weights are the same ones the Findry Material Calculator uses. Trips are based on volume only, and this calculator does not add a waste, swell, or compaction allowance.</p>
      </div>
      <noscript>
        <p class="note">This on-page calculator needs JavaScript. The formula and example below still work by hand.</p>
      </noscript>
      <form class="material-calc-card" data-trench-form hidden novalidate>
        <div class="material-calc-field">
          <label class="material-calc-label" for="trench-calc-material">Backfill material</label>
          <select id="trench-calc-material" name="material">
{material_options}
          </select>
        </div>
        <fieldset>
          <legend>Truck capacity</legend>
          <div class="material-calc-seg">
            <label>
              <input type="radio" name="trench-calc-capacity-unit" value="cubic-yards" checked>
              Cubic Yards
            </label>
            <label>
              <input type="radio" name="trench-calc-capacity-unit" value="cubic-metres">
              Cubic Metres
            </label>
          </div>
        </fieldset>
        <div class="material-calc-field" data-capacity-presets>
          <label class="material-calc-label" for="trench-calc-capacity-preset">Truck capacity (yd³)</label>
          <select id="trench-calc-capacity-preset" name="capacity-preset" aria-describedby="trench-calc-capacity-error">
{yard_options}
              <option value="custom">Custom</option>
          </select>
        </div>
        <div class="material-calc-field" data-capacity-entry hidden>
          <label class="material-calc-label" for="trench-calc-capacity" data-capacity-entry-label>Custom truck capacity (yd³)</label>
          <div class="material-calc-input-row">
            <input id="trench-calc-capacity" name="capacity" type="text" inputmode="decimal" maxlength="12" autocomplete="off" spellcheck="false" placeholder="e.g. 24" aria-describedby="trench-calc-capacity-error">
            <span class="material-calc-unit" data-capacity-entry-unit>yd³</span>
          </div>
          <p class="material-calc-hint" data-capacity-hint hidden>Enter your truck's capacity in cubic metres.</p>
        </div>
        <p id="trench-calc-capacity-error" class="material-calc-error" role="alert"></p>
        <fieldset>
          <legend>Dimension units</legend>
          <div class="material-calc-seg">
            <label>
              <input type="radio" name="trench-calc-units" value="imperial" checked>
              Imperial (ft, in)
            </label>
            <label>
              <input type="radio" name="trench-calc-units" value="metric">
              Metric (m, mm)
            </label>
          </div>
          <p class="material-calc-hint">Changing units clears entered measurements.</p>
        </fieldset>
        <fieldset>
          <legend>Trench measurements</legend>
          <div class="material-calc-dims">
{dims}          </div>
        </fieldset>
        <div class="material-calc-actions">
          <button type="submit" class="btn">Calculate</button>
          <button type="button" class="btn btn--secondary" data-trench-reset>Reset</button>
        </div>
        <div class="material-calc-results" data-trench-results hidden aria-live="polite">
          <p class="material-calc-context" data-result-context></p>
          <p class="material-calc-kicker" data-result-hero-label>Backfill (cubic yards)</p>
          <p class="material-calc-hero" data-result-hero></p>
          <dl class="material-calc-rows">
            <div><dt data-result-secondary-label>Backfill (cubic metres)</dt><dd data-result-secondary></dd></div>
            <div><dt>Trench volume</dt><dd data-result-trench></dd></div>
            <div data-result-pipe-row hidden><dt>Pipe volume subtracted</dt><dd data-result-pipe></dd></div>
            <div><dt data-result-mass-label>Estimated US Short Tons</dt><dd data-result-mass></dd></div>
            <div><dt>Load Equivalent by Volume</dt><dd data-result-loads></dd></div>
            <div><dt>Estimated Trips by Volume</dt><dd data-result-trips></dd></div>
          </dl>
          <div class="material-calc-measure">
            <p class="material-calc-kicker">Measurements</p>
            <dl data-result-measurements></dl>
          </div>
          <p class="material-calc-safety" data-result-safety></p>
          <div class="material-calc-actions" style="margin-top:var(--s-4)">
            <button type="button" class="btn btn--secondary" data-trench-edit>Edit Measurements</button>
            <button type="button" class="btn btn--secondary" data-trench-reset>Start New Calculation</button>
          </div>
        </div>
        <p class="note material-calc-status" data-trench-status role="status" aria-live="polite"></p>
      </form>
      <div class="material-calc-cta">
        <p>After the trench is backfilled, the pipe is out of sight. Save its depth, size, photos, and reference points in the Findry app so you can find the work later.</p>
        <div class="btn-row btn-row--stores">
          {store_html}
        </div>
      </div>
    </div>
    <script src="{up}assets/js/material-calculator.js" defer></script>
    <script src="{up}assets/js/trench-backfill-calculator.js" defer></script>
  </section>
'''


def _faq_blocks(faqs):
    """Visible FAQ items and FAQPage JSON-LD, built from the same strings."""
    items = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(question)}</h3>
          <p>{e(answer)}</p>
        </div>'''
        for question, answer in faqs)
    ld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer},
            }
            for question, answer in faqs
        ],
    }, indent=2, ensure_ascii=False)
    return items, ld


def build_findry_trench_backfill_calculator():
    a = APP['findry']
    path = TRENCH_CALC_PATH
    up = '../' * path.count('/')
    title = 'Trench Backfill Calculator: Gravel, Yards & Tons | Findry'
    description = ('Free trench backfill calculator. Enter trench length, width, depth, and pipe '
                   'size to estimate cubic yards, tons of gravel or fill, and truck trips.')
    faqs = [
        ('How do I calculate trench backfill?',
         'Multiply the trench length × width × depth to get the trench volume. If a pipe goes in '
         'the trench, subtract the pipe volume: 3.1416 × (pipe diameter ÷ 2)² × length. In feet, '
         'divide the cubic feet by 27 to get cubic yards. For example, a 100 ft × 2 ft × 4 ft '
         'trench is 800 cubic feet. A 6-inch pipe takes up about 19.63 cubic feet, so the '
         'backfill is about 780.37 cubic feet, or 28.9 cubic yards.'),
        ('How much gravel do I need for a trench?',
         'Work out the backfill volume in cubic yards, then multiply by the weight of the gravel '
         'if your supplier sells by the ton. This calculator uses about 1.4 US short tons per '
         'cubic yard for gravel, the same estimate as the Findry Material Calculator. A 100 ft × '
         '2 ft × 4 ft trench with a 6-inch pipe needs about 28.9 cubic yards, or roughly 40.46 '
         'tons of gravel. Confirm the weight with your supplier.'),
        ('How much gravel do I need for a 100 ft trench?',
         'It depends on the width and depth. A 100 ft trench that is 2 ft wide and 1 ft deep holds '
         'about 7.41 cubic yards, or roughly 10.37 tons of gravel. At 2 ft wide and 4 ft deep, it '
         'holds about 29.63 cubic yards before any pipe is subtracted. Enter your own '
         'measurements in the calculator above.'),
        ('Should I subtract the pipe from the backfill?',
         'Yes, if you want the volume of material that goes around and over the pipe. Small pipes '
         'barely change the total, but large pipes and culverts can take up a lot of the trench. '
         'Enter the outside diameter of the pipe for the best estimate.'),
        ('Does the calculator include compaction or bedding?',
         'No. It uses exactly the measurements you enter and does not add a waste, swell, or '
         'compaction allowance. Backfill is usually placed and compacted in lifts, and the '
         'bedding, haunch, and cover zones may call for different materials. Ask your engineer '
         'or supplier how much extra to order and which material each zone needs.'),
        ('How many truck loads will I need to backfill a trench?',
         'Divide the backfill volume by your truck’s capacity, using the same unit, and round up '
         'to whole trips. For example, 28.9 cubic yards ÷ a 10 yd³ truck = 2.89 loads, so 3 trips. '
         'Trips are based on volume only, not legal payload or weight limits.'),
        ('Do I need to call 811 before I dig a trench?',
         'Yes. In the United States, call 811 or submit a request online a few working days before '
         'you dig, so buried utilities can be marked. Local rules vary, so check the requirements '
         'in your state. Findry does not detect or locate underground utilities.'),
    ]
    faq_items, faq_ld = _faq_blocks(faqs)
    widget = trench_backfill_calculator_widget(up, store_buttons(a))

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="/apps/findry/">Back to Findry</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid app-hero-grid--single">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <p class="eyebrow">Free Findry calculator</p>
        <h1>Trench Backfill Calculator</h1>
        <p class="tagline">Estimate backfill, tons, and truck trips for a trench.</p>
        <p class="lead">Use this free trench backfill calculator to estimate how much gravel,
          sand, fill dirt, or other material you need to backfill a utility trench. Enter the
          trench length, width, and depth in feet or metres, and add the pipe diameter if a pipe
          goes in the trench. The calculator subtracts the pipe volume and shows the backfill in
          cubic yards and cubic metres, the estimated weight in US short tons or metric tonnes,
          and how many truck trips it may take. It runs in your browser, so there is nothing to
          download.</p>
      </div>
    </div>
  </section>

  {widget}

  <section class="section section--tinted" aria-labelledby="trench-formula">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">The formula</p>
        <h2 id="trench-formula">How to calculate trench backfill</h2>
        <p class="lead">The calculator uses the same math you would do by hand. Here it is in plain words, so you can check any estimate.</p>
      </div>
      <div class="feature-list">
        <div class="feature-item">
          <div class="rule"></div>
          <h3>1. Trench volume</h3>
          <p>Trench volume = length × width × depth. In Imperial, use feet for all three to get cubic feet. In Metric, use metres to get cubic metres.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>2. Pipe volume</h3>
          <p>Pipe volume = π × (diameter ÷ 2)² × length, with π ≈ 3.1416. Convert the diameter to the same unit as the trench first: inches ÷ 12 for feet, or millimetres ÷ 1,000 for metres. Use the outside diameter of the pipe.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>3. Backfill volume</h3>
          <p>Backfill = trench volume − pipe volume. Divide cubic feet by 27 to get cubic yards, because one cubic yard is 3 ft × 3 ft × 3 ft. One cubic metre is about 1.308 cubic yards.</p>
        </div>
        <div class="feature-item">
          <div class="rule"></div>
          <h3>4. Weight and trips</h3>
          <p>Estimated weight = cubic yards × the material’s weight per cubic yard. Load equivalent = backfill ÷ truck capacity, and trips is that number rounded up, because a partly full truck still makes a trip.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="trench-example">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Example</p>
        <h2 id="trench-example">Example: gravel backfill for a 100 ft water line trench</h2>
      </div>
      <div class="prose">
        <p>(Illustrative example with made-up sample values.)</p>
        <p>A crew is backfilling a trench 100 ft long, 2 ft wide, and 4 ft deep around a 6-inch pipe with gravel, using a 10 yd³ truck.</p>
        <ul>
          <li><strong>Trench volume:</strong> 100 × 2 × 4 = 800 ft³ (29.63 yd³)</li>
          <li><strong>Pipe volume:</strong> 3.1416 × (0.5 ÷ 2)² × 100 = 19.63 ft³ (0.73 yd³)</li>
          <li><strong>Backfill:</strong> 800 − 19.63 = 780.37 ft³ ÷ 27 = <strong>28.9 yd³</strong> (<strong>22.1 m³</strong>)</li>
          <li><strong>Estimated weight:</strong> 28.9 × 1.4 = <strong>40.46 US short tons</strong> of gravel</li>
          <li><strong>Loads:</strong> 28.9 ÷ 10 = <strong>2.89 loads</strong>, so <strong>3 trips</strong></li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="trench-materials">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Materials</p>
        <h2 id="trench-materials">Material weights used</h2>
        <p class="lead">These are the same built-in estimates as the Findry Material Calculator, in US short tons (2,000 lb) per cubic yard.</p>
      </div>
      <div class="prose">
        <ul>
          <li><strong>Gravel:</strong> 1.4 tons per yd³</li>
          <li><strong>Crushed Stone:</strong> 1.5 tons per yd³</li>
          <li><strong>Sand:</strong> 1.35 tons per yd³</li>
          <li><strong>Topsoil:</strong> 1.1 tons per yd³</li>
          <li><strong>Fill Dirt:</strong> 1.2 tons per yd³</li>
          <li><strong>Mulch:</strong> 0.35 tons per yd³</li>
          <li><strong>Concrete:</strong> 2 tons per yd³</li>
          <li><strong>Asphalt Millings:</strong> 1.35 tons per yd³</li>
        </ul>
        <p>Real weights vary by product, moisture, and supplier, so check with your supplier before you order by the ton.</p>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="trench-tips">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Before you dig and order</p>
        <h2 id="trench-tips">Tips for trench backfill</h2>
      </div>
      <div class="prose">
        <ul>
          <li><strong>Call 811 before you dig.</strong> Request a locate a few working days ahead so existing utilities are marked, and follow your state’s rules.</li>
          <li><strong>Measure the average depth.</strong> Trench depth often changes along the run. Measure in a few places and use the average, or split the run into sections.</li>
          <li><strong>Use the outside pipe diameter.</strong> The outside diameter gives a more accurate pipe volume than the nominal size.</li>
          <li><strong>Plan for compaction.</strong> The calculator does not add extra for compaction or waste. Ask your engineer or supplier how much more to order.</li>
          <li><strong>Check the spec for each zone.</strong> Bedding, haunch, and final backfill may need different materials. Run one calculation per zone if they differ.</li>
          <li><strong>Document before you backfill.</strong> Once the trench is closed, the pipe is hard to find again. Take photos and record depth, size, and reference points first. See <a href="/apps/findry/how-to-document-buried-utilities/">how to document buried utilities</a>.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="trench-faq">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">FAQ</p>
        <h2 id="trench-faq">Trench backfill calculator FAQ</h2>
      </div>
      <div class="feature-list">
{faq_items}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="findry-trench">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <p class="eyebrow">Part of Findry</p>
          <h2 id="findry-trench">Keep a record of what you buried.</h2>
          <p>Findry is a jobsite record app. Save photos, depths, pipe sizes, materials, reference points, and notes by project before the trench is closed, so you can find the work later. Findry does not detect or locate underground utilities.</p>
          <p>Need more estimates? Try the <a href="/apps/findry/material-calculator/">Material Calculator</a> and the <a href="/apps/findry/truck-load-calculator/">Truck Load Calculator</a>.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--secondary" href="/apps/findry/">Explore Findry</a>
        </div>
      </div>
    </div>
  </section>

  <script type="application/ld+json">
{faq_ld}
  </script>

</main>
'''

    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": SITE + "apps/findry/trench-backfill-calculator/",
        "description": description,
        "about": {
            "@type": "SoftwareApplication",
            "name": "Findry",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": a.get('operating_system', a.get('platform', '')),
            "url": SITE + app_route(a),
            "downloadUrl": [url for url in (a.get('store_url'), a.get('play_url')) if url],
            "author": {"@type": "Organization", "name": "Kaymer LLC"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
    }

    return _findry_tool_page(path, title, description, body, structured)


# ================================== Findry guide: how to document buried utilities
def build_findry_buried_utilities_guide():
    a = APP['findry']
    path = BURIED_GUIDE_PATH
    up = '../' * path.count('/')
    title = 'How to Document Buried Utilities: Step-by-Step Guide | Findry'
    description = ('How to document buried pipes and utilities before backfill: photos, GPS '
                   'location, depth, size, material, and notes, saved so you can find the work later.')
    steps = [
        ('Step 1: Call 811 before you dig',
         'Before any excavation, call 811 or submit a request online a few working days ahead so '
         'existing buried utilities can be marked. Write the locate ticket number down. You will '
         'add it to your record later. Local rules vary, so follow the requirements in your state.'),
        ('Step 2: Photograph the work before backfill',
         'Once the pipe, conduit, or cable is in place and before any backfill goes in, take '
         'photos. Get a wide shot that shows the trench with a building, curb, or other fixed '
         'feature in view, then close-ups of fittings, valves, tees, bends, and connections. Lay '
         'a tape measure in the trench for scale and shoot a photo that shows the depth.'),
        ('Step 3: Record the location',
         'Tie the location to things that will still be there later, like building corners, '
         'curbs, hydrants, manholes, valve boxes, or property pins. Two measurements from two '
         'fixed points are easier to re-find than one. If you capture GPS coordinates with your '
         'phone or a GPS device, write them down too, but keep the tape measurements: phone GPS '
         'can be off by several feet.'),
        ('Step 4: Measure and write down the depth',
         'Measure from finished grade to the top of the pipe, and note where along the run you '
         'measured. Depth often changes, so take a reading at each end, at bends, and at any '
         'fittings or valves.'),
        ('Step 5: Note the material and size',
         'Record what was installed: the utility type (water, sewer, storm, gas, electric, '
         'telecom), the pipe or conduit material (for example PVC, HDPE, or ductile iron), the '
         'size, and the length of the run. Add any warning tape, tracer wire, or markers you put '
         'in the trench.'),
        ('Step 6: Add notes',
         'Write down the date, the crew or contractor, the locate ticket number, the project '
         'address, and anything the next person should know, like a change from the plan, a '
         'nearby line, or a shallow spot.'),
        ('Step 7: Save the record where you can find it later',
         'A record only helps if you can find it again. Keep photos and notes together, organized '
         'by project, instead of spread across a notebook, a text thread, and a camera roll. Make '
         'sure the record can be searched by address, project, or utility type, and back it up.'),
    ]
    step_items = '\n'.join(
        f'''        <div class="feature-item">
          <div class="rule"></div>
          <h3>{e(t)}</h3>
          <p>{e(d)}</p>
        </div>''' for t, d in steps)
    faqs = [
        ('Why document buried utilities?',
         'After backfill, a pipe or conduit is out of sight. A good record shows the next crew, '
         'the owner, or you, what is down there and where, so the work can be found for repairs, '
         'tie-ins, or new digging without guessing.'),
        ('What should a buried utility record include?',
         'At minimum: photos before backfill, the location tied to fixed reference points, the '
         'depth, the utility type, the material and size, the date, who did the work, and the '
         'locate ticket number. GPS coordinates and notes about warnings or changes make it even '
         'more useful.'),
        ('Can Findry find or detect underground pipes?',
         'No. Findry does not detect or locate underground utilities. It is a documentation app: '
         'it stores the photos, depths, measurements, reference points, and notes you save about '
         'the work you install or expose, so you can find that work later. It does not replace '
         '811 or professional locating.'),
        ('Do I still need to call 811 if I have records?',
         'Yes. Always call 811 before you dig. Your own records help you find your own work, but '
         'other utilities may be in the ground, and the law in most places requires a locate '
         'request before excavation.'),
        ('Can I add GPS coordinates to a Findry record?',
         'Yes. If you capture coordinates with your phone or a separate GPS device, you can type '
         'them into the record notes. Keep tape measurements to fixed reference points as well, '
         'because they are often more accurate than phone GPS.'),
        ('Is Findry free?',
         'Findry is free to download for iPhone (iOS 16.4 or later) and Android (7.0 or later). '
         'An optional Findry Pro subscription adds extra features, including cloud backup.'),
    ]
    faq_items, faq_ld = _faq_blocks(faqs)

    body = f'''<main id="main">

  <div class="shell" style="padding-top:var(--s-2)">
    <a class="backlink" href="/apps/findry/">Back to Findry</a>
  </div>

  <section class="app-hero shell">
    <div class="app-hero-grid app-hero-grid--single">
      <div class="rise">
        {icon_markup(a, up=up, large=True)}
        <p class="eyebrow">Findry field guide</p>
        <h1>How to Document Buried Utilities</h1>
        <p class="tagline">Record it before you backfill, so you can find it later.</p>
        <p class="lead">Once a trench is closed, the pipe, conduit, or cable inside it is out of
          sight. A few minutes of documentation before backfill can save hours of searching,
          guesswork, and risky digging later. This guide covers what to capture: photos, location,
          depth, material and size, and notes, and how to save it so the work can be found again.
          It applies to water and sewer lines, storm drains, irrigation, gas, electrical conduit,
          and telecom.</p>
        <p class="note" style="margin-top:var(--s-5)"><strong>Call 811 before you dig.</strong> In the United States, call 811 or
          submit a request online a few working days before any excavation so existing utilities can
          be marked. Your own records do not replace a locate request.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="guide-steps">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Step by step</p>
        <h2 id="guide-steps">How to document buried utilities in 7 steps</h2>
        <p class="lead">Do this while the trench is still open. Once it is backfilled, you cannot go back for the photo you missed.</p>
      </div>
      <div class="feature-list">
{step_items}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="guide-checklist">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">Checklist</p>
        <h2 id="guide-checklist">Buried utility record checklist</h2>
      </div>
      <div class="prose">
        <ul>
          <li>Photos before backfill: wide shot with a fixed feature, close-ups of fittings, and a depth photo with a tape</li>
          <li>Location: measurements from two fixed reference points, plus GPS coordinates if you have them</li>
          <li>Depth to the top of the pipe, with where each reading was taken</li>
          <li>Utility type, material, size, and length of run</li>
          <li>Valves, cleanouts, tees, bends, tracer wire, and warning tape</li>
          <li>Date, crew or contractor, project address, and 811 locate ticket number</li>
          <li>Notes on changes from the plan, nearby lines, or shallow spots</li>
          <li>Saved by project, searchable, and backed up</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="guide-findry">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">The easy way</p>
        <h2 id="guide-findry">Document buried utilities with Findry</h2>
        <p class="lead">Findry is a free jobsite record app for iPhone and Android. It keeps everything on this checklist in one record, inside the project it belongs to.</p>
      </div>
      <div class="prose">
        <p>Create a project for the job, then add a record for each line or installation. Save photos, depths, measurements, pipe size, material, valve and cleanout details, reference points, warnings, and field notes. Type the locate ticket number and any GPS coordinates into the notes.</p>
        <p>When you come back to the job next week or years later, search by project, record title, utility type, keywords, or notes. Mark records with Find Later, and use Emergency Lookup for quick access to important records.</p>
        <p><strong>Findry documents the work you bury so you can find it later. It does not detect or locate underground utilities,</strong> and it does not replace 811 or local utility-marking requirements.</p>
      </div>
      <div class="btn-row btn-row--stores" style="margin-top:var(--s-5)">
        {store_buttons(a)}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="guide-faq">
    <div class="shell">
      <div class="section-head">
        <p class="eyebrow">FAQ</p>
        <h2 id="guide-faq">Documenting buried utilities FAQ</h2>
      </div>
      <div class="feature-list">
{faq_items}
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="guide-more">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <p class="eyebrow">Part of Findry</p>
          <h2 id="guide-more">More for the same job.</h2>
          <p>See what to include in <a href="/apps/findry/underground-utility-records/">underground utility records</a>, and estimate fill for the trench with the free <a href="/apps/findry/trench-backfill-calculator/">Trench Backfill Calculator</a>.</p>
        </div>
        <div class="btn-row">
          <a class="btn btn--secondary" href="/apps/findry/">Explore Findry</a>
        </div>
      </div>
    </div>
  </section>

  <script type="application/ld+json">
{faq_ld}
  </script>

</main>
'''

    structured = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": "How to document buried utilities",
        "description": description,
        "url": SITE + "apps/findry/how-to-document-buried-utilities/",
        "step": [
            {"@type": "HowToStep", "position": i + 1, "name": t, "text": d}
            for i, (t, d) in enumerate(steps)
        ],
        "tool": [{"@type": "HowToTool", "name": "Findry app for iPhone or Android"},
                 {"@type": "HowToTool", "name": "Tape measure"}],
        "publisher": {"@type": "Organization", "name": "Kaymer LLC"},
    }

    return _findry_tool_page(path, title, description, body, structured)


# ============================================================== about page ===
def build_about():
    body = '''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="about-title">
    <div class="rise">
      <p class="eyebrow">ABOUT</p>
      <h1 id="about-title">Built for real work and everyday life.</h1>
      <div class="rule"></div>
      <p class="lead">Kaymer LLC creates focused mobile products that solve practical problems through clear, thoughtful design.</p>
      <div class="prose">
        <p>Based in the United States, we build technology around the way people actually work and live. Every product begins with a real need and is shaped to be useful, dependable, and easy to understand.</p>
      </div>
    </div>
  </section>

  <section class="section section--tinted" aria-labelledby="building">
    <div class="shell">
      <div class="section-head">
        <h2 id="building">What we’re building</h2>
      </div>
      <div class="feature-list feature-list--two">
        <article class="feature-item">
          <div class="rule"></div>
          <h3>Findry</h3>
          <p>Findry helps contractors and field crews organize important jobsite information—including photos, measurements, notes, and project details—and use practical tools such as the Material Calculator and Truck Load Calculator. It is available for iPhone and Android.</p>
        </article>
        <article class="feature-item">
          <div class="rule"></div>
          <h3>Nôs Beleza</h3>
          <p>Nôs Beleza is an upcoming local services marketplace for Cape Verde, beginning with beauty and personal care. It is currently in development and is not yet available in app stores.</p>
        </article>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="shell">
      <div class="email-card">
        <div class="email-card-body">
          <h2>Get in touch</h2>
          <p>Questions about our apps or about Kaymer LLC? Visit our support page.</p>
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
                'Kaymer LLC creates focused mobile products that solve practical problems through clear, thoughtful design.',
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

    nos_beleza_topics = '\n'.join([
        row('nos-beleza/support.html', 'Nôs Beleza help topics',
            'Accounts, finding a business, booking, services and schedule, reviews, photos, deletion.'),
        row('nos-beleza/support.html#s-2-customer-or-professional-which-account-do-i-need',
            'Customer or professional account',
            'Which account to open, and why a professional account cannot book.'),
        row('nos-beleza/support.html#s-8-professional-verification', 'Professional verification',
            'What to submit, who reviews it, and what the badge does not mean.'),
        row('nos-beleza/privacy.html#s-13-retention-and-deletion',
            'Deleting your Nôs Beleza account',
            'What is removed, what is kept, and what happens to your reviews.'),
    ])

    body = f'''<main id="main">

  <section class="hero hero--intro shell" aria-labelledby="support-title">
    <div class="rise">
      <p class="eyebrow">Support</p>
      <h1 id="support-title">How can we help?</h1>
      <div class="rule"></div>
      <p class="lead">Your email goes directly to Kaymer. Tell us which app you are using and
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

      <h3 class="ui-head" style="margin-bottom:var(--s-3)">Nôs Beleza</h3>
      <div class="link-rows">
{nos_beleza_topics}
      </div>
      <p class="note" style="margin-top:var(--s-6)">Findry's own legal documents list
        <a href="mailto:support@findryapp.com">support@findryapp.com</a> for questions about
        those documents. Both addresses reach Kaymer LLC.</p>
    </div>
  </section>

</main>
'''
    return page('contact.html', 'Support — Kaymer LLC',
                'Get support for Kaymer LLC apps. Email support@thekaymer.com, or jump straight to the published help and legal documents for Findry and Nôs Beleza.',
                'contact.html', body)


# ============================================================== legal index ==
def build_legal_index():
    # The URL migration must preserve the reviewed index copy and date labels.
    source = os.path.join(ROOT, 'legal/index.html')
    if not os.path.isfile(source):
        source = os.path.join(ROOT, 'legal.html')
    if os.path.isfile(source):
        markup = open(source, encoding='utf-8').read()
        existing_main = re.search(r'(?s)<main\b.*?</main>', markup)
        if existing_main:
            return page('legal.html', 'Legal — Kaymer LLC',
                        'Privacy policies, terms, and support documents for Kaymer LLC, Findry, and Nôs Beleza.',
                        'legal.html', existing_main.group(0) + '\n')
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
    nos_beleza_rows = '\n'.join([
        row('nos-beleza/privacy.html', 'Nôs Beleza Privacy Policy',
            legal_date_note('nos-beleza/privacy.html', '')),
        row('nos-beleza/terms.html', 'Nôs Beleza Terms of Service',
            legal_date_note('nos-beleza/terms.html', '')),
        row('nos-beleza/support.html', 'Nôs Beleza Support',
            'Help topics for accounts, bookings, verification, reviews, and deletion.'),
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

      <h2 class="ui-head" style="margin-bottom:var(--s-3)">Nôs Beleza</h2>
      <div class="link-rows">
{nos_beleza_rows}
      </div>

    </div>
  </section>

</main>
'''
    return page('legal.html', 'Legal — Kaymer LLC',
                'Privacy policies, terms, and support documents for Kaymer LLC, Findry, and Nôs Beleza.',
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
         'The Findry privacy policy: what the app collects, how it is used and stored, and how to delete your account. Effective October 9, 2026.'),
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
            '<a href="../apps/findry/">About Findry</a>',
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
    'nos-beleza/privacy.html': {
        'title': 'Nôs Beleza Privacy Policy — Kaymer LLC',
        'label': 'Nôs Beleza legal',
        'desc': 'The Nôs Beleza privacy policy: accounts, bookings, reviews, photos, professional verification, notifications, and account deletion.',
        'related': ['<a href="terms.html">Nôs Beleza Terms of Service</a>',
                    '<a href="support.html">Nôs Beleza Support</a>',
                    '<a href="../apps/nos-beleza.html">About Nôs Beleza</a>'],
    },
    'nos-beleza/terms.html': {
        'title': 'Nôs Beleza Terms of Service — Kaymer LLC',
        'label': 'Nôs Beleza legal',
        'desc': 'The Nôs Beleza terms of service, covering accounts, the marketplace relationship, bookings, professional verification, reviews, and liability.',
        'related': ['<a href="privacy.html">Nôs Beleza Privacy Policy</a>',
                    '<a href="support.html">Nôs Beleza Support</a>',
                    '<a href="../apps/nos-beleza.html">About Nôs Beleza</a>'],
    },
    'nos-beleza/support.html': {
        'title': 'Nôs Beleza Support — Kaymer LLC',
        'label': 'Nôs Beleza support',
        'desc': 'Help topics for Nôs Beleza: accounts, finding a business, booking and managing appointments, professional services and verification, reviews, photos, notifications, and account deletion.',
        'related': ['<a href="privacy.html">Nôs Beleza Privacy Policy</a>',
                    '<a href="terms.html">Nôs Beleza Terms of Service</a>',
                    '<a href="../contact.html">Contact support</a>'],
        'current': 'contact.html',
    },
}


def read_approved_legal(path):
    """Return (body_html, updated_line) from a document already in the current
    shell. This is the source of truth: whatever wording is committed is what
    gets re-emitted."""
    clean_path = os.path.join(ROOT, canonical_route(path), 'index.html')
    source = clean_path if os.path.isfile(clean_path) else os.path.join(ROOT, path)
    src = open(source, encoding='utf-8').read()
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
        '  <url>\n    <loc>{}{}</loc>\n  </url>'.format(SITE, canonical_route(p))
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
        if a['slug'] == 'findry':
            pages.append(build_findry_material_calculator())
            pages.append(build_findry_truck_load_calculator())
            pages.append(build_findry_underground_utility_records())
            pages.append(build_findry_trench_backfill_calculator())
            pages.append(build_findry_buried_utilities_guide())
    pages.append(build_about())
    pages.append(build_support())
    pages.append(build_legal_index())
    pages.extend(build_findry_legal())
    for p in LEGACY:
        pages.append(rebuild_legacy(p))

    write_redirect('apps/findry.html', 'apps/findry/', meta_refresh=True)
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
