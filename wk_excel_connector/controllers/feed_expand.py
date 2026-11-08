# -*- coding: utf-8 -*-
##########################################################################
# AANPASSING Chameleonstars: kolommen uitklappen voor marktplaatsfeeds.
#
# Een regel in een Excel-template kan "uitgeklapt" worden:
#   - json      : een JSON-object (bv. Product Properties) wordt een kolom
#                 per sleutel, bv. {"brand": "Crazon"} -> kolom prop_brand
#   - html_list : de <li>-items van een HTML-tekst (bv. Description Fr)
#                 worden kolommen bullet_fr_1, bullet_fr_2, ...
#
# Bewust zonder Odoo-imports, zodat dit los te testen is.
##########################################################################

import json
import re

MODE_JSON = 'json'
MODE_HTML_LIST = 'html_list'

_SLUG_RE = re.compile(r'[^a-z0-9]+')


def slugify(text):
    """'Age from (years)' -> 'age_from_years'"""
    return _SLUG_RE.sub('_', str(text or '').lower()).strip('_')


def to_cell(value):
    """Waarde omzetten naar tekst voor de CSV."""
    if value is None or value is False:
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def parse_json_object(value):
    """Geeft altijd een dict terug; alles wat geen JSON-object is wordt {}."""
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def html_list_items(value):
    """Tekst van de <li>-items in een HTML-fragment, in volgorde.

    Geneste lijsten worden niet apart geteld: hun tekst zit in het
    bovenliggende item.
    """
    if not value or not isinstance(value, str) or '<li' not in value.lower():
        return []
    try:
        from lxml import html as lxml_html
        root = lxml_html.fragment_fromstring(value, create_parent='div')
    except Exception:
        return []
    items = []
    for li in root.iter('li'):
        if any(anc.tag == 'li' for anc in li.iterancestors()):
            continue
        text = ' '.join(li.text_content().split())
        if text:
            items.append(text)
    return items


def _plan_json(values, prefix):
    parsed = [parse_json_object(v) for v in values]
    # slug -> sleutels die erop uitkomen (bij botsing wint de eerste niet-lege)
    slugs = {}
    for data in parsed:
        for key in data:
            slug = slugify(key)
            if not slug:
                continue
            keys = slugs.setdefault(slug, [])
            if key not in keys:
                keys.append(key)
    columns = sorted(slugs)
    headers = [prefix + slug for slug in columns]
    cells = []
    for data in parsed:
        row = []
        for slug in columns:
            value = ''
            for key in slugs[slug]:
                value = to_cell(data.get(key))
                if value:
                    break
            row.append(value)
        cells.append(row)
    return headers, cells


def _plan_html_list(values, prefix, limit):
    items = [html_list_items(v) for v in values]
    if limit and limit > 0:
        # Vast aantal kolommen: blijven ook bestaan als ze overal leeg zijn.
        count = limit
    else:
        count = max((len(i) for i in items), default=0)
    headers = ['%s%d' % (prefix, n + 1) for n in range(count)]
    cells = [(i + [''] * count)[:count] for i in items]
    return headers, cells


def expand_columns(labels, rows, specs):
    """Klapt kolommen uit volgens specs.

    labels: kolomtitels
    rows:   rijen (lists), uitgelijnd met labels
    specs:  even lang als labels; per kolom None (ongewijzigd laten) of
            dict(mode='json'|'html_list', prefix='prop_', max=0)

    Een kolom met een spec wordt vervangen door de uitgeklapte kolommen.
    Geeft (labels, rows) terug.
    """
    if not specs or not any(specs):
        return labels, rows

    blocks = []  # per oorspronkelijke kolom: (headers, cellen per rij)
    for idx, label in enumerate(labels):
        spec = specs[idx] if idx < len(specs) else None
        values = [row[idx] if idx < len(row) else '' for row in rows]
        if not spec:
            blocks.append(([label], [[v] for v in values]))
            continue
        prefix = spec.get('prefix') or (slugify(label) + '_')
        mode = spec.get('mode')
        if mode == MODE_JSON:
            blocks.append(_plan_json(values, prefix))
        elif mode == MODE_HTML_LIST:
            blocks.append(_plan_html_list(values, prefix, spec.get('max') or 0))
        else:
            blocks.append(([label], [[v] for v in values]))

    new_labels = [h for headers, _cells in blocks for h in headers]
    new_rows = []
    for r in range(len(rows)):
        new_row = []
        for _headers, cells in blocks:
            new_row.extend(cells[r])
        new_rows.append(new_row)
    return new_labels, new_rows
