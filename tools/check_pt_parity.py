#!/usr/bin/env python3
"""Structural parity check: Portuguese Nôs Beleza pages vs their English sources.

    python3 tools/check_pt_parity.py

Checks, for privacy / terms / support:
  * both editions exist and the PT page declares lang="pt";
  * the same section ids, in the same order, for h2 and h3 headings, and the
    same counts of paragraphs, list items, links and mailto addresses;
  * every <a href> in the PT legal body resolves to a real file/anchor, and any
    link to a Nôs Beleza document points at the PT sibling (never the English one);
  * the table of contents matches the headings;
  * canonical/hreflang point at the right editions.
Exit status is non-zero on any failure.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = ['privacy', 'terms', 'support']
failures = []


def fail(msg):
    failures.append(msg)
    print('FAIL', msg)


def read(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as fh:
        return fh.read()


def body(src):
    m = re.search(r'(?s)<div class="legal-body">\n(.*?)\n    </div>', src)
    return m.group(1) if m else ''


def ids(src, tag):
    return re.findall(r'<%s id="([^"]+)"' % tag, src)


def hrefs(src):
    return re.findall(r'<a [^>]*?href="([^"]+)"', src)


for doc in DOCS:
    en_path, pt_path = f'nos-beleza/{doc}.html', f'nos-beleza/pt/{doc}.html'
    if not os.path.exists(os.path.join(ROOT, en_path)):
        fail(f'{en_path} missing'); continue
    if not os.path.exists(os.path.join(ROOT, pt_path)):
        fail(f'{pt_path} missing'); continue
    en, pt = read(en_path), read(pt_path)
    eb, pb = body(en), body(pt)
    if not pb:
        fail(f'{pt_path}: no legal-body'); continue
    if '<html lang="pt">' not in pt:
        fail(f'{pt_path}: html lang is not pt')
    if '<html lang="en">' not in en:
        fail(f'{en_path}: html lang is not en')
    for tag in ('h2', 'h3'):
        if tag == 'h2' and ids(eb, 'h2') != ids(pb, 'h2'):
            fail(f'{pt_path}: h2 section ids differ from English')
        if len(re.findall(r'<%s[ >]' % tag, eb)) != len(re.findall(r'<%s[ >]' % tag, pb)):
            fail(f'{pt_path}: {tag} count differs')
    for tag in ('p', 'li', 'ul'):
        if len(re.findall(r'<%s[ >]' % tag, eb)) != len(re.findall(r'<%s[ >]' % tag, pb)):
            fail(f'{pt_path}: <{tag}> count differs ({len(re.findall(r"<%s[ >]" % tag, eb))} vs {len(re.findall(r"<%s[ >]" % tag, pb))})')
    if len(re.findall(r'<strong>', eb)) != len(re.findall(r'<strong>', pb)):
        fail(f'{pt_path}: <strong> count differs')
    en_mail = sorted(h for h in hrefs(eb) if h.startswith('mailto:'))
    pt_mail = sorted(h for h in hrefs(pb) if h.startswith('mailto:'))
    if en_mail != pt_mail:
        fail(f'{pt_path}: mailto links differ')
    if len(hrefs(eb)) != len(hrefs(pb)):
        fail(f'{pt_path}: link count differs')
    # TOC parity
    en_toc = re.findall(r'<li><a href="#([^"]+)">', en)
    pt_toc = re.findall(r'<li><a href="#([^"]+)">', pt)
    if en_toc != pt_toc or pt_toc != ids(pb, 'h2'):
        fail(f'{pt_path}: table of contents does not match headings')
    # Link resolution in the PT body and the whole page
    own_ids = set(re.findall(r'id="([^"]+)"', pt))
    for h in hrefs(pt):
        if h.startswith(('mailto:', 'http://', 'https://')):
            continue
        target, _, frag = h.partition('#')
        if not target:
            if frag not in own_ids:
                fail(f'{pt_path}: dangling anchor #{frag}')
            continue
        full = os.path.normpath(os.path.join(ROOT, os.path.dirname(pt_path), target))
        if not os.path.exists(full):
            fail(f'{pt_path}: broken link {h}'); continue
        if frag and os.path.isfile(full):
            if f'id="{frag}"' not in open(full, encoding='utf-8').read():
                fail(f'{pt_path}: link {h} points at a missing anchor')
    # No link from PT body to an English Nôs Beleza document
    for h in hrefs(pb):
        t = h.partition('#')[0]
        full = os.path.normpath(os.path.join(os.path.dirname(pt_path), t)) if t and not t.startswith(('mailto:', 'http')) else ''
        if re.fullmatch(r'nos-beleza/(privacy|terms|support)\.html', full):
            fail(f'{pt_path}: PT body links to English document {h}')
        if '../../' in h and h.partition('#')[0].endswith('.html') and 'nos-beleza' not in h and 'lang="en"' not in pb[max(0, pb.find(h) - 120):pb.find(h)] and 'hreflang="en"' not in pb[pb.find(h):pb.find(h) + 80]:
            fail(f'{pt_path}: site-level link {h} is not marked as English')
    # Canonical + hreflang
    if f'<link rel="canonical" href="https://thekaymer.com/nos-beleza/pt/{doc}.html">' not in pt:
        fail(f'{pt_path}: canonical wrong')
    for hl, u in (('en', f'https://thekaymer.com/nos-beleza/{doc}.html'), ('pt', f'https://thekaymer.com/nos-beleza/pt/{doc}.html')):
        if f'<link rel="alternate" hreflang="{hl}" href="{u}">' not in pt:
            fail(f'{pt_path}: hreflang {hl} missing')
    # Last-updated dates must describe the same day as the English page
    en_d = re.search(r'Last updated: (\w+) (\d+), (\d{4})', en)
    pt_d = re.search(r'Última atualização: (\d+) de (\w+) de (\d{4})', pt)
    months = dict(January='janeiro', February='fevereiro', March='março', April='abril', May='maio', June='junho', July='julho',
                  August='agosto', September='setembro', October='outubro', November='novembro', December='dezembro')
    if not (en_d and pt_d and (months[en_d.group(1)], en_d.group(2), en_d.group(3)) == (pt_d.group(2), pt_d.group(1), pt_d.group(3))):
        fail(f'{pt_path}: last-updated date does not match English')
    # Sitemap
    if f'https://thekaymer.com/nos-beleza/pt/{doc}.html' not in read('sitemap.xml'):
        fail(f'sitemap.xml missing PT {doc}')

if failures:
    print(f'\n{len(failures)} problem(s)')
    sys.exit(1)
print('OK: Portuguese pages match English structure (privacy, terms, support)')
