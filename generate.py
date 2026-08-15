#!/usr/bin/env python3
"""Iris サイト生成スクリプト"""
import json, os, re, html, urllib.parse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'data' / 'books.json').read_text(encoding='utf-8'))
LIBRARY_DATA = json.loads((ROOT / 'data' / 'library.json').read_text(encoding='utf-8'))
LIBRARY_EN_DATA = json.loads((ROOT / 'data' / 'library_en.json').read_text(encoding='utf-8'))
LIBRARY_DE_DATA = json.loads((ROOT / 'data' / 'library_de.json').read_text(encoding='utf-8'))
LIBRARY_ES_DATA = json.loads((ROOT / 'data' / 'library_es.json').read_text(encoding='utf-8'))
LIBRARY_FR_DATA = json.loads((ROOT / 'data' / 'library_fr.json').read_text(encoding='utf-8'))
LIBRARY_MULTILANG = {'de': LIBRARY_DE_DATA, 'es': LIBRARY_ES_DATA, 'fr': LIBRARY_FR_DATA}
BOOKS_BY_SLUG = {b['slug']: b for b in DATA}

SITE_NAME = 'Iris Institute'
SITE_URL = 'https://iris-institute.github.io'
SITE_TAGLINE = '世界を、体系的に読み解く。'
SITE_SUB = '国・企業・産業を、公開情報と一次資料から多角的に分析する。'

# -----------------------------------------------------------
# 共通テンプレート
# -----------------------------------------------------------
AFFILIATE_TAG = 'leonjornal-22'
KU_SIGNUP_URL = f'https://www.amazon.co.jp/kindle-dbs/hz/signup?tag={AFFILIATE_TAG}'

def cover_url(asin):
    return f'https://m.media-amazon.com/images/P/{asin}._SL500_.jpg'

def amazon_url(asin):
    return f'https://www.amazon.co.jp/dp/{asin}?tag={AFFILIATE_TAG}'

AFFILIATE_TAG_COM = 'iris0c8-20'

def amazon_url_com(asin):
    return f'https://www.amazon.com/dp/{asin}?tag={AFFILIATE_TAG_COM}'

AFFILIATE_TAG_UK = 'iris08de-21'

def amazon_url_uk(asin):
    return f'https://www.amazon.co.uk/dp/{asin}?tag={AFFILIATE_TAG_UK}'

AFFILIATE_TAGS_MULTILANG = {'de': 'iris018-21', 'es': 'iris08de-21', 'fr': 'iris0302-21'}

def amazon_url_lang(asin, lang):
    tag = AFFILIATE_TAGS_MULTILANG[lang]
    return f'https://www.amazon.{lang}/dp/{asin}?tag={tag}'

def hreflang_block(hmap):
    """hreflang <link> タグ群を返す"""
    return '\n'.join(f'<link rel="alternate" hreflang="{k}" href="{v}">' for k, v in hmap.items())

# トップページ hreflang（全5言語）
TOP_HREFLANG = {
    'ja':        f'{SITE_URL}/',
    'en':        f'{SITE_URL}/en/',
    'es':        f'{SITE_URL}/es/',
    'de':        f'{SITE_URL}/de/',
    'fr':        f'{SITE_URL}/fr/',
    'x-default': f'{SITE_URL}/en/',
}

# Japanライブラリ hreflang（EN/DE/ES/FR）
JAPAN_LIB_HREFLANG = {
    'en':        f'{SITE_URL}/en/library/japan/',
    'de':        f'{SITE_URL}/de/library/japan/',
    'es':        f'{SITE_URL}/es/library/japan/',
    'fr':        f'{SITE_URL}/fr/library/japan/',
    'x-default': f'{SITE_URL}/en/library/japan/',
}

def lang_switcher(current_lang):
    """言語切替ドロップダウン（<details>ベース、CSSのみ）"""
    labels = {'ja': '日本語', 'en': 'EN', 'es': 'ES', 'de': 'DE', 'fr': 'FR'}
    names  = {'ja': '日本語', 'en': 'English', 'es': 'Español', 'de': 'Deutsch', 'fr': 'Français'}
    roots  = {'ja': '{ROOT}/', 'en': '{ROOT}/en/', 'es': '{ROOT}/es/', 'de': '{ROOT}/de/', 'fr': '{ROOT}/fr/'}
    items = ''
    for code in ('ja', 'en', 'es', 'de', 'fr'):
        cls = ' class="lang-active"' if code == current_lang else ''
        items += f'<a href="{roots[code]}"{cls}>{names[code]}</a>'
    return f'<div class="lang-switcher"><details><summary>{labels[current_lang]}</summary><div class="lang-dropdown">{items}</div></details></div>'

def head(title, description, canonical, og_image=None, extra_head='', lang='ja', omit_meta_description=False):
    og_image = og_image or f'{SITE_URL}/assets/og-default.png'
    sw = lang_switcher(lang)
    if lang == 'en':
        nav_links = '''<a href="{ROOT}/en/">Books</a>
<a href="{ROOT}/en/library/">Library</a>
<a href="{ROOT}/en/about.html">About</a>'''
        home_link = '{ROOT}/en/'
    elif lang == 'es':
        nav_links = '''<a href="{ROOT}/es/">Libros</a>
<a href="{ROOT}/es/library/">Biblioteca</a>
<a href="{ROOT}/es/about.html">Acerca de</a>'''
        home_link = '{ROOT}/es/'
    elif lang == 'de':
        nav_links = '''<a href="{ROOT}/de/">Bücher</a>
<a href="{ROOT}/de/library/">Bibliothek</a>
<a href="{ROOT}/de/about.html">Über uns</a>'''
        home_link = '{ROOT}/de/'
    elif lang == 'fr':
        nav_links = '''<a href="{ROOT}/fr/">Livres</a>
<a href="{ROOT}/fr/library/">Bibliothèque</a>
<a href="{ROOT}/fr/about.html">À propos</a>'''
        home_link = '{ROOT}/fr/'
    else:
        nav_links = '''<a href="{ROOT}/">書籍一覧</a>
<a href="{ROOT}/library/">Iris Libraries</a>
<a href="{ROOT}/about.html">Irisについて</a>'''
        home_link = '{ROOT}/'
    nav = nav_links + '\n' + sw
    meta_desc = '' if omit_meta_description else f'<meta name="description" content="{html.escape(description)}">\n'
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KW6PM4RJMW"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'G-KW6PM4RJMW');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="uqFJXxp03hN8A0h1ZLQQzcdm6wi5rEI5cBX0iU28K8U" />
<title>{html.escape(title)}</title>
{meta_desc}<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" href="{{ROOT}}/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{{ROOT}}/assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="{{ROOT}}/assets/favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="{{ROOT}}/assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{{ROOT}}/assets/style.css">
{extra_head}
</head>
<body>
<header class="site-header">
<div class="container">
<div class="site-title"><a href="{home_link}">{SITE_NAME}</a></div>
<nav class="site-nav">
{nav}
</nav>
</div>
</header>
'''

def footer(lang='ja'):
    year = datetime.now().year
    if lang == 'en':
        links = f'''<a href="{{ROOT}}/en/">Books</a>
<a href="{{ROOT}}/en/about.html">About</a>
<a href="{{ROOT}}/privacy.html">Privacy</a>'''
    elif lang == 'es':
        links = f'''<a href="{{ROOT}}/es/">Libros</a>
<a href="{{ROOT}}/es/about.html">Acerca de</a>
<a href="{{ROOT}}/privacy.html">Privacidad</a>'''
    elif lang == 'de':
        links = f'''<a href="{{ROOT}}/de/">Bücher</a>
<a href="{{ROOT}}/de/about.html">Über uns</a>
<a href="{{ROOT}}/privacy.html">Datenschutz</a>'''
    elif lang == 'fr':
        links = f'''<a href="{{ROOT}}/fr/">Livres</a>
<a href="{{ROOT}}/fr/about.html">À propos</a>
<a href="{{ROOT}}/privacy.html">Confidentialité</a>'''
    else:
        links = f'''<a href="{{ROOT}}/">書籍一覧</a>
<a href="{{ROOT}}/about.html">Irisについて</a>
<a href="{{ROOT}}/privacy.html">プライバシーポリシー</a>'''
    return f'''
<footer class="site-footer">
<div class="container">
<div>
<div class="footer-brand">{SITE_NAME}</div>
<div class="footer-copyright">© {year} {SITE_NAME}. All rights reserved.</div>
</div>
<div class="footer-links">
{links}
</div>
</div>
</footer>
</body>
</html>'''

def render(html_src, depth=0):
    """相対パス解決（depth=0はルート、1はサブディレクトリ）"""
    root = '/'.join(['..'] * depth) if depth else '.'
    return html_src.replace('{ROOT}', root)

# -----------------------------------------------------------
# トップページ
# -----------------------------------------------------------
def render_card(b, detail_prefix='books/'):
    detail_url = f"{detail_prefix}{b['slug']}.html"
    cover = cover_url(b['asin'])
    amazon = amazon_url(b['asin'])
    classes = f"book-card cat-{b['category']} lang-{b['lang']}"
    return f'''<article class="{classes}">
<a href="{detail_url}" class="book-title-link">
<div class="book-cover"><img src="{cover}" alt="{html.escape(b['title'])} 表紙" loading="lazy"></div>
<h2 class="book-title">{html.escape(b['title'])}</h2>
</a>
<p class="book-short">{html.escape(b['short'])}</p>
<div class="book-actions">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">Amazonで見る</a>
<a href="{detail_url}" class="link-detail">本の詳細を見る</a>
</div>
</article>'''

def build_index():
    # 注目書籍（手動指定）
    FEATURED_SLUGS = ['pacific-war', 'asean-history', 'asean-culture', 'asean-economy']
    featured = [next(b for b in DATA if b['slug'] == s) for s in FEATURED_SLUGS]
    featured_cards = ''.join(render_card(b, 'books/') for b in featured)

    # 地域カテゴリー（/books/ と同じ定義を再現）
    CATEGORIES = [
        ('southeast-asia', '東南アジア', 'タイ・ベトナム・インドネシア他9カ国＋ASEAN横串', lambda b: '東南アジア' in b.get('tags', []) and b['lang'] == 'ja'),
        ('east-asia', '東アジア', '中国・台湾・香港・韓国・北朝鮮', lambda b: '東アジア' in b.get('tags', []) and b['lang'] == 'ja'),
        ('south-asia', '南アジア', 'インド・ネパール', lambda b: '南アジア' in b.get('tags', []) and b['lang'] == 'ja'),
        ('europe', 'ヨーロッパ', 'ロシア・ウクライナ・ドイツ・イギリス他', lambda b: 'ヨーロッパ' in b.get('tags', []) and b['lang'] == 'ja'),
        ('americas', '北米・中南米', 'アメリカ・カナダ・メキシコ・ベネズエラ', lambda b: ('北米' in b.get('tags', []) or '中南米' in b.get('tags', [])) and b['lang'] == 'ja'),
        ('oceania', 'オセアニア', 'オーストラリア', lambda b: 'オセアニア' in b.get('tags', []) and b['lang'] == 'ja'),
        ('themes', 'テーマ書', '仏教・世界遺産・太平洋戦争・生成AI・投資分野', lambda b: (not any(t in b.get('tags', []) for t in ['東南アジア', '東アジア', '南アジア', 'ヨーロッパ', '北米', '中南米', 'オセアニア'])) and b['lang'] == 'ja'),
    ]

    cat_cards = []
    total_ja = 0
    for cid, ctitle, cdesc, cmatch in CATEGORIES:
        count = sum(1 for b in DATA if cmatch(b))
        if count == 0:
            continue
        total_ja += count
        cat_cards.append(f'''<a href="books/#{cid}" class="cat-card">
<div class="cat-card-header">
<span class="cat-card-title">{ctitle}</span>
<span class="cat-card-count">{count}冊</span>
</div>
<p class="cat-card-desc">{cdesc}</p>
</a>''')

    body = f'''
<main>
<section class="hero hero-large">
<div class="container">
<h1>{SITE_TAGLINE}</h1>
<p class="hero-sub">{SITE_SUB}</p>
<p class="hero-desc">Iris Instituteは、国・地域・産業を歴史・地理・文化・政治・経済といった複数の視点から体系的に読み解く書籍を制作している独立系の出版・研究プロジェクトです。政府統計・国際機関の資料・現地の一次資料を土台に、ニュースの断片や旅行ガイドでは見えてこない「構造」を提示することを目指しています。</p>
<div class="hero-stats">
<span class="hero-stat"><strong>{total_ja + 2}</strong> 冊刊行</span>
<span class="hero-stat"><strong>7</strong> 地域・テーマ</span>
<span class="hero-stat"><strong>5</strong> 言語対応</span>
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>注目の書籍</h2>
<p>編集部が特にお勧めする4冊。</p>
</div>
<div class="books-grid">
{featured_cards}
</div>
</div>
</section>

<section class="section-categories">
<div class="container">
<div class="section-heading">
<h2>地域・テーマから探す</h2>
<p>刊行済みの書籍を地域とテーマで整理しています。</p>
</div>
<div class="cat-grid">
{''.join(cat_cards)}
</div>
<div class="view-all-wrap">
<a href="books/" class="view-all-link">すべての書籍を一覧で見る →</a>
</div>
</div>
</section>
</main>
'''

    title = f'{SITE_NAME} — 世界を体系的に読み解く'
    desc = f'{SITE_TAGLINE} {SITE_SUB} 国・地域・企業を多角的に分析した書籍を出版しています。'

    # サイト全体の識別のためのWebSite/Organization構造化データ（トップページのみ）
    site_jsonld = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://iris-institute.github.io/#website",
      "url": "https://iris-institute.github.io/",
      "name": "Iris Institute",
      "alternateName": ["海外文化研究所Iris", "Iris", "iris-institute.github.io"],
      "description": "国・地域・産業を、公開情報と一次資料から多角的に分析する独立系の出版・研究プロジェクト",
      "publisher": { "@id": "https://iris-institute.github.io/#organization" },
      "inLanguage": "ja"
    },
    {
      "@type": "Organization",
      "@id": "https://iris-institute.github.io/#organization",
      "name": "Iris Institute",
      "alternateName": ["海外文化研究所Iris", "Iris"],
      "url": "https://iris-institute.github.io/",
      "logo": {
        "@type": "ImageObject",
        "url": "https://iris-institute.github.io/assets/favicon-512.png",
        "width": 512,
        "height": 512
      }
    }
  ]
}
</script>'''

    page = head(title, desc, SITE_URL + '/', extra_head=site_jsonld + '\n' + hreflang_block(TOP_HREFLANG)) + body + footer()
    (ROOT / 'index.html').write_text(render(page, 0), encoding='utf-8')
    print(f'✓ index.html (注目3冊 + {len(cat_cards)}カテゴリー)')

def build_all_books_pages():
    """/books/index.html — 地域別カテゴリーで一覧表示"""
    # カテゴリー定義（表示順・タイトル・所属判定）
    CATEGORIES = [
        {
            'id': 'southeast-asia',
            'title': '東南アジア',
            'desc': '9カ国とASEAN全体を扱う横串本のシリーズ。',
            'match': lambda b: '東南アジア' in b.get('tags', []) and b['lang'] == 'ja',
            'sub_split': True,  # 個別国 → ASEAN横串の順で分ける
        },
        {
            'id': 'east-asia',
            'title': '東アジア',
            'desc': '中国・台湾・香港・韓国・北朝鮮。',
            'match': lambda b: '東アジア' in b.get('tags', []) and b['lang'] == 'ja',
        },
        {
            'id': 'south-asia',
            'title': '南アジア',
            'desc': 'インド亜大陸の国々。',
            'match': lambda b: '南アジア' in b.get('tags', []) and b['lang'] == 'ja',
        },
        {
            'id': 'europe',
            'title': 'ヨーロッパ',
            'desc': '欧州各国とロシア・旧ソ連圏。',
            'match': lambda b: 'ヨーロッパ' in b.get('tags', []) and b['lang'] == 'ja',
        },
        {
            'id': 'americas',
            'title': '北米・中南米',
            'desc': 'アメリカ大陸の国々。',
            'match': lambda b: ('北米' in b.get('tags', []) or '中南米' in b.get('tags', [])) and b['lang'] == 'ja',
        },
        {
            'id': 'oceania',
            'title': 'オセアニア',
            'desc': 'オセアニア地域。',
            'match': lambda b: 'オセアニア' in b.get('tags', []) and b['lang'] == 'ja',
        },
        {
            'id': 'themes',
            'title': 'テーマ書',
            'desc': '国境を越えたテーマを扱う書籍。',
            'match': lambda b: (not any(t in b.get('tags', []) for t in ['東南アジア', '東アジア', '南アジア', 'ヨーロッパ', '北米', '中南米', 'オセアニア'])) and b['lang'] == 'ja',
        },
    ]

    # カテゴリー別に書籍を振り分け（新刊順）
    grouped = []
    for cat in CATEGORIES:
        books = sorted([b for b in DATA if cat['match'](b)], key=lambda b: b['date'], reverse=True)
        if not books:
            continue
        grouped.append((cat, books))

    total = sum(len(books) for _, books in grouped)

    # 目次（ジャンプナビ）
    nav_items = ''.join(
        f'<a href="#{cat["id"]}" class="cat-nav-item">{cat["title"]} <span>{len(books)}</span></a>'
        for cat, books in grouped
    )

    # カテゴリごとのセクション
    sections_html = []
    for cat, books in grouped:
        if cat.get('sub_split') and cat['id'] == 'southeast-asia':
            # ASEAN横串と個別国を分けて表示
            country_books = [b for b in books if 'ASEAN総合' not in b.get('tags', [])]
            asean_books = [b for b in books if 'ASEAN総合' in b.get('tags', [])]

            country_cards = ''.join(render_card(b, '') for b in country_books)
            asean_cards = ''.join(render_card(b, '') for b in asean_books)

            asean_block = f'''
<h3 class="cat-subheading">9カ国を横串で扱うシリーズ</h3>
<div class="books-grid">
{asean_cards}
</div>
''' if asean_books else ''

            sections_html.append(f'''
<section class="cat-section" id="{cat['id']}">
<div class="cat-header">
<h2>{cat['title']} <span class="cat-count">{len(books)}冊</span></h2>
<p class="cat-desc">{cat['desc']}</p>
</div>
<div class="books-grid">
{country_cards}
</div>
{asean_block}
</section>
''')
        else:
            cards = ''.join(render_card(b, '') for b in books)
            sections_html.append(f'''
<section class="cat-section" id="{cat['id']}">
<div class="cat-header">
<h2>{cat['title']} <span class="cat-count">{len(books)}冊</span></h2>
<p class="cat-desc">{cat['desc']}</p>
</div>
<div class="books-grid">
{cards}
</div>
</section>
''')

    body = f'''
<main>
<section class="hero">
<div class="container">
<h1>すべての書籍</h1>
<p>Iris Instituteが刊行する全{total}冊。地域・テーマ別に分類しています。</p>
</div>
</section>

<nav class="cat-nav">
<div class="container">
{nav_items}
</div>
</nav>

<div class="container books-container">
{''.join(sections_html)}
</div>

<section class="ku-cta">
<div class="container">
<h2>Kindle Unlimited で全書籍を読み放題</h2>
<p>Iris Instituteの書籍のほとんどは <strong>Kindle Unlimited 対象</strong>。月額980円で200万冊以上が読み放題、初回30日間は無料でお試しできます。</p>
<a href="{KU_SIGNUP_URL}" class="btn-amazon-large" target="_blank" rel="sponsored noopener">Kindle Unlimitedを試す</a>
</div>
</section>
</main>
'''
    page_title = f'すべての書籍 | {SITE_NAME}'
    page_desc = f'{SITE_NAME}が刊行する全{total}冊の書籍を地域・テーマ別に整理。東南アジア・東アジア・南アジア・ヨーロッパ・北米・中南米・オセアニア、そしてテーマ書のカテゴリーで分類。'
    canonical = f'{SITE_URL}/books/'
    page = head(page_title, page_desc, canonical) + body + footer()
    (ROOT / 'books' / 'index.html').write_text(render(page, 1), encoding='utf-8')
    # 古いページネーションページを削除
    for old in (ROOT / 'books').glob('page-*.html'):
        old.unlink()
    print(f'✓ /books/ カテゴリー別一覧（{len(grouped)}カテゴリー, {total}冊）')

# -----------------------------------------------------------
# 詳細ページ生成
# -----------------------------------------------------------
def seo_keywords(book):
    """複合検索キーワードを自然に含めるための素材"""
    t = book['title']
    # 「○○を読み解く」から「○○」を抽出
    m = re.match(r'^(.+?)を読み解く', t)
    if m:
        topic = m.group(1)
        return [
            f'{topic}の歴史',
            f'{topic}の経済',
            f'{topic}の文化',
            f'{topic}の政治',
            f'{topic}の地理',
            f'{topic} わかりやすく',
            f'{topic} 本',
            f'{topic}について学ぶ',
        ]
    if 'Decoding' in t:
        topic = t.replace('Decoding ', '')
        return [
            f'{topic} history',
            f'{topic} economics',
            f'{topic} book',
            f'understanding {topic}',
            f'{topic} politics',
        ]
    return []

def build_long_desc(book):
    """SEO最適化された長文説明"""
    # 個別オーバーライドがあればそれを使う（list of paragraphs）
    if book.get('long_desc'):
        return '\n'.join(f'<p>{p}</p>' for p in book['long_desc'])

    keywords = seo_keywords(book)
    title = book['title']
    short = book['short']

    if book['lang'] == 'en':
        topic = title.replace('Decoding ', '')
        return f'''
<p>{short} <em>{title}</em> is written for readers who want to understand {topic} in a structured way — not through fragments of news or travel writing, but through the underlying history, geography, culture, politics and economics that shape it today.</p>
<p>Each chapter builds on primary sources — government statistics, official disclosures and peer-reviewed research — to answer the questions that headline coverage tends to skip: how {topic} came to be what it is, what forces shape its present, and where it is heading. The book is written to be accessible to business professionals, students and general readers alike, without oversimplifying the material.</p>
<p>Available on Kindle for smartphone, tablet and PC. A companion volume to the <em>Decoding the World</em> series.</p>
'''

    # 日本語
    m = re.match(r'^(.+?)を読み解く', title)
    topic = m.group(1) if m else title

    return f'''
<p>{short}『{title}』は、{topic}を歴史・地理・文化・政治・経済の5つの視点から体系的に理解したい読者のための一冊です。</p>
<p>本書が扱うのは、ニュースの断片や旅行ガイドでは見えてこない、{topic}という国・地域を成り立たせている構造そのものです。政府統計・国際機関の公表資料・現地の一次資料を土台に、「{topic}はなぜ今の姿になったのか」「これからどこへ向かうのか」という問いに、章ごとに順を追って答えていきます。</p>
<p>ビジネスパーソンが会議前に{topic}の背景を掴む一冊としても、学生がレポートや卒論のために{topic}を深く調べる出発点としても、また旅行や移住の前に{topic}の内側を知りたい一般読者にも、読み通せる構成にしています。専門用語には初出時に説明を加えているので、{topic}についてこれから学ぶ方でも無理なく読み進められます。</p>
<p>Kindleアプリを入れたスマートフォン・タブレット・PCで、いつでも読むことができます。</p>
'''

def build_toc(book):
    """典型的な目次を提示（実際の目次はASIN別に差別化可能）"""
    if book.get('toc'):
        return '<ul>' + ''.join(f'<li>{x}</li>' for x in book['toc']) + '</ul>'
    if book['lang'] == 'en':
        topic = book['title'].replace('Decoding ', '')
        return f'''<ul>
<li>Chapter 1: History — How {topic} became what it is today</li>
<li>Chapter 2: Geography — Land, climate, and resources</li>
<li>Chapter 3: Culture — Language, religion, and society</li>
<li>Chapter 4: Politics — Government, power, and diplomacy</li>
<li>Chapter 5: Economics — Industry, trade, and future outlook</li>
</ul>'''
    m = re.match(r'^(.+?)を読み解く', book['title'])
    topic = m.group(1) if m else book['title']
    return f'''<ul>
<li>第1章　歴史——{topic}の成り立ち</li>
<li>第2章　地理——国土・気候・資源</li>
<li>第3章　文化——言語・宗教・社会</li>
<li>第4章　政治——政府・権力・外交</li>
<li>第5章　経済——産業・貿易・将来展望</li>
</ul>'''

def build_who(book):
    if book.get('who'):
        return '<ul>' + ''.join(f'<li>{x}</li>' for x in book['who']) + '</ul>'
    if book['lang'] == 'en':
        topic = book['title'].replace('Decoding ', '')
        return f'''<ul>
<li>Business professionals expanding into {topic}</li>
<li>Students and researchers studying {topic}</li>
<li>Investors evaluating {topic} markets</li>
<li>Journalists and analysts covering {topic}</li>
<li>Anyone seeking a structured, in-depth understanding of {topic}</li>
</ul>'''
    m = re.match(r'^(.+?)を読み解く', book['title'])
    topic = m.group(1) if m else book['title']
    return f'''<ul>
<li>{topic}のニュース背景を体系的に理解したいビジネスパーソン</li>
<li>{topic}への進出・投資・出張を控えている方</li>
<li>大学のレポート・卒論で{topic}について調べる学生</li>
<li>就活で{topic}関連企業・業界を志望する学生</li>
<li>{topic}のことを"わかりやすく"知りたい一般読者</li>
<li>教養として世界を体系的に学びたい社会人</li>
</ul>'''

def build_learn(book):
    if book.get('learn'):
        return '<ul>' + ''.join(f'<li>{x}</li>' for x in book['learn']) + '</ul>'
    if book['lang'] == 'en':
        topic = book['title'].replace('Decoding ', '')
        return f'''<ul>
<li>The historical events that shaped modern {topic}</li>
<li>The geographic and demographic realities of {topic}</li>
<li>The cultural codes and social structures of {topic}</li>
<li>The political system and international position of {topic}</li>
<li>The economic strengths, weaknesses, and future of {topic}</li>
</ul>'''
    m = re.match(r'^(.+?)を読み解く', book['title'])
    topic = m.group(1) if m else book['title']
    return f'''<ul>
<li>{topic}の歴史がなぜ現在の姿を作ったのか</li>
<li>{topic}の地理的条件と人口動態のリアル</li>
<li>{topic}の文化・宗教・社会の基本構造</li>
<li>{topic}の政治体制と国際的な立ち位置</li>
<li>{topic}の経済の強み・弱み・将来性</li>
</ul>'''

def json_ld(book):
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "{book['title']}",
  "description": "{book['short']}",
  "image": "{cover_url(book['asin'])}",
  "author": {{"@type": "Organization", "name": "{SITE_NAME}"}},
  "publisher": {{"@type": "Organization", "name": "{SITE_NAME}"}},
  "inLanguage": "{book['lang']}",
  "datePublished": "{book['date']}",
  "url": "{SITE_URL}/books/{book['slug']}.html",
  "workExample": {{
    "@type": "Book",
    "bookFormat": "https://schema.org/EBook",
    "isbn": "",
    "potentialAction": {{
      "@type": "ReadAction",
      "target": ["{amazon_url(book['asin'])}"]
    }}
  }}
}}
</script>'''

def build_detail(book):
    slug = book['slug']
    title = book['title']
    subtitle = book['subtitle']

    # SEO最適化タイトル・description（bookに個別指定があればそれを優先）
    if book.get('seo_title'):
        seo_title = f'{book["seo_title"]} | {SITE_NAME}'
    elif book['lang'] == 'en':
        topic = title.replace('Decoding ', '')
        seo_title = f'{title} | Understanding {topic} through 5 Lenses | {SITE_NAME}'
    else:
        m = re.match(r'^(.+?)を読み解く', title)
        topic = m.group(1) if m else title
        seo_title = f'{title} | {topic}の歴史・経済・文化を体系的に学ぶ | {SITE_NAME}'

    if book.get('seo_desc'):
        seo_desc = book['seo_desc']
    elif book['lang'] == 'en':
        topic = title.replace('Decoding ', '')
        seo_desc = f'{title}: {book["short"]} A comprehensive analysis of {topic} through history, geography, culture, politics and economics. Kindle edition available.'
    else:
        m = re.match(r'^(.+?)を読み解く', title)
        topic = m.group(1) if m else title
        seo_desc = f'{title}——{book["short"]} {topic}の歴史・地理・文化・政治・経済を5つの視点で分析。Kindle Unlimited対応。'

    canonical = f'{SITE_URL}/books/{slug}.html'
    cover = cover_url(book['asin'])
    amazon = amazon_url(book['asin'])

    # UI 言語切替（英語書籍は英語UIで表示）
    is_en = book['lang'] == 'en'
    L = {
        'cover_alt_suffix': 'cover' if is_en else '表紙',
        'buy_kindle': 'Buy on Kindle' if is_en else 'Kindleで購入',
        'view_on_amazon': 'View on Amazon' if is_en else 'Amazonで見る',
        'book_details': 'Book details' if is_en else '本の詳細を見る',
        'what_learn': 'What you will learn' if is_en else 'この本で分かること',
        'about_book': 'About this book' if is_en else '本の紹介',
        'toc': 'Table of contents' if is_en else '主な目次',
        'who_for': 'Who this book is for' if is_en else 'こんな人におすすめ',
        'read_on_kindle': 'Read on Kindle' if is_en else 'Kindleで読む',
        'related': 'Related books' if is_en else '関連書籍',
        'ku_hint': (
            'Kindle Unlimited includes over 2 million titles including our books. ¥980/month, free for the first 30 days.'
            if is_en else
            'Kindle Unlimited に登録すると、Iris Instituteの書籍を含む200万冊以上が読み放題。月額980円・初回30日間無料。'
        ),
        'ku_cta': 'Try Kindle Unlimited →' if is_en else 'Kindle Unlimitedを試す →',
    }

    # 地域・カテゴリー表示のローカライズ
    if is_en:
        cat_label = {'English': 'English', '世界': 'World', '企業': 'Companies',
                     '投資・ビジネス': 'Investment & Business', 'その他': 'Other'}.get(book['category'], book['category'])
        region_label = {'アジア': 'Asia', 'ヨーロッパ': 'Europe', '北米・中南米': 'Americas',
                        'その他': 'Global'}.get(book['region'], book['region'])
        meta_line = f'{cat_label} / {region_label}'
    else:
        meta_line = f"{book['category']} ／ {book['region']}"

    # 関連書籍：同言語のみをハードフィルタし、タグ重複数でスコアリング
    same_lang = [b for b in DATA if b['lang'] == book['lang'] and b['slug'] != slug]
    def score(other):
        return len(set(book.get('tags', [])) & set(other.get('tags', [])))
    ranked = sorted(same_lang, key=lambda x: (score(x), x['date']), reverse=True)
    related = ranked[:4]
    related_cards = []
    for r in related:
        related_cards.append(f'''<article class="book-card">
<a href="{r['slug']}.html" class="book-title-link">
<div class="book-cover"><img src="{cover_url(r['asin'])}" alt="{html.escape(r['title'])}" loading="lazy"></div>
<h2 class="book-title">{html.escape(r['title'])}</h2>
</a>
<p class="book-short">{html.escape(r['short'])}</p>
<div class="book-actions">
<a href="{amazon_url(r['asin'])}" class="btn-amazon" target="_blank" rel="noopener">{L['view_on_amazon']}</a>
<a href="{r['slug']}.html" class="link-detail">{L['book_details']}</a>
</div>
</article>''')

    # 関連本が0冊ならセクション自体を非表示
    if related_cards:
        related_html = f'''
<section class="related-books">
<h2>{L['related']}</h2>
<div class="related-grid">
{''.join(related_cards)}
</div>
</section>'''
    else:
        related_html = ''

    body = f'''
<main class="book-detail">
<div class="container">
<div class="book-detail-inner">
<aside class="book-detail-cover">
<img src="{cover}" alt="{html.escape(title)} {L['cover_alt_suffix']}">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">{L['buy_kindle']}</a>
</aside>
<article>
<div class="book-detail-meta">{meta_line}</div>
<h1>{html.escape(title)}</h1>
<p class="book-subtitle">{html.escape(subtitle)}</p>

<h2>{L['what_learn']}</h2>
{build_learn(book)}

<h2>{L['about_book']}</h2>
{build_long_desc(book)}

<h2>{L['toc']}</h2>
{build_toc(book)}

<h2>{L['who_for']}</h2>
{build_who(book)}

<h2>{L['read_on_kindle']}</h2>
<p><a href="{amazon}" class="btn-amazon-large" target="_blank" rel="noopener">{L['view_on_amazon']}</a></p>
<p class="ku-hint">{L['ku_hint']}<a href="{KU_SIGNUP_URL}" target="_blank" rel="sponsored noopener">{L['ku_cta']}</a></p>
</article>
</div>

{related_html}
</div>
</main>
<div class="sticky-buy">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">{L['view_on_amazon']}</a>
</div>
'''

    # 詳細ページはメタ説明を出さず、本文冒頭からGoogleに自動抽出させる
    # OG（SNS共有）用にはbook['short']を渡す
    page = head(seo_title, book['short'], canonical, cover,
                extra_head=json_ld(book), omit_meta_description=True,
                lang=book['lang']) + body + footer(lang=book['lang'])
    (ROOT / 'books' / f'{slug}.html').write_text(render(page, 1), encoding='utf-8')

def build_all_details():
    for b in DATA:
        build_detail(b)
    print(f'✓ 詳細ページ {len(DATA)}件')

# -----------------------------------------------------------
# /en/ 英語トップページ
# -----------------------------------------------------------
def build_en_index():
    en_books = [b for b in DATA if b['lang'] == 'en']
    en_books.sort(key=lambda b: b['date'], reverse=True)

    cards = []
    for b in en_books:
        detail_url = f"../books/{b['slug']}.html"
        cover = cover_url(b['asin'])
        amazon = amazon_url(b['asin'])
        cards.append(f'''<article class="book-card">
<a href="{detail_url}" class="book-title-link">
<div class="book-cover"><img src="{cover}" alt="{html.escape(b['title'])} cover" loading="lazy"></div>
<h2 class="book-title">{html.escape(b['title'])}</h2>
</a>
<p class="book-short">{html.escape(b['short'])}</p>
<div class="book-actions">
<a href="{detail_url}" class="btn-detail">Details</a>
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">Amazon</a>
</div>
</article>''')

    body = f'''
<main>
<section class="hero">
<div class="container">
<h1>Decode the world, one country at a time.</h1>
<p>Analytical books on countries, companies and industries — built from primary sources.</p>
</div>
</section>

<section class="books-section">
<div class="container">
<div class="book-count">All {len(en_books)} books</div>
<div class="books-grid">
{''.join(cards)}
</div>
</div>
</section>
</main>
'''

    title = f'{SITE_NAME} — Analytical books on countries, companies and industries'
    desc = f'{SITE_NAME} publishes structured, primary-source-based books on countries, companies and industries. The Decoding the World Series analyzes each subject through history, geography, culture, politics and economics.'
    page = head(title, desc, SITE_URL + '/en/', lang='en', extra_head=hreflang_block(TOP_HREFLANG)) + body + footer(lang='en')
    (ROOT / 'en').mkdir(exist_ok=True)
    (ROOT / 'en' / 'index.html').write_text(render(page, 1), encoding='utf-8')
    print(f'✓ en/index.html ({len(en_books)} books)')

def build_en_about():
    body = '''
<main class="page-content container">
<h1>About Iris Institute</h1>

<p>Iris Institute is an independent publishing and research project producing analytical books that decode countries, companies and industries in a structured way.</p>

<h2>What we do</h2>
<p>We take one subject — a country, a company, an industry — and analyze it through multiple lenses: history, geography, culture, politics, economics, strategy, finance. Each book answers the structural questions news headlines and industry reports leave open: <em>why is it the way it is, and where is it going?</em> All work is built from primary sources: government statistics, filings, peer-reviewed research, and official disclosures.</p>

<h2>Editorial principles</h2>
<ul>
<li>Prefer primary sources over secondary commentary</li>
<li>Present structure and logic rather than praise or condemnation</li>
<li>Explain every technical term at first use</li>
<li>Not just numbers — always what the numbers mean</li>
<li>Give the same weight to failures, contradictions and challenges as to successes</li>
</ul>

<h2>Series</h2>
<ul>
<li><strong>Decoding the World Series</strong> — Country and region analysis through five lenses</li>
<li><strong>Company Series</strong> (upcoming) — Major companies analyzed through six lenses</li>
<li><strong>Investment &amp; Business Series</strong> (upcoming) — Practical books on real estate, crypto, generative AI</li>
</ul>

<h2>Contact</h2>
<p>For inquiries, please reach us via the Amazon author page.</p>
</main>
'''
    page = head(f'About | {SITE_NAME}', f'About {SITE_NAME}: our activities, editorial principles and book series.', SITE_URL + '/en/about.html', lang='en') + body + footer(lang='en')
    (ROOT / 'en' / 'about.html').write_text(render(page, 1), encoding='utf-8')
    print('✓ en/about.html')

# -----------------------------------------------------------
# 多言語サイト（ES / DE / FR）
# -----------------------------------------------------------
_LANG_CONF = {
    'es': {
        'dir': 'es',
        'hero': 'Decodifica el mundo, un país a la vez.',
        'hero_sub': 'Libros analíticos sobre países, empresas e industrias — basados en fuentes primarias.',
        'coming_h': 'Próximamente',
        'coming_p': 'Estamos preparando nuestra colección en español. Mientras tanto, los libros en inglés están disponibles en la <a href="{ROOT}/en/">edición en inglés</a>.',
        'site_title': f'{SITE_NAME} — Libros analíticos sobre países, empresas e industrias',
        'site_desc': f'{SITE_NAME} publica libros estructurados basados en fuentes primarias sobre países, empresas e industrias.',
        'lib_hero': 'Iris Libraries',
        'lib_sub': '10 libros esenciales por tema',
        'lib_coming': 'Próximamente — Estamos preparando nuestras bibliotecas temáticas en español.',
        'lib_crumb': '← Iris Libraries',
        'books_label': 'libros',
        'affiliate_note': 'Como Asociado de Amazon, me beneficio de las compras adscritas.',
        'amazon_btn': 'Amazon.es',
        'about_h1': 'Acerca de Iris Institute',
        'about_body': '''<p>Iris Institute es un proyecto editorial e investigación independiente que produce libros analíticos para decodificar países, empresas e industrias de manera estructurada.</p>
<h2>Qué hacemos</h2>
<p>Tomamos un tema — un país, una empresa, una industria — y lo analizamos a través de múltiples lentes: historia, geografía, cultura, política, economía, estrategia, finanzas. Cada libro responde las preguntas estructurales que los titulares de noticias y los informes de la industria dejan abiertas: <em>¿por qué es así y hacia dónde va?</em></p>
<h2>Principios editoriales</h2>
<ul>
<li>Preferir fuentes primarias sobre comentarios secundarios</li>
<li>Presentar estructura y lógica en lugar de elogios o condenas</li>
<li>Explicar cada término técnico en su primer uso</li>
<li>No solo números — siempre qué significan los números</li>
</ul>
<h2>Contacto</h2>
<p>Para consultas, contáctenos a través de la página de autor de Amazon.</p>''',
        'about_title': f'Acerca de | {SITE_NAME}',
        'about_desc': f'Acerca de {SITE_NAME}: nuestras actividades, principios editoriales y series de libros.',
    },
    'de': {
        'dir': 'de',
        'hero': 'Entschlüsseln Sie die Welt, ein Land nach dem anderen.',
        'hero_sub': 'Analytische Bücher über Länder, Unternehmen und Branchen — auf Primärquellen basierend.',
        'coming_h': 'Demnächst',
        'coming_p': 'Wir bereiten unsere deutschsprachige Kollektion vor. In der Zwischenzeit stehen englischsprachige Bücher in der <a href="{ROOT}/en/">englischen Ausgabe</a> zur Verfügung.',
        'site_title': f'{SITE_NAME} — Analytische Bücher über Länder, Unternehmen und Branchen',
        'site_desc': f'{SITE_NAME} veröffentlicht strukturierte, auf Primärquellen basierende Bücher über Länder, Unternehmen und Branchen.',
        'lib_hero': 'Iris Libraries',
        'lib_sub': '10 wesentliche Bücher pro Thema',
        'lib_coming': 'Demnächst — Wir bereiten unsere thematischen Bibliotheken auf Deutsch vor.',
        'lib_crumb': '← Iris Libraries',
        'books_label': 'Bücher',
        'affiliate_note': 'Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.',
        'amazon_btn': 'Amazon.de',
        'about_h1': 'Über Iris Institute',
        'about_body': '''<p>Iris Institute ist ein unabhängiges Verlags- und Forschungsprojekt, das analytische Bücher produziert, die Länder, Unternehmen und Branchen auf strukturierte Weise entschlüsseln.</p>
<h2>Was wir tun</h2>
<p>Wir nehmen ein Thema — ein Land, ein Unternehmen, eine Branche — und analysieren es durch mehrere Linsen: Geschichte, Geographie, Kultur, Politik, Wirtschaft, Strategie, Finanzen. Jedes Buch beantwortet die strukturellen Fragen, die Nachrichtenschlagzeilen und Branchenberichte offen lassen: <em>Warum ist es so, wie es ist, und wohin geht es?</em></p>
<h2>Redaktionelle Grundsätze</h2>
<ul>
<li>Primärquellen gegenüber sekundären Kommentaren bevorzugen</li>
<li>Struktur und Logik statt Lob oder Verurteilung präsentieren</li>
<li>Jeden Fachbegriff bei der ersten Verwendung erklären</li>
<li>Nicht nur Zahlen — immer auch deren Bedeutung</li>
</ul>
<h2>Kontakt</h2>
<p>Für Anfragen wenden Sie sich bitte über die Amazon-Autorenseite an uns.</p>''',
        'about_title': f'Über uns | {SITE_NAME}',
        'about_desc': f'Über {SITE_NAME}: unsere Aktivitäten, redaktionellen Grundsätze und Buchreihen.',
    },
    'fr': {
        'dir': 'fr',
        'hero': 'Décryptez le monde, un pays à la fois.',
        'hero_sub': 'Des livres analytiques sur les pays, les entreprises et les secteurs — fondés sur des sources primaires.',
        'coming_h': 'Bientôt disponible',
        'coming_p': 'Nous préparons notre collection en français. En attendant, les livres en anglais sont disponibles dans l\'<a href="{ROOT}/en/">édition anglaise</a>.',
        'site_title': f'{SITE_NAME} — Livres analytiques sur les pays, les entreprises et les secteurs',
        'site_desc': f'{SITE_NAME} publie des livres structurés, fondés sur des sources primaires, sur les pays, les entreprises et les secteurs.',
        'lib_hero': 'Iris Libraries',
        'lib_sub': '10 livres essentiels par thème',
        'lib_coming': 'Bientôt disponible — Nous préparons nos bibliothèques thématiques en français.',
        'lib_crumb': '← Iris Libraries',
        'books_label': 'livres',
        'affiliate_note': 'En tant que partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.',
        'amazon_btn': 'Amazon.fr',
        'about_h1': "À propos d'Iris Institute",
        'about_body': '''<p>Iris Institute est un projet éditorial et de recherche indépendant qui produit des livres analytiques décodant les pays, les entreprises et les secteurs de manière structurée.</p>
<h2>Ce que nous faisons</h2>
<p>Nous prenons un sujet — un pays, une entreprise, un secteur — et l\'analysons à travers plusieurs prismes : histoire, géographie, culture, politique, économie, stratégie, finance. Chaque livre répond aux questions structurelles que les gros titres et les rapports sectoriels laissent sans réponse : <em>pourquoi est-ce ainsi, et où cela va-t-il ?</em></p>
<h2>Principes éditoriaux</h2>
<ul>
<li>Préférer les sources primaires aux commentaires secondaires</li>
<li>Présenter la structure et la logique plutôt que l\'éloge ou la condamnation</li>
<li>Expliquer chaque terme technique à sa première utilisation</li>
<li>Pas seulement des chiffres — toujours ce que signifient les chiffres</li>
</ul>
<h2>Contact</h2>
<p>Pour toute demande, contactez-nous via la page auteur Amazon.</p>''',
        'about_title': f'À propos | {SITE_NAME}',
        'about_desc': f"À propos d'{SITE_NAME} : nos activités, principes éditoriaux et séries de livres.",
    },
}

def build_lang_index(lang):
    c = _LANG_CONF[lang]
    body = f'''
<main>
<section class="hero">
<div class="container">
<h1>{c["hero"]}</h1>
<p>{c["hero_sub"]}</p>
</div>
</section>
<section class="books-section">
<div class="container">
<div class="lang-coming-soon">
<h2>{c["coming_h"]}</h2>
<p>{c["coming_p"]}</p>
</div>
</div>
</section>
</main>
'''
    page = head(c['site_title'], c['site_desc'], f'{SITE_URL}/{lang}/', lang=lang, extra_head=hreflang_block(TOP_HREFLANG)) + body + footer(lang=lang)
    out_dir = ROOT / lang
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 1), encoding='utf-8')
    print(f'✓ {lang}/index.html')

def build_lang_about(lang):
    c = _LANG_CONF[lang]
    body = f'''
<main class="page-content container">
<h1>{c["about_h1"]}</h1>
{c["about_body"]}
</main>
'''
    page = head(c['about_title'], c['about_desc'], f'{SITE_URL}/{lang}/about.html', lang=lang) + body + footer(lang=lang)
    (ROOT / lang / 'about.html').write_text(render(page, 1), encoding='utf-8')
    print(f'✓ {lang}/about.html')

def build_lang_library_index(lang, lib_data):
    c = _LANG_CONF[lang]
    if lib_data:
        cards = []
        for ldef in lib_data:
            total = len(ldef['books'])
            cards.append(f'''<a href="{{ROOT}}/{lang}/library/{ldef["slug"]}/" class="lib-index-card">
<h3 class="lib-index-title">{html.escape(ldef["title"])}</h3>
<p class="lib-index-meta">{total} {c["books_label"]}</p>
<p class="lib-index-intro">{html.escape(ldef["intro"][:80])}…</p>
</a>''')
        content = f'<div class="lib-index-grid">{"".join(cards)}</div>'
    else:
        content = f'''<div class="lang-coming-soon">
<h2>{c["coming_h"]}</h2>
<p>{c["lib_coming"]}</p>
</div>'''
    body = f'''
<main class="lib-index-page">
<section class="hero hero-large">
<div class="container">
<h1>{c["lib_hero"]}</h1>
<p class="hero-sub">{c["lib_sub"]}</p>
</div>
</section>
<section class="lib-index-content">
<div class="container">
{content}
</div>
</section>
</main>
'''
    canonical = f'{SITE_URL}/{lang}/library/'
    page = head(f'{c["lib_hero"]} | {SITE_NAME}', c['lib_coming'], canonical, lang=lang) + body + footer(lang=lang)
    out_dir = ROOT / lang / 'library'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print(f'✓ {lang}/library/index.html')

def build_multilang_library_page(ldef, lang):
    c = _LANG_CONF[lang]
    slug = ldef['slug']
    books_html = []
    for rank, entry in enumerate(ldef['books'], 1):
        asin = entry.get('asin', '')
        if asin:
            local_url = amazon_url_lang(asin, lang)
            com_url = amazon_url_com(asin)
            btn_label = c['amazon_btn']
            cover_html = f'''<div class="lib-book-cover">
<a href="{local_url}" target="_blank" rel="noopener sponsored">
<img src="{cover_url(asin)}" alt="{html.escape(entry['title'])} cover" loading="lazy" width="100">
</a></div>'''
        else:
            local_url = ''
            com_url = ''
            btn_label = c['amazon_btn']
            cover_html = '<div class="lib-cover-placeholder"><span class="lib-cover-icon">📖</span></div>'
        meta = f'{html.escape(entry.get("pub_year",""))} · {html.escape(entry.get("publisher",""))}'
        desc = html.escape(entry.get('description', ''))
        if local_url:
            action = (f'<a href="{local_url}" class="btn-amazon" target="_blank" rel="noopener sponsored">{btn_label}</a>'
                      f'<a href="{com_url}" class="btn-amazon-intl" target="_blank" rel="noopener sponsored">Amazon.com</a>')
        else:
            action = ''
        title_url = local_url or com_url
        books_html.append(f'''<div class="lib-book-card lib-book-ext">
<div class="lib-book-rank">{rank}</div>
{cover_html}
<div class="lib-book-body">
<h3 class="lib-book-title"><a href="{title_url}" target="_blank" rel="noopener sponsored">{html.escape(entry["title"])}</a></h3>
<p class="lib-book-author">{html.escape(entry.get("author",""))}</p>
<p class="lib-book-meta">{meta}</p>
<p class="lib-book-desc">{desc}</p>
<div class="lib-book-actions">{action}</div>
</div>
</div>''')

    body = f'''
<main class="lib-page">
<section class="hero">
<div class="container">
<div class="lib-crumb"><a href="{{ROOT}}/{lang}/library/">{c["lib_crumb"]}</a></div>
<h1>{html.escape(ldef["title"])}</h1>
<p class="lib-intro">{html.escape(ldef["intro"])}</p>
</div>
</section>
<section class="lib-books-section">
<div class="container">
{"".join(books_html)}
</div>
</section>
<p class="lib-affiliate-note">{c["affiliate_note"]}</p>
</main>
'''
    canonical = f'{SITE_URL}/{lang}/library/{slug}/'
    extra = hreflang_block(JAPAN_LIB_HREFLANG) if slug == 'japan' else ''
    page = head(ldef['seo_title'], ldef['meta_desc'], canonical, lang=lang, extra_head=extra) + body + footer(lang=lang)
    out_dir = ROOT / lang / 'library' / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 3), encoding='utf-8')
    print(f'  ✓ {lang}/library/{slug}/ ({len(ldef["books"])} books)')

def build_all_multilang():
    for lang in ('es', 'de', 'fr'):
        build_lang_index(lang)
        build_lang_about(lang)
        lib_data = LIBRARY_MULTILANG[lang]
        build_lang_library_index(lang, lib_data)
        for ldef in lib_data:
            build_multilang_library_page(ldef, lang)

# -----------------------------------------------------------
# シリーズ・テーマページ（SEOハブ）
# -----------------------------------------------------------
def render_series_card(b, path_prefix='../../books/'):
    """シリーズページ用の書籍カード"""
    detail_url = f"{path_prefix}{b['slug']}.html"
    cover = cover_url(b['asin'])
    amazon = amazon_url(b['asin'])
    return f'''<article class="book-card">
<a href="{detail_url}" class="book-title-link">
<div class="book-cover"><img src="{cover}" alt="{html.escape(b['title'])} 表紙" loading="lazy"></div>
<h3 class="book-title">{html.escape(b['title'])}</h3>
</a>
<p class="book-short">{html.escape(b['short'])}</p>
<div class="book-actions">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">Amazonで見る</a>
<a href="{detail_url}" class="link-detail">本の詳細を見る</a>
</div>
</article>'''

# -----------------------------------------------------------
# シリーズページ定義（データ駆動）
# 新規追加は SERIES リストに1エントリ追加するだけで OK
# -----------------------------------------------------------
SERIES = [
    {
        'slug': 'southeast-asia',
        'seo_title': '東南アジア9カ国を国別に読み解く | 9冊シリーズ',
        'meta_desc': 'タイ・ベトナム・ラオス・カンボジア・ミャンマー・マレーシア・シンガポール・インドネシア・フィリピンの9カ国を、それぞれ1冊で。歴史・地理・文化・政治・経済の5つの視点で東南アジア各国を体系的に読み解くシリーズ。',
        'h1': '東南アジア9カ国を国別に読み解く',
        'hero_sub': 'タイ・ベトナム・インドネシアを一括りにしない。9つの国を、9冊で。',
        'hero_desc': '東南アジアは「ASEAN」というひとつの経済圏として語られがちですが、その内側には歴史も宗教も政治体制もまったく異なる9つの国が並んでいます。仏教国のタイ・ラオス・カンボジア・ミャンマー、イスラム圏のインドネシア・マレーシア、キリスト教中心のフィリピン、社会主義のベトナム、そして都市国家シンガポール。一冊で「東南アジア」を片付けようとすると、この違いが見えなくなります。Iris Instituteは、9つの国を1冊ずつ、歴史・地理・文化・政治・経済の5つの視点で書き下ろしました。',
        'sections': [
            {'kind': 'books', 'title': '大陸部（インドシナ半島）', 'desc': 'メコン川流域を中心とする5カ国。仏教文化圏でありながら、政治体制と経済発展のフェーズは大きく異なる。',
             'slugs': ['thailand', 'vietnam', 'laos', 'cambodia', 'myanmar']},
            {'kind': 'books', 'title': '海洋部・島嶼部', 'desc': 'マレー半島とその南の島々。多民族・多宗教が交わり、貿易と製造業のハブとして機能する4カ国。',
             'slugs': ['malaysia', 'singapore', 'indonesia', 'philippines']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '進出・出張前に', 'html': '赴任・出張の前に対象国の1冊を読めば、現地の商習慣や政治的な機微を掴んだ状態で入国できます。特に<a href="../../books/thailand.html">タイ</a>・<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>は日系企業の進出先として重要。'},
                {'title': '投資判断に', 'html': '株式・不動産・直接投資のいずれでも、対象国の政治リスク・為替・産業構造を理解することが第一歩。<a href="../../books/indonesia.html">インドネシア</a>（人口2.7億）と<a href="../../books/vietnam.html">ベトナム</a>（若年層豊富）は成長市場として注目。'},
                {'title': '大学のレポートに', 'html': '政治体制の比較・宗教と経済発展の関係・植民地時代の遺産など、東南アジア研究の出発点として。参考文献・出典を明示しているのでレポート作成にも使えます。'},
                {'title': '旅行前の教養として', 'html': '観光ガイドが扱わない「その国の内側」を知って旅すると、見えるものが変わります。<a href="../../books/cambodia.html">カンボジア</a>のアンコール、<a href="../../books/myanmar.html">ミャンマー</a>の民主化前後、<a href="../../books/laos.html">ラオス</a>の静けさの理由。'},
            ]},
            {'kind': 'related_books', 'title': '9カ国を横串で理解したい方へ', 'desc': '個別国ではなくASEAN全体の視点でまとめて理解したい方は、下記の横串シリーズをおすすめします。',
             'slugs': ['asean-history', 'asean-economy', 'asean-culture', 'asean-manufacturing']},
        ]
    },
    {
        'slug': 'asean',
        'seo_title': 'ASEANを学べる本 4選——歴史・経済・文化・製造業を横串で',
        'meta_desc': 'ASEAN10カ国・人口6.7億人・GDP4兆ドルの経済圏を体系的に学べる4冊。歴史・経済・文化・製造業DXという4つの視点で9カ国を貫く、ASEAN全体像の入り口。ビジネス・投資・研究の出発点として。',
        'h1': 'ASEANを学べる4冊——歴史・経済・文化・製造業DX',
        'hero_sub': 'ひとつのテーマで9カ国を貫く、ASEAN全体像の入り口。',
        'hero_desc': 'ASEANは加盟10カ国、人口6.7億人、GDP約4兆ドルという巨大な経済圏です。この規模を扱うとき、「国ごとに9冊読む」のとは別に、「ひとつのテーマで9カ国を貫いて見る」というアプローチが必要になります。歴史なら植民地支配と冷戦の影響を横並びで、経済なら産業構造とサプライチェーンを比較して、文化なら宗教・言語・食を対比しながら理解する。Iris Instituteは、そのための横串4冊を書き下ろしました。',
        'sections': [
            {'kind': 'books', 'title': 'ASEAN横串シリーズ', 'desc': 'ひとつのテーマで9カ国を貫く4冊。ビジネス・研究・進出準備のいずれにも使える構成。',
             'slugs': ['asean-history', 'asean-economy', 'asean-culture', 'asean-manufacturing']},
            {'kind': 'guide', 'title': '4冊の使い分け', 'cards': [
                {'title': 'まず全体像から', 'html': '<a href="../../books/asean-history.html">ASEANの歴史</a>から入ると、9カ国が今の姿になった背景がわかります。植民地支配・独立戦争・冷戦・ASEAN設立という共通の骨格を掴んでから、他のテーマ書に進むと理解が深まります。'},
                {'title': 'ビジネス・投資には', 'html': '<a href="../../books/asean-economy.html">ASEANの経済</a>と<a href="../../books/asean-manufacturing.html">ASEANの製造業</a>のセット。産業構造・サプライチェーン・EV/半導体シフト・スマートファクトリー化まで、投資判断や進出戦略に直結する情報が集約されています。'},
                {'title': '現地に赴任する前に', 'html': '<a href="../../books/asean-culture.html">ASEANの文化</a>で宗教・言語・食・慣習の違いを掴むと、赴任先での摩擦や誤解を減らせます。仏教国・イスラム圏・キリスト教中心国が混在する地域の商習慣を理解する助けになります。'},
                {'title': '大学の研究に', 'html': '地域研究・国際関係・開発経済の授業やレポートで、9カ国を横並びで比較する視点は評価されやすい切り口です。4冊の参考文献・データ出典もそのまま利用できます。'},
            ]},
            {'kind': 'related_books', 'title': '特定の国を深掘りしたい方へ', 'desc': '横串で全体像を掴んだあとは、対象国の1冊で深く読み込むと理解が立体化します。',
             'slugs': ['thailand', 'vietnam', 'laos', 'cambodia']},
            {'kind': 'related_series', 'links': [('southeast-asia', '9カ国シリーズ一覧を見る')]},
        ]
    },
    {
        'slug': 'east-asia',
        'seo_title': '東アジアを国別に読み解く 5冊——中国・台湾・韓国・北朝鮮・香港',
        'meta_desc': '中国・台湾・韓国・北朝鮮・香港の5カ国・地域を、それぞれ1冊で。歴史・地理・文化・政治・経済の5つの視点で東アジアを体系的に理解できる書籍シリーズ。米中対立・台湾有事・南北関係の構造も。',
        'h1': '東アジアを国別に読み解く 5冊',
        'hero_sub': '中国・台湾・韓国・北朝鮮・香港——ひとつずつ、構造から理解する。',
        'hero_desc': '日本にとって東アジアは、最も近くて最も重要で、しかし最も語られ方に偏りがある地域です。中国は「脅威」として、韓国は「反日」として、北朝鮮は「独裁」として、台湾は「有事」として、香港は「自由の喪失」として——ニュースで消費される見出しは強く、そこで理解が止まりがちです。Iris Instituteは、5つの国・地域それぞれを1冊で、歴史・地理・文化・政治・経済の5つの視点から書き下ろしました。ステレオタイプの手前にある構造を、まずは1冊で掴んでください。',
        'sections': [
            {'kind': 'books', 'title': '5冊のラインナップ', 'desc': '大陸中国と、その周辺で異なる道を歩む4つの国・地域。',
             'slugs': ['china', 'taiwan', 'hongkong', 'korea', 'north-korea']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '米中対立を理解したい', 'html': '<a href="../../books/china.html">中国</a>から入り、<a href="../../books/taiwan.html">台湾</a>で対岸の視点を、<a href="../../books/hongkong.html">香港</a>で「一国二制度」の実験の結末を確認する順が理解しやすい。'},
                {'title': '朝鮮半島情勢を掴む', 'html': '<a href="../../books/korea.html">韓国</a>と<a href="../../books/north-korea.html">北朝鮮</a>のセット。同じ民族・言語でここまで違う社会が並立している構造は、外から見ると見えにくい。両方読むと理解が立体化します。'},
                {'title': 'ビジネスで関わる方に', 'html': '<a href="../../books/china.html">中国</a>と<a href="../../books/taiwan.html">台湾</a>は半導体・EV・製造業で日本企業と深く絡む地域。政治リスクと経済リスクを構造から理解しておくと、駐在や取引の判断精度が上がります。'},
                {'title': '「なぜ違う道を歩んだか」を知る', 'html': '中国・台湾・香港・韓国・北朝鮮は、20世紀に共通の危機（帝国主義・冷戦）を経験しながら、まったく異なる政治体制と経済発展の道を選びました。5冊を並べて読むと、その分岐点が見えてきます。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('southeast-asia', '東南アジア9カ国シリーズを見る'),
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
            ]},
        ]
    },
    {
        'slug': 'international-affairs',
        'seo_title': '国際情勢・地政学を学ぶ本 6冊——世界の"今"を体系的に理解する',
        'meta_desc': '中国・台湾・北朝鮮・ロシア・ウクライナ・ジョージアなど、現代国際情勢のホットスポットを1冊ずつ体系的に読み解く書籍シリーズ。地政学の入門から、米中対立・ウクライナ戦争・台湾有事の背景まで。',
        'h1': '国際情勢・地政学を学ぶ本 6冊',
        'hero_sub': '見出しでしか語られない国を、構造で理解する。',
        'hero_desc': 'ウクライナ戦争、台湾有事の懸念、北朝鮮のミサイル、米中対立、コーカサスの緊張——国際ニュースは日々流れてきますが、その背景にある地理・歴史・体制のパターンを掴まないままだと、状況が変わるたびに理解を組み直すことになります。Iris Instituteの国別シリーズは、「今この国で何が起きているか」ではなく、「なぜ起きているか」を、歴史・地理・文化・政治・経済の5つの視点で構造化しています。以下の6冊は、現代の国際情勢を理解するうえで特に重要な国・地域を扱っています。',
        'sections': [
            {'kind': 'books', 'title': '地政学ホットスポット 6冊', 'desc': '現在の国際情勢を語るうえで避けて通れない国・地域。',
             'slugs': ['china', 'taiwan', 'north-korea', 'russia', 'ukraine', 'georgia']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': 'ウクライナ戦争の背景を掴む', 'html': '<a href="../../books/russia.html">ロシア</a>と<a href="../../books/ukraine.html">ウクライナ</a>の両方を読むと、この戦争が突発的なものではなく、千年以上の関係史と、旧ソ連圏の政治構造から生じたことがわかります。'},
                {'title': '米中対立と台湾有事', 'html': '<a href="../../books/china.html">中国</a>の内部構造と、<a href="../../books/taiwan.html">台湾</a>という「もうひとつの中国」の歴史。<a href="../../books/north-korea.html">北朝鮮</a>を加えると、東アジアの安全保障パズルの主要ピースが揃います。'},
                {'title': 'コーカサス・旧ソ連圏', 'html': '<a href="../../books/georgia.html">ジョージア</a>は、ロシアとNATO加盟国トルコの狭間にあり、コーカサス地政学を理解する鍵となる国。ウクライナと並行して読むと、旧ソ連圏の地政学が立体的に見えてきます。'},
                {'title': '地政学"入門"として', 'html': '個別国を5〜6冊読むだけで、地政学の教科書1冊よりも実感を伴った理解ができます。抽象的な理論より、具体的な国から入るほうが記憶に残ります。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('east-asia', '東アジア5カ国シリーズを見る'),
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
            ]},
        ]
    },
    {
        'slug': 'latin-america',
        'seo_title': '中南米を読み解く 3冊——メキシコ・ベネズエラ・Decoding Mexico',
        'meta_desc': 'メキシコ・ベネズエラをそれぞれ1冊で。歴史・地理・文化・政治・経済の5つの視点でラテンアメリカ主要国を体系的に理解できる書籍シリーズ。ニアショアリング・資源国家崩壊・麻薬カルテルなど現代の中南米論点を網羅。',
        'h1': '中南米を読み解く 3冊',
        'hero_sub': 'ニアショアリングで注目のメキシコ、崩壊した産油国ベネズエラ——ラテンアメリカを構造から。',
        'hero_desc': 'ラテンアメリカは日本から見て地理的に最も遠く、情報も入りにくい地域です。しかしメキシコはUSMCA体制下でアジアの製造業移転先として急浮上し、ベネズエラは世界最大の原油埋蔵量を持ちながら崩壊した国家として現代政治学の重要ケースになっています。Iris Instituteのラテンアメリカ書籍は、こうした国々を歴史・地理・文化・政治・経済の5つの視点で構造から解説しています。今後アルゼンチン・ブラジル・チリなどの主要国も順次追加予定です。',
        'sections': [
            {'kind': 'books', 'title': '現在の刊行タイトル', 'desc': 'まずはこの3冊から。今後アルゼンチン・ブラジル・チリ・パラグアイなどを追加予定。',
             'slugs': ['mexico', 'venezuela', 'decoding-mexico']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': 'ニアショアリング・製造業移転', 'html': '<a href="../../books/mexico.html">メキシコ</a>はUSMCA体制と中国からの製造業移転で急成長中。日系メーカーの新規進出先としても最有力候補。政治・治安リスクと経済ポテンシャルの両面を1冊で掴めます。'},
                {'title': '資源国家の崩壊事例', 'html': '<a href="../../books/venezuela.html">ベネズエラ</a>は、豊富な石油資源を持ちながら経済崩壊と大量難民を生んだ現代の失敗事例。政治学・開発経済学の観点でも参照される国です。'},
                {'title': '海外文献で調べる', 'html': '<a href="../../books/decoding-mexico.html">Decoding Mexico</a>は英語版。海外の研究者・ビジネスパーソンとメキシコについて議論する際に共通の参照書として使えます。'},
                {'title': 'これから追加予定', 'html': 'アルゼンチン（ミレイ政権の急進経済改革）、ブラジル（BRICS＋主要国）、チリ（リチウム大国）、パラグアイなど、南米主要国は順次刊行予定です。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
            ]},
        ]
    },
    {
        'slug': 'english-speaking',
        'seo_title': '英語圏4カ国を読み解く——アメリカ・イギリス・オーストラリア・カナダ',
        'meta_desc': 'アメリカ・イギリス・オーストラリア・カナダ、英語を公用語とする主要4カ国を、それぞれ1冊で。歴史・地理・文化・政治・経済の5つの視点で英語圏を体系的に理解できる書籍シリーズ。移住・留学・ワーホリ・駐在の判断材料に。',
        'h1': '英語圏4カ国を読み解く——アメリカ・イギリス・オーストラリア・カナダ',
        'hero_sub': '同じ英語でも、住みやすさも文化も、まったく違う4カ国。',
        'hero_desc': '日本人が「英語圏に行きたい」と考えるとき、真っ先に候補に上がるのがアメリカ・イギリス・オーストラリア・カナダの4カ国です。ただし、この4カ国は「英語が通じる」という一点を除けば、政治体制・移民政策・物価・気候・階級意識・多民族との距離感がまったく異なります。イギリスは階級社会と旧帝国の遺産を今も引きずり、アメリカは分断された超大国、カナダは多文化主義を国是に掲げ、オーストラリアはアジア太平洋の要として中国依存を再調整中。留学・ワーホリ・移住・駐在のいずれを検討するにせよ、この4カ国の"違い"を構造から理解しておくと、行き先選びの判断精度がまったく違ってきます。',
        'sections': [
            {'kind': 'books', 'title': '英語圏4カ国のラインナップ', 'desc': '英語を公用語とする主要4カ国。それぞれの成り立ちと現在地を1冊で。',
             'slugs': ['america', 'uk', 'australia', 'canada']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': 'キャリア形成・グローバル就労', 'html': '<a href="../../books/america.html">アメリカ</a>は世界最高峰の給与水準とテック覇権。<a href="../../books/uk.html">イギリス</a>はシティ・オブ・ロンドンの金融ハブ機能が今も強力。ビザ取得の難易度も含めて、産業構造と労働市場を1冊で掴んでおくべき国。'},
                {'title': '移住・永住を目指す', 'html': '<a href="../../books/canada.html">カナダ</a>と<a href="../../books/australia.html">オーストラリア</a>は移民受け入れが制度化されており、日本人の永住先として現実的な選択肢。ただし近年は移民政策が厳格化傾向にあるので、最新の政治動向を1冊で確認を。'},
                {'title': 'ワーホリで挑戦する', 'html': '4カ国すべてが日本とワーキング・ホリデー協定を締結（アメリカを除く3カ国）。<a href="../../books/uk.html">イギリス</a>・<a href="../../books/canada.html">カナダ</a>・<a href="../../books/australia.html">オーストラリア</a>は若年層の英語習得先として長年人気。生活コスト・仕事の見つけやすさは各国の経済状況で毎年変わります。'},
                {'title': '文化・階級・多民族社会を知る', 'html': 'イギリスの階級意識、アメリカの人種問題、カナダの多文化主義、オーストラリアのアジア人口比率。同じ英語圏でも社会の内側はまったく違います。「英語が通じる=同じ」と思わずに、それぞれの1冊で構造を掴んでください。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
            ]},
        ]
    },
    {
        'slug': 'buddhism',
        'seo_title': '仏教を学ぶ本と仏教国を知る 6冊',
        'meta_desc': '『仏教を読み解く』と、上座部仏教国5カ国（タイ・ラオス・カンボジア・ミャンマー・ネパール）を扱った書籍シリーズ。ブッダの教えの歴史・哲学・実践から、現代の仏教国の政治・経済・社会構造まで、仏教文化を立体的に理解できる6冊。',
        'h1': '仏教を学ぶ本と仏教国を知る 6冊',
        'hero_sub': '教えとしての仏教、社会としての仏教国——両方から仏教を理解する。',
        'hero_desc': '仏教は2500年前にインドで生まれ、東南アジア・チベット・中国・日本へと広がりました。教義として学ぶ仏教と、社会制度として機能する仏教国は、実はまったく違う姿をしています。タイでは僧侶が国家的な権威を持ち、ミャンマーでは仏教徒とロヒンギャ・ムスリムの対立が続き、ラオスでは社会主義体制と仏教が併存し、カンボジアではポル・ポト政権が破壊した僧院文化が再建されつつある。ネパールはブッダ生誕の地でありながら、ヒンドゥー教が主流。Iris Instituteは、仏教そのものを扱う1冊と、上座部仏教（南伝仏教）が根付く5カ国の書籍を用意しました。教えと社会、両方から仏教を立体的に理解できます。',
        'sections': [
            {'kind': 'books', 'title': '仏教を体系的に学ぶ', 'desc': 'ブッダの教えの歴史・哲学・実践・儀式・現代社会での意味を5つの視点で整理した1冊。',
             'slugs': ['buddhism']},
            {'kind': 'books', 'title': '上座部仏教国 5カ国', 'desc': '仏教が国教または多数派宗教として機能している国々。政治・経済・社会構造と仏教の関係を1冊ずつ。',
             'slugs': ['thailand', 'myanmar', 'cambodia', 'laos', 'nepal']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '仏教の入門として', 'html': '<a href="../../books/buddhism.html">仏教を読み解く</a>から入ると、ブッダの教えの本質・大乗と上座部の違い・日本仏教との違いが体系的に整理できます。座禅や瞑想を実践している方も、教えの背景理解が深まります。'},
                {'title': '仏教国の政治を理解する', 'html': '<a href="../../books/thailand.html">タイ</a>の王室と僧伽（サンガ）の関係、<a href="../../books/myanmar.html">ミャンマー</a>の軍事政権と仏教徒ナショナリズム、<a href="../../books/cambodia.html">カンボジア</a>のポル・ポト後の宗教復興——政教関係が独特の形で残る国々の内実を知る。'},
                {'title': '仏教巡礼・仏教遺跡を訪ねる前に', 'html': '<a href="../../books/nepal.html">ネパール</a>のルンビニ（ブッダ生誕地）、<a href="../../books/cambodia.html">カンボジア</a>のアンコール、<a href="../../books/myanmar.html">ミャンマー</a>のバガン。訪ねる前に対象国と仏教の関係を1冊読んでおくと、遺跡の見え方が変わります。'},
                {'title': '瞑想・マインドフルネスの背景を知る', 'html': '瞑想やマインドフルネス実践者にとって、その源流である上座部仏教国の社会文化を知ることは、実践への理解を深めます。<a href="../../books/thailand.html">タイ</a>・<a href="../../books/myanmar.html">ミャンマー</a>は瞑想リトリートの本場でもあります。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('southeast-asia', '東南アジア9カ国シリーズを見る'),
                ('asean', 'ASEAN横串4冊シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'semiconductor-geopolitics',
        'seo_title': '半導体地政学を読む 3冊——台湾・韓国・アメリカ',
        'meta_desc': 'TSMC（台湾）・サムスン（韓国）・エヌビディア（アメリカ）を軸に、半導体をめぐる地政学的緊張を国別に理解する書籍シリーズ。台湾有事・米中対立・日本のラピダス構想など、半導体産業と国家戦略が結びつく現在地を体系的に。',
        'h1': '半導体地政学を読む 3冊——台湾・韓国・アメリカ',
        'hero_sub': 'TSMC、サムスン、エヌビディア——半導体は国家戦略になった。',
        'hero_desc': '半導体はもはや単なる産業ではなく、国家安全保障そのものです。台湾のTSMCが世界の先端ロジック半導体の9割を握り、韓国のサムスンとSKハイニックスがメモリ市場を支配し、アメリカのエヌビディアがAI用GPUで独走している。そこに中国が国産化と輸出規制回避で挑み、日本はラピダスで先端ロジック復権を狙い、EUはEU Chips Actで独自路線を模索する。この産業構造を理解するには、各国の政治体制・産業政策・地政学的立場を1冊ずつ読むのが結局は最短ルートです。Iris Instituteは、半導体地政学の主要プレイヤー3カ国を、それぞれ1冊で書き下ろしています（日本は英語版<a href="../../books/decoding-japan.html">Decoding Japan</a>で言及）。',
        'sections': [
            {'kind': 'books', 'title': '半導体を握る3カ国', 'desc': '先端半導体のグローバルサプライチェーンを構成する主要国。それぞれの産業構造と国家戦略を1冊で。',
             'slugs': ['taiwan', 'korea', 'america']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '台湾有事のリスクを掴む', 'html': '<a href="../../books/taiwan.html">台湾</a>から入ると、TSMCがなぜ台湾に集中しているのか、有事の際に世界のサプライチェーンがどう壊れるのかが構造的に理解できます。米中対立を追う人の必読書。'},
                {'title': '米中半導体戦争を追う', 'html': '<a href="../../books/america.html">アメリカ</a>のCHIPS法・輸出規制と、それに対する中国の対応。エヌビディアを軸にした産業覇権の背景と、なぜアメリカが半導体を国家安全保障に格上げしたかがわかります。'},
                {'title': 'メモリ・OSATの視点で', 'html': '<a href="../../books/korea.html">韓国</a>のサムスン・SKハイニックスは、メモリ半導体で世界を支配。財閥主導の産業構造と、中国メモリ企業の追い上げに対する韓国の戦略を1冊で。'},
                {'title': '日本のラピダス構想を評価する', 'html': '日本はラピダス（2nm量産）・TSMC熊本・キオクシアで半導体復権を目指しています。日本の産業政策の実力を評価するには、台湾・韓国・アメリカの現在地との比較が不可欠。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('east-asia', '東アジア5カ国シリーズを見る'),
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
            ]},
        ]
    },
    {
        'slug': 'brics-plus',
        'seo_title': 'BRICS+を読む 3冊——中国・ロシア・インド',
        'meta_desc': '中国・ロシア・インドを、それぞれ1冊で。米国主導の国際秩序に対抗する新興国連合BRICS+の主要プレイヤーを、歴史・地理・文化・政治・経済の5つの視点で体系的に理解する書籍シリーズ。ブラジル・南アフリカは今後刊行予定。',
        'h1': 'BRICS+を読む 3冊——中国・ロシア・インド',
        'hero_sub': '西側主導の世界に対抗する新興国連合。その中核3カ国を1冊ずつ。',
        'hero_desc': 'BRICS+は、中国・ロシア・インド・ブラジル・南アフリカに、2024年以降イラン・エジプト・エチオピア・UAEなどが加わった新興国連合です。人口では世界の45%超、GDPではG7を上回る規模となり、米国主導の国際秩序に対抗する枠組みとして急速に存在感を増しています。ただし内部は決して一枚岩ではなく、中国とインドは国境紛争を抱え、ロシアとインドの関係は複雑で、脱ドル化の実現度も国によって温度差があります。Iris Instituteは、BRICS+の中核3カ国（中国・ロシア・インド）を、それぞれ1冊で書き下ろしました。ブラジル・南アフリカも今後刊行予定です。',
        'sections': [
            {'kind': 'books', 'title': 'BRICS中核3カ国', 'desc': '人口・GDP・国際的影響力で圧倒的な3カ国。それぞれの内部構造と国際戦略を1冊ずつ。',
             'slugs': ['china', 'russia', 'india']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '"脱ドル化"の実態を掴む', 'html': '<a href="../../books/china.html">中国</a>と<a href="../../books/russia.html">ロシア</a>から入ると、なぜ両国が人民元・ルーブル決済を推進するのか、SWIFT代替システムの現状はどうかが構造から理解できます。'},
                {'title': 'グローバルサウスの視点', 'html': '<a href="../../books/india.html">インド</a>は「戦略的自律」を掲げ、西側にもBRICSにも完全には属さない立ち位置を取っています。BRICS加盟国でありながらG7とも連携する複雑な外交スタンス。'},
                {'title': 'BRICS内部の不協和音', 'html': '中国とインドはヒマラヤ国境で軍事衝突を繰り返し、ロシアはウクライナ戦争で外交的に孤立気味。BRICSは一枚岩ではなく、3冊読むと内部の緊張関係がよく見えます。'},
                {'title': '今後の刊行予定', 'html': 'ブラジル（BRICS拡大の推進役）、南アフリカ（アフリカ大陸のBRICS代表）、イラン（2024年新規加入）などのBRICS+拡大メンバーは順次刊行予定。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
                ('east-asia', '東アジア5カ国シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'immigration-nations',
        'seo_title': '移民国家を読む 4冊——アメリカ・カナダ・オーストラリア・シンガポール',
        'meta_desc': '移民が国を作った4カ国——アメリカ・カナダ・オーストラリア・シンガポールを、それぞれ1冊で。多民族社会の統合と摩擦、移民政策の変遷、日本人が移住・留学・駐在で関わる際に理解すべき国家の成り立ちを体系的に。',
        'h1': '移民国家を読む 4冊——アメリカ・カナダ・オーストラリア・シンガポール',
        'hero_sub': '移民が"作った"国と、移民を"設計した"国。統合の哲学がまったく違う4カ国。',
        'hero_desc': '日本のような単一民族国家からは想像しにくいですが、世界には「移民が国を作った」歴史を持つ国々があります。アメリカ・カナダ・オーストラリアは17〜19世紀以降のヨーロッパ移民が土台となり、20〜21世紀にはアジア・中南米移民を大量に受け入れました。シンガポールは独立時にマレー系・華人・インド系の共存を国家設計に組み込みました。これら4カ国は「移民をどう扱うか」に国家アイデンティティが直結しており、統合の哲学（同化主義・多文化主義・実利的共存）がまったく違います。日本人が移住・留学・駐在で関わる際にも、この違いを理解しておくと、なぜ現地でこういう摩擦が起きるのかが構造的に見えてきます。',
        'sections': [
            {'kind': 'books', 'title': '移民が作った・設計した4カ国', 'desc': '移民政策と多民族社会の統合方式に、それぞれ独自の哲学を持つ4カ国。',
             'slugs': ['america', 'canada', 'australia', 'singapore']},
            {'kind': 'guide', 'title': '4カ国の統合モデル比較', 'cards': [
                {'title': 'アメリカ——同化主義から分断へ', 'html': '<a href="../../books/america.html">アメリカ</a>は「メルティングポット（人種のるつぼ）」を理想としてきたが、近年は人種・宗教・階級で分断が深まる状況。ラティーノ・アジア系人口の増加と政治的対立の背景を1冊で。'},
                {'title': 'カナダ——多文化主義の国是', 'html': '<a href="../../books/canada.html">カナダ</a>は世界で初めて「多文化主義」を国家政策に明文化した国。移民受け入れは今も積極的で、日本人の永住先としても現実的な選択肢。'},
                {'title': 'オーストラリア——ホワイトオーストラリアから多民族国家へ', 'html': '<a href="../../books/australia.html">オーストラリア</a>は白豪主義（1970年代まで）からの大転換を経て、今やアジア系人口が急増。中国系との関係を含む多民族政策の現在地。'},
                {'title': 'シンガポール——設計された多民族共存', 'html': '<a href="../../books/singapore.html">シンガポール</a>は独立時から、マレー系・華人・インド系の共存を制度として組み込んだ「設計された」多民族国家。住宅・言語・教育すべてに人種比率が制度化されている。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('english-speaking', '英語圏4カ国シリーズを見る'),
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
            ]},
        ]
    },
    {
        'slug': 'failed-states',
        'seo_title': '"崩れた国家"を読む 3冊——ベネズエラ・北朝鮮・ミャンマー',
        'meta_desc': '経済崩壊・独裁体制・軍事政権——うまくいかなかった国家の内実を、それぞれ1冊で。ベネズエラ（石油大国の崩壊）、北朝鮮（金王朝三代の独裁）、ミャンマー（軍事政権と民主化の反復）を歴史・政治・経済の5視点で構造的に理解する。',
        'h1': '"崩れた国家"を読む 3冊——ベネズエラ・北朝鮮・ミャンマー',
        'hero_sub': 'なぜ豊かな国が崩壊し、なぜ改革が反転したのか。3つのケースから学ぶ。',
        'hero_desc': '国が「崩れる」パターンにはいくつかの類型があります。ベネズエラは世界最大の石油埋蔵量を持ちながら、資源への過度な依存と社会主義的な経済統制で経済を崩壊させました。北朝鮮は金王朝三代の独裁と核開発で、意図的に国際社会から切り離された国家として存続しています。ミャンマーは民主化と軍事政権復活を繰り返し、少数民族との内戦が続く「未完の国家」です。これらは単に「かわいそうな国」として消費されるべきではなく、他国が同じ道を歩まないための重要な教訓を含んでいます。政治学・国際関係論・開発経済学のケーススタディとしても価値の高い3冊です。',
        'sections': [
            {'kind': 'books', 'title': '崩壊・独裁・停滞の3つの型', 'desc': '「失敗」の質がそれぞれ異なる3カ国。歴史・政治体制・経済構造から現在の姿を読み解く。',
             'slugs': ['venezuela', 'north-korea', 'myanmar']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '資源国家の崩壊事例', 'html': '<a href="../../books/venezuela.html">ベネズエラ</a>は「オランダ病」の典型例。豊富な石油収入への依存が製造業を潰し、社会主義的な価格統制がハイパーインフレを招いた構造は、資源国全般への警鐘となります。'},
                {'title': '独裁体制の存続メカニズム', 'html': '<a href="../../books/north-korea.html">北朝鮮</a>は「なぜ崩壊しないのか」を分析する必読ケース。核・中国・情報統制の3点で、金体制がどう存続してきたかを構造的に理解できます。'},
                {'title': '民主化の反転と少数民族問題', 'html': '<a href="../../books/myanmar.html">ミャンマー</a>は民主化→軍事クーデター（2021）→内戦という反転を経験した国。多民族国家における統治の難しさと、隣国（中国・インド）の影響を1冊で。'},
                {'title': '"どの国が次に崩れるか"を予測する', 'html': '国家崩壊のパターン（資源依存・独裁・民族対立・経済制裁）を3ケースから学ぶと、他の脆弱国家を評価する視点が身につきます。政治リスク分析・カントリーリスク評価の基礎として。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('international-affairs', '地政学・国際情勢の書籍リストを見る'),
                ('latin-america', '中南米シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'peninsula-nations',
        'seo_title': '半島の国々を読む 3冊——韓国・北朝鮮・ベトナム',
        'meta_desc': '朝鮮半島とインドシナ半島の3カ国——韓国・北朝鮮・ベトナムを、それぞれ1冊で。同じ民族・言語で分断された朝鮮半島、南北統一を果たしたベトナム。半島国家の地政学的宿命と国家統合のパターンを歴史から読み解く書籍シリーズ。',
        'h1': '半島の国々を読む 3冊——韓国・北朝鮮・ベトナム',
        'hero_sub': '分断された半島と、統一された半島——同じ20世紀を歩んだ3つの国家。',
        'hero_desc': '朝鮮半島とインドシナ半島は、20世紀に共通の運命を経験しました。冷戦下で南北に分断され、大国の代理戦争の舞台となり、それぞれ独自の統治体制を打ち立てた。ただし結末はまったく違います。韓国と北朝鮮は今も分断されたまま、体制も経済発展も対照的な道を歩みました。一方ベトナムは1975年の南北統一後、社会主義体制を維持しながら市場経済化（ドイモイ）を進め、いまや東南アジアの成長エンジンの1つとなっています。半島という地理的条件、冷戦の遺産、そして国家統合の成否——3冊を並べて読むと、20世紀後半のアジアが抱えた課題と、それぞれの解の違いが立体的に見えてきます。',
        'sections': [
            {'kind': 'books', 'title': '半島国家 3カ国', 'desc': '朝鮮半島の南北分断と、インドシナ半島の統一——3つの異なる結末を持つ国々。',
             'slugs': ['korea', 'north-korea', 'vietnam']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '分断国家の"その後"を比較する', 'html': '<a href="../../books/korea.html">韓国</a>と<a href="../../books/north-korea.html">北朝鮮</a>は同じ民族・言語で分断されて75年以上。片や先進国、片や独裁体制。同じ出発点からなぜここまで差がついたのかを2冊並べて読むと理解が深まります。'},
                {'title': '"統一"の成功例と失敗例', 'html': '<a href="../../books/vietnam.html">ベトナム</a>は1975年に南北を武力統一し、その後の経済改革（ドイモイ）で成功した稀有な事例。朝鮮半島との比較で「なぜベトナムはできて朝鮮はできなかったか」が見えてきます。'},
                {'title': '冷戦の代理戦争の傷跡', 'html': '朝鮮戦争（1950-53）とベトナム戦争（1955-75）は、冷戦下の大国代理戦争の代表例。3カ国の現在の政治体制・対米関係・対中関係の背景を歴史から掴むと、東アジア外交の理解が変わります。'},
                {'title': '社会主義国家の"生き残り方"', 'html': '<a href="../../books/north-korea.html">北朝鮮</a>（体制維持型）と<a href="../../books/vietnam.html">ベトナム</a>（市場改革型）は、社会主義体制の対照的な2つの解。同じイデオロギー出発点からなぜ別の道を選んだのか、選ばざるを得なかったのかが読み取れます。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('east-asia', '東アジア5カ国シリーズを見る'),
                ('southeast-asia', '東南アジア9カ国シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'expat-postings',
        'seo_title': '海外駐在・赴任前に読む国別書籍 10選——日系企業の主要駐在地',
        'meta_desc': 'アメリカ・中国・タイ・ベトナム・インドネシア・シンガポール・インド・ドイツ・イギリス・メキシコ——日系企業の駐在員が赴任する主要10カ国を、それぞれ1冊で。ビザ・住居・学校情報だけでは足りない「行き先の国の構造」を、赴任前に体系的に。',
        'h1': '海外駐在・赴任前に読む国別書籍 10選',
        'hero_sub': '住宅・学校・保険の情報の"次"に読むべき1冊を、国別に。',
        'hero_desc': '海外駐在の準備で必要な情報は3層あります。第1層はビザ・住居・学校・保険といった実務情報、第2層は現地の商習慣・食事・治安・気候といった生活情報、そして第3層が「その国がなぜ今の姿になっているか」という構造的理解です。第1・第2層は会社の人事部や現地スタッフ、赴任者コミュニティから得られますが、第3層——ニュースの背景を読み解くための構造理解——は体系的な本でないと掴めません。駐在期間中に現地の顧客・パートナー・同僚とまともな会話をするためには、そして家族に対して「なぜこの国がこう動いているか」を説明できるようになるためには、赴任前に1冊読んでおく価値が非常に高い。Iris Instituteは、日系企業の駐在員が赴任する主要10カ国を、それぞれ歴史・地理・文化・政治・経済の5つの視点で書き下ろしています。',
        'sections': [
            {'kind': 'books', 'title': 'アジア駐在の主要6カ国', 'desc': '日系企業のアジア駐在で圧倒的に多い主要地域。製造業・統括拠点・IT・小売など業種を問わず該当。',
             'slugs': ['china', 'thailand', 'vietnam', 'indonesia', 'singapore', 'india']},
            {'kind': 'books', 'title': '欧米・中南米の主要4カ国', 'desc': '本社機能・R&D・北米製造業移転など、非アジアの主要駐在地。',
             'slugs': ['america', 'germany', 'uk', 'mexico']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '製造業の工場駐在', 'html': '<a href="../../books/thailand.html">タイ</a>・<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>・<a href="../../books/mexico.html">メキシコ</a>は日系メーカーの4大工場駐在地。労働法・現地スタッフとの関係・サプライチェーンの実態を、政治経済の視点で理解しておくと、現場のトラブル対応の判断精度が上がります。'},
                {'title': '統括拠点・地域本社駐在', 'html': '<a href="../../books/singapore.html">シンガポール</a>はアジア統括拠点、<a href="../../books/germany.html">ドイツ</a>は欧州統括、<a href="../../books/america.html">アメリカ</a>は世界本社機能。駐在中に管轄地域全体を見る仕事が多いので、隣接国も含めて理解しておくと動きやすい。'},
                {'title': '営業・顧客対応駐在', 'html': '現地顧客との会話で、その国の政治・経済・文化の基本を知らないと会話が空回りします。特に<a href="../../books/china.html">中国</a>・<a href="../../books/india.html">インド</a>・<a href="../../books/uk.html">イギリス</a>のようにビジネス外の話題が重要な文化圏では、教養レベルの理解が信頼構築に直結。'},
                {'title': '家族帯同の赴任者向け', 'html': '配偶者・子どもと現地で暮らすなら、赴任者本人以上に「その国のことを知っている」ことが心理的安定につながります。学校選び・住居選び・生活圏の判断にも、国の構造理解は下地として重要。'},
            ]},
            {'kind': 'guide', 'title': '駐在中に活きる、ちょっと深い視点', 'cards': [
                {'title': '駐在中のニュースを読み解く', 'html': '駐在中は現地のニュースに晒される時間が長くなります。日本語のニュースサイトだけでは、その国の内側で今何が問題視されているかは掴めません。1冊読んでおくと、現地のニュースの背景がクリアに見えるようになります。'},
                {'title': '駐在員コミュニティを超えた交流', 'html': '駐在員コミュニティに閉じこもらず、現地の人・欧米駐在員・他業種の日本人と関係を作るには、日本の外の視点で「この国」を語れることが強力な武器になります。'},
                {'title': '帰任後のキャリアに活かす', 'html': '駐在は「その国の専門家」になるチャンス。感覚だけでなく、統計・制度・歴史を含めた体系的知識を持ち帰ると、帰任後のキャリアで大きな差別化要因になります。'},
                {'title': '次の赴任地の候補も見ておく', 'html': '駐在は1回で終わらないことも多い。今の駐在国だけでなく、次に打診されそうな候補国も並行して読んでおくと、辞令が出た時に即応できます。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
                ('english-speaking', '英語圏4カ国シリーズを見る'),
                ('east-asia', '東アジア5カ国シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'manufacturing',
        'seo_title': '世界の製造業を読む——主要生産拠点10カ国＋ASEAN横串',
        'meta_desc': '中国・ドイツ・タイ・韓国・台湾・ベトナム・インドネシア・マレーシア・メキシコ・インド——世界の製造業を支える主要国を、それぞれ1冊で。半導体・自動車・エレクトロニクスからニアショアリングまで、グローバル製造業の構造を国別に理解する書籍シリーズ。',
        'h1': '世界の製造業を読む——主要生産拠点10カ国＋ASEAN横串',
        'hero_sub': 'グローバルサプライチェーンの担い手を、国別に構造から理解する。',
        'hero_desc': '製造業は国境を越えたサプライチェーンで成り立っています。ドイツの精密機械、中国の量産能力、韓国・台湾の半導体、タイ・ベトナムの自動車生産、インドネシアの資源加工、メキシコのニアショアリング——これらが互いに絡み合ってひとつの製品ができる。単一の国だけを見ていては、なぜある工場がその場所にあるのか、なぜ移転が起きているのかが見えません。Iris Instituteは、世界の製造業を支える主要生産拠点10カ国を、それぞれ歴史・地理・文化・政治・経済の5つの視点で書き下ろしました。あわせてASEAN製造業を横串で扱った1冊も刊行しています。日系メーカーの調達・生産・営業担当者、投資家、経営企画、コンサルタントにとって、地に足のついた国別理解の基礎として使ってください。',
        'sections': [
            {'kind': 'books', 'title': '製造業の世界的ハブ 5カ国', 'desc': '世界のGDPと輸出を支える製造大国。自動車・半導体・機械の主要生産国。',
             'slugs': ['china', 'germany', 'thailand', 'korea', 'taiwan']},
            {'kind': 'books', 'title': '新興・ニアショアリング拠点 5カ国', 'desc': '中国依存の見直しと人件費上昇を受けて、日系メーカーの新規進出・移転先として重要度を増している国々。',
             'slugs': ['vietnam', 'indonesia', 'malaysia', 'india', 'mexico']},
            {'kind': 'related_books', 'title': 'ASEAN製造業を横串で理解する', 'desc': '9カ国それぞれの製造業を1冊にまとめた横串書。スマートファクトリー・EV・半導体シフトの最前線を東南アジア全体像で。',
             'slugs': ['asean-manufacturing']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '自動車業界の駐在・調達', 'html': '<a href="../../books/thailand.html">タイ</a>（東南アジア自動車ハブ）・<a href="../../books/mexico.html">メキシコ</a>（北米向け生産）・<a href="../../books/india.html">インド</a>（現地内需＋輸出）・<a href="../../books/germany.html">ドイツ</a>（欧州本社）の組み合わせが、自動車業界の実務に直結する主要国。EV転換で構造が変わる時期なので最新の1冊を。'},
                {'title': '半導体・エレクトロニクス', 'html': '<a href="../../books/taiwan.html">台湾</a>（TSMC）・<a href="../../books/korea.html">韓国</a>（サムスン・SKハイニックス）・<a href="../../books/malaysia.html">マレーシア</a>（後工程・OSAT）・<a href="../../books/vietnam.html">ベトナム</a>（組立）で、半導体グローバルバリューチェーンを国別に理解できます。'},
                {'title': 'チャイナプラスワン・脱中国', 'html': '<a href="../../books/china.html">中国</a>依存を減らす戦略を検討する場合、代替地として<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>・<a href="../../books/india.html">インド</a>・<a href="../../books/mexico.html">メキシコ</a>の4カ国が主要候補。それぞれのメリット・デメリットを構造から比較して、自社の戦略に落とし込めます。'},
                {'title': 'サプライチェーン全体を俯瞰', 'html': '個別国だけでなく<a href="../../books/asean-manufacturing.html">ASEAN製造業を読み解く</a>で東南アジア全体像を掴むと、部品調達・生産・出荷のネットワーク設計に活きます。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('semiconductor-geopolitics', '半導体地政学シリーズを見る'),
                ('expat-postings', '海外駐在向け書籍を見る'),
                ('asean', 'ASEAN横串4冊シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'overseas-entrepreneurship',
        'seo_title': '海外起業・スタートアップの前に読む国別書籍 11選',
        'meta_desc': 'シンガポール・香港・アメリカ・イギリス・マレーシア・ベトナム・インドネシア・タイ・インド・カナダ・オーストラリア——海外で起業・法人設立を検討する日本人が押さえておくべき国別情報。ビジネスハブから新興市場、起業家ビザ制度まで、税制と法制度の背景を国の構造から理解する。',
        'h1': '海外起業・スタートアップの前に読む国別書籍 11選',
        'hero_sub': '法人設立の手続きの"手前"にある、その国の構造を知る。',
        'hero_desc': '海外で起業しようとする日本人が最初にぶつかるのは、「どの国で始めるか」の判断です。シンガポールや香港は税制と行政効率で魅力的だが競争が激しい。アメリカ・イギリスは巨大市場だがビザと生活コストの壁が高い。ベトナム・インドネシアは成長市場だが規制と汚職のリスクを抱える。カナダ・オーストラリアはスタートアップビザで移住起業がしやすい。この判断は、税制・会社法・ビザ制度といった手続きの話だけでは決められません。その国が「どんな経済戦略を取り、どこに規制が緩く、どこに規制が厳しいのか」を国の構造から理解した上で選ぶことで、後の判断すべてが変わります。Iris Instituteは、海外起業の主要検討国11カ国を、それぞれ歴史・地理・文化・政治・経済の5つの視点で書き下ろしています。',
        'sections': [
            {'kind': 'books', 'title': 'ビジネスハブ・起業しやすい国 5カ国', 'desc': '税制・行政効率・国際性で世界的な起業拠点として機能する国。日本人の起業家・投資家が最初に検討する候補。',
             'slugs': ['singapore', 'hongkong', 'america', 'uk', 'malaysia']},
            {'kind': 'books', 'title': '成長市場で挑む 4カ国', 'desc': '人口ボーナス・消費市場拡大・製造業移転で、現地起業のチャンスが広がっている新興国。',
             'slugs': ['vietnam', 'indonesia', 'thailand', 'india']},
            {'kind': 'books', 'title': '起業ビザ・投資家ビザで移住起業 2カ国', 'desc': 'スタートアップビザ・投資家ビザ制度が整備されている国。起業と永住を両立させたい方向け。',
             'slugs': ['canada', 'australia']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '税制メリットで選ぶ', 'html': '<a href="../../books/singapore.html">シンガポール</a>（法人税17%・段階的免税）・<a href="../../books/hongkong.html">香港</a>（16.5%・オフショア所得非課税）・<a href="../../books/malaysia.html">マレーシア</a>（ラブアン制度）・<a href="../../books/uk.html">イギリス</a>（LLP・R&D税額控除）などの税制優遇制度は国の産業戦略の一部。制度の"なぜ"を理解して活用する。'},
                {'title': '巨大市場で勝負する', 'html': '<a href="../../books/america.html">アメリカ</a>は世界最大の消費市場・投資市場・人材市場。ただしEビザ・O-1ビザなど起業家向けビザは複雑で、州によって法制度も違う。<a href="../../books/india.html">インド</a>は14億人の内需市場と規制の壁を天秤にかけて判断が必要。'},
                {'title': '成長市場で先行者利益を狙う', 'html': '<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>・<a href="../../books/thailand.html">タイ</a>は日本人起業家の実績と現地日本人コミュニティが厚い国。ただし現地パートナー・法制度・汚職リスクを政治経済の視点から理解しておくことが不可欠。'},
                {'title': '起業＋永住を狙う', 'html': '<a href="../../books/canada.html">カナダ</a>（スタートアップビザ）と<a href="../../books/australia.html">オーストラリア</a>（革新的事業投資家ビザ）は、事業立ち上げが永住権につながる制度を用意。移民国家の政策と経済戦略を理解して活用する。'},
            ]},
            {'kind': 'guide', 'title': '見落とされがちな視点', 'cards': [
                {'title': 'その国の"制度が変わる速度"を掴む', 'html': '起業家が判断を誤りやすいのが、「今の制度が今後も続くか」という視点。政治体制・与党の安定性・過去の制度変更履歴を読むと、その国の制度リスクの見通しが立ちます。'},
                {'title': 'ローカル人材の質と労働慣行', 'html': '駐在ではなく起業だと、現地スタッフ採用が事業の生死を左右します。国の教育制度・労働文化・雇用の流動性は、国別書籍の「文化」「経済」章で押さえておくべき論点。'},
                {'title': '為替と資本規制', 'html': '事業で稼いだお金を海外に持ち出せるか、送金に規制はないか。<a href="../../books/china.html">中国</a>・<a href="../../books/india.html">インド</a>など資本規制が強い国では、事業の設計段階から考慮が必要。'},
                {'title': '出口戦略——事業売却・撤退', 'html': '起業は始めるだけでなく、売却・撤退の可能性も設計するもの。その国のM&A市場・IPO環境・撤退規制も、経済章から読み取れる重要情報。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
                ('expat-postings', '海外駐在向け書籍を見る'),
                ('immigration-nations', '移民国家シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'pro-japan',
        'seo_title': '親日国を読む 8冊——歴史的経緯と現代の日本観',
        'meta_desc': '台湾・タイ・ベトナム・インドネシア・フィリピン・マレーシア・インド・ジョージアを、それぞれ1冊で。「なぜその国は親日なのか」を歴史・地理・文化・政治・経済の視点から構造的に理解する書籍シリーズ。旅行・出張・進出前の教養として。',
        'h1': '親日国を読む 8冊——歴史的経緯と現代の日本観',
        'hero_sub': '「親日」の言葉の裏にある、それぞれの国の事情を1冊ずつ。',
        'hero_desc': '「親日国」という言葉はよく聞きますが、なぜその国が親日なのかは国によってまったく違います。台湾は統治時代の遺産と2011年東日本大震災の相互支援、タイは王室外交と日系企業の長年の存在、ベトナムは戦後の経済協力と若者の日本文化への憧れ、マレーシアはマハティールのルック・イースト政策、インドは日露戦争と独立運動期の日本評価、ジョージアはユーラシアの端で意外に強い日本尊敬——それぞれ歴史的経緯と現在の関係性が違います。「親日だから安心」で片付けずに、なぜ・どんな文脈でそう見えているのかを国の構造から理解すると、その国との付き合い方の深さがまったく変わります。Iris Instituteが刊行する国別書籍から、代表的な親日国8カ国を選んで紹介します。',
        'sections': [
            {'kind': 'books', 'title': '東アジア・東南アジアの親日国 6カ国', 'desc': '日系企業・観光・文化交流で日本と深く結びついている、日本人にとって身近な親日国。',
             'slugs': ['taiwan', 'thailand', 'vietnam', 'indonesia', 'philippines', 'malaysia']},
            {'kind': 'books', 'title': '南アジア・コーカサスの親日国 2カ国', 'desc': '距離は遠いが、独自の歴史的経緯や政策的背景で日本に強い親近感を持つ国。',
             'slugs': ['india', 'georgia']},
            {'kind': 'guide', 'title': '"なぜ親日か"の背景別に読む', 'cards': [
                {'title': '統治時代の遺産型', 'html': '<a href="../../books/taiwan.html">台湾</a>は50年の日本統治期に築かれたインフラ・教育・水利の記憶が今も肯定的に語られる特殊な国。世代交代しても親日感情が強く保たれている構造を、歴史章から理解できます。'},
                {'title': '戦後経済協力型', 'html': '<a href="../../books/thailand.html">タイ</a>・<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>・<a href="../../books/philippines.html">フィリピン</a>は、戦後の日本のODA・日系企業進出・技術移転が国の産業発展に貢献した記憶が土台。ビジネスの信頼と親日感情が結びついている構造。'},
                {'title': '政策的親日型', 'html': '<a href="../../books/malaysia.html">マレーシア</a>のマハティール首相（ルック・イースト政策）や、<a href="../../books/india.html">インド</a>のモディ政権の対日重視は、リーダーの戦略判断が親日を後押しした事例。政治章で背景がわかります。'},
                {'title': '意外な親日国', 'html': '<a href="../../books/georgia.html">ジョージア</a>は日本人にはあまり知られていないが、実は日本文化・技術への尊敬が強い国。ロシアとの緊張関係の中で日本を「模範的な小国」と見る視座が独特です。'},
            ]},
            {'kind': 'guide', 'title': '"親日"を過信しないための視点', 'cards': [
                {'title': '世代・地域で温度差がある', 'html': '同じ国内でも、都市部と農村部、高齢層と若年層で日本観は大きく違います。1冊読むと、「親日」がその国内でどれくらい均一なのかがわかります。'},
                {'title': '歴史問題と親日感情は別軸', 'html': '中国・韓国のように歴史問題で複雑な感情を持つ国も、日常レベルでは日本文化・日本人観光客に対して好意的だったりします。単純な"親日／反日"の二分法では捉えきれない現実。'},
                {'title': '"日本嫌い"の裏側にある事情も', 'html': '親日国とされる国でも、ビジネスの現場や政治的な場面では日本への警戒・不満があるのは自然。両面を知ってこそ、その国との関係を長続きさせられます。'},
                {'title': '"親日"は永続しない', 'html': '国民感情は世代交代・国際情勢・政治で変わります。過去に強く親日だった国が徐々に離れることも、逆もあります。今の関係を維持するには、その国の内部を理解し続けることが必要。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('southeast-asia', '東南アジア9カ国シリーズを見る'),
                ('east-asia', '東アジア5カ国シリーズを見る'),
                ('overseas-life', '海外移住・ワーホリ向け書籍を見る'),
            ]},
        ]
    },
    {
        'slug': 'financial-hubs',
        'seo_title': '世界の金融ハブ都市を読む 3冊——香港・シンガポール・イギリス',
        'meta_desc': '香港・シンガポール・イギリス——世界の金融ハブとして機能する3つの都市/国家を、それぞれ1冊で。シティ・オブ・ロンドン、アジアのハブ争い、国家安全維持法後の香港変質など、金融ハブの成立条件と現在地を歴史・政治・経済の視点から体系的に理解する書籍シリーズ。',
        'h1': '世界の金融ハブ都市を読む 3冊——香港・シンガポール・イギリス',
        'hero_sub': 'なぜそこに世界のお金が集まるのか。金融ハブの成立条件を、3都市の構造から。',
        'hero_desc': '世界の金融取引は、少数の「ハブ」に集中しています。イギリス（シティ・オブ・ロンドン）、香港、シンガポール——この3つが、時差・法制度・英語・税制・専門人材の集積という金融ハブの必要条件を歴史的に満たしてきました。ただし、この3都市の立ち位置は近年大きく揺らいでいます。香港は2020年の国家安全維持法以降、金融ハブとしての中立性を疑われるようになり、シンガポールはその代替地としてアジア資金の流入を吸収中。イギリスはBrexit後にEUとの金融パスポート制度を失い、フランクフルト・パリ・アムステルダムとの綱引きが続いています。Iris Instituteは、この3つの金融ハブを、それぞれ歴史・地理・文化・政治・経済の5つの視点で書き下ろしました。金融業界の駐在候補地選び、投資判断、資産管理拠点の検討にどうぞ。',
        'sections': [
            {'kind': 'books', 'title': '3つの金融ハブ', 'desc': '英語・法制度・時差・税制・専門人材が揃った、世界の金融取引の中枢。',
             'slugs': ['uk', 'hongkong', 'singapore']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': 'シティ・オブ・ロンドンを理解する', 'html': '<a href="../../books/uk.html">イギリス</a>はロンドンのシティが世界最大級の外国為替取引・保険・国際債券市場を持つ金融ハブ。Brexit後の位置づけ変化と、フランクフルト等との競争関係を歴史・政治章から理解できます。'},
                {'title': 'アジアのハブ争い', 'html': '<a href="../../books/hongkong.html">香港</a>と<a href="../../books/singapore.html">シンガポール</a>は長年アジア金融ハブの座を争ってきましたが、2020年以降シンガポール優位が明確に。両国を並べて読むと、なぜこの逆転が起きたかが構造から見えます。'},
                {'title': '香港変質のインパクト', 'html': '<a href="../../books/hongkong.html">香港</a>は国家安全維持法（2020年）で法治国家としての中立性が疑われ、外資系金融機関の一部撤退・アジア本社機能のシンガポール移転が加速。「一国二制度」の現在地を1冊で。'},
                {'title': 'プライベートバンキング拠点として', 'html': '<a href="../../books/singapore.html">シンガポール</a>は近年、中国・香港・インドネシア富裕層の資産の受け皿として急拡大。ファミリーオフィス制度と外為・秘密保持の枠組みは、資産管理拠点として検討する際の重要ポイント。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('immigration-nations', '移民国家シリーズを見る'),
                ('overseas-entrepreneurship', '海外起業・スタートアップシリーズを見る'),
                ('english-speaking', '英語圏4カ国シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'investment-business',
        'seo_title': '投資・ビジネス書 4選——仮想通貨・不動産・生成AI・巨大IT企業',
        'meta_desc': '仮想通貨投資・不動産投資・生成AI・Googleを、それぞれ1冊で。実務者・投資家・スタートアップに関わるすべての人が、今の変化を体系的にキャッチアップするための書籍シリーズ。歴史的経緯から現在の主要プレイヤー、投資戦略、税制まで。',
        'h1': '投資・ビジネス書 4選——仮想通貨・不動産・生成AI・巨大IT',
        'hero_sub': 'いまお金と技術が動いている領域を、実務者目線で体系化する4冊。',
        'hero_desc': '現代のビジネスと投資で「知らずには済まされない」領域が、2020年代に一気に増えました。ChatGPTやClaudeの登場で仕事の進め方が変わり、ビットコインETFの承認で仮想通貨が金融資産の主流に加わり、不動産は金利と人口動態の変化で新しい局面に入り、GoogleやAmazonといった巨大IT企業が引き続き社会インフラを握っている。断片的なニュースを追うだけでは、なぜ今それが動いているのか、どこに向かうのかは掴めません。Iris Instituteは、これら4つの領域を、それぞれ現役実務者・エンジニア視点で書き下ろした書籍を用意しています。個人投資家、事業会社の企画担当、スタートアップ関係者、コンサルタント、学生の卒論まで、幅広い読者の入門書として。',
        'sections': [
            {'kind': 'books', 'title': '投資・テクノロジー 4分野', 'desc': '今、判断精度が問われている4つの領域。それぞれ1冊で歴史と現在地を掴む。',
             'slugs': ['crypto-investment', 'real-estate-investment', 'generative-ai', 'google']},
            {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
                {'title': '仮想通貨を体系的に理解する', 'html': '<a href="../../books/crypto-investment.html">仮想通貨投資を読み解く</a>は、ビットコイン誕生の歴史から現代のDeFi、税制、投資戦略、リスク管理まで一冊で網羅。SNSの断片情報や暴騰暴落のニュースでは掴めない「本質」の部分を体系的に整理。'},
                {'title': '不動産投資を判断精度上げて始める', 'html': '<a href="../../books/real-estate-investment.html">不動産投資を読み解く</a>は法律・市場動向・利回り計算・税金・失敗パターンを構造から解説。「まず1棟目」の判断を勘ではなく分析でできるようにする実務書。'},
                {'title': '生成AIの原理と実装を理解する', 'html': '<a href="../../books/generative-ai.html">生成AIを読み解く</a>は、現役AIエンジニアがChatGPT・Claude・Geminiの原理と特徴、社会への影響を平易に解説。「LLMは何ができて何ができないのか」を業務判断できるレベルに引き上げる1冊。'},
                {'title': '巨大IT企業のビジネスモデル', 'html': '<a href="../../books/google.html">Googleを読み解く</a>は、検索・広告・AI・クラウドで世界を動かす企業の創業・事業・戦略・組織・財務・未来を6視点で分析。GAFAM分析の出発点として、あるいは競合分析のケーススタディとして。'},
            ]},
            {'kind': 'guide', 'title': '4冊を横串で読むメリット', 'cards': [
                {'title': 'テクノロジーとお金の融合を掴む', 'html': '生成AIと仮想通貨は、既存の金融・IT業界を根本から揺さぶっています。両者を並行して理解すると、フィンテック・AIエージェント経済など次に来る潮流が見えやすくなります。'},
                {'title': '実物資産×デジタル資産の視点', 'html': '<a href="../../books/real-estate-investment.html">不動産</a>（実物資産・インカム重視）と<a href="../../books/crypto-investment.html">仮想通貨</a>（デジタル資産・キャピタルゲイン重視）を対比して読むと、ポートフォリオ設計の考え方が立体化。'},
                {'title': 'AIが業界をどう変えるか', 'html': '<a href="../../books/generative-ai.html">生成AI</a>と<a href="../../books/google.html">Google</a>を並べて読むと、AI技術の"純粋な原理"と"巨大企業がそれをどう事業化しているか"の両面が見え、業界全体の勢力図が理解しやすくなります。'},
                {'title': '時代の"論点"を教養として押さえる', 'html': '4分野とも、これから10年の経済・技術・社会の主要論点。ビジネス会話で置いていかれないために、それぞれ1冊分の"最低限の教養"を持っておく価値があります。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('overseas-entrepreneurship', '海外起業・スタートアップシリーズを見る'),
                ('semiconductor-geopolitics', '半導体地政学シリーズを見る'),
                ('financial-hubs', '世界の金融ハブ都市シリーズを見る'),
            ]},
        ]
    },
    {
        'slug': 'overseas-life',
        'seo_title': '海外移住・ワーホリ・長期滞在の前に読む国別書籍 12選',
        'meta_desc': 'ワーホリ協定国7カ国（オーストラリア・カナダ・イギリス・ドイツ・韓国・台湾・香港）と、移住人気国5カ国（アメリカ・シンガポール・タイ・マレーシア・フィリピン）を、それぞれ1冊で。政治・経済・社会の構造を理解して渡航するための書籍リスト。',
        'h1': '海外移住・ワーホリ・長期滞在の前に読む国別書籍',
        'hero_sub': 'ビザや保険の情報だけでは足りない。「その国が今どうなっているか」を、赴く前に。',
        'hero_desc': 'ワーホリで1年間住むにせよ、駐在や移住で5年10年暮らすにせよ、行き先の国が今どんな政治体制で、どんな経済状況で、どんな社会問題を抱えているかを知らずに飛び込むのは、思っている以上にストレスがかかります。労働ビザの条件・物価・治安・気候といった実務情報はガイドブックや在留邦人ブログで足りますが、「なぜオーストラリアは移民に厳しくなってきているのか」「なぜドイツでは家が借りにくいのか」「シンガポールの生活コストが上がり続けている理由は何か」といった構造的な話は、体系的な本でないと掴めません。Iris Instituteの国別書籍は、そうした「行く前に理解しておきたい構造」を、歴史・地理・文化・政治・経済の5つの視点で1冊にまとめています。',
        'sections': [
            {'kind': 'books', 'title': 'ワーホリ協定国を読む（7カ国）', 'desc': '日本と<strong>ワーキング・ホリデー協定</strong>を結んでいる国のうち、Iris Instituteが刊行済みの7カ国。ビザ申請の前に、行き先の国のニュース背景を1冊で押さえておくと、現地での判断力がまったく違います。',
             'slugs': ['australia', 'canada', 'uk', 'germany', 'korea', 'taiwan', 'hongkong']},
            {'kind': 'guide', 'title': 'ワーホリ協定国 別・行き先選びの視点', 'cards': [
                {'title': '英語圏に行きたい', 'html': '<a href="../../books/australia.html">オーストラリア</a>・<a href="../../books/canada.html">カナダ</a>・<a href="../../books/uk.html">イギリス</a>の3択。物価・気候・移民政策・仕事の見つけやすさが大きく違います。'},
                {'title': 'ヨーロッパで暮らしたい', 'html': '<a href="../../books/germany.html">ドイツ</a>は英語だけでも仕事は見つかるが、生活は独語が必須。Zeitenwende以降の政策変化と住宅難の背景を知っておくと動きやすい。'},
                {'title': 'アジアで挑戦したい', 'html': '<a href="../../books/korea.html">韓国</a>・<a href="../../books/taiwan.html">台湾</a>・<a href="../../books/hongkong.html">香港</a>。日本から近く、生活文化のギャップも比較的小さい。ただし政治・経済状況は毎年変わるので、最新の1冊で確認を。'},
                {'title': '"ワーホリで何をするか"を先に考える', 'html': '語学習得・キャリア形成・費用回収・純粋な体験——目的別に最適な国は違います。行き先を決める前に、候補国の経済構造と仕事事情を1冊読むだけで判断精度が上がります。'},
            ]},
            {'kind': 'books', 'title': 'ワーホリ非対象・移住や長期滞在で人気の国（5カ国）', 'desc': 'ワーキングホリデー協定はないものの、駐在・起業・リタイアメント移住・留学で日本人に人気の国。ビザの取り方が難しい分、腰を据えて長く住む前提で読む1冊。',
             'slugs': ['america', 'singapore', 'thailand', 'malaysia', 'philippines']},
            {'kind': 'guide', 'title': '移住・長期滞在 目的別の読み方', 'cards': [
                {'title': 'キャリア形成・グローバル就労', 'html': '<a href="../../books/america.html">アメリカ</a>と<a href="../../books/singapore.html">シンガポール</a>。給与水準は世界最高峰だが、ビザ取得のハードルと生活コストも相応。産業構造と労働市場を理解して行くべき国。'},
                {'title': '物価が安く暮らしやすい', 'html': '<a href="../../books/thailand.html">タイ</a>・<a href="../../books/malaysia.html">マレーシア</a>・<a href="../../books/philippines.html">フィリピン</a>。リタイアメント移住の定番。ただし政治情勢と為替リスクは毎年変わるので、赴任・移住前に必ず最新の1冊を。'},
                {'title': 'MM2H・ロングステイビザ', 'html': '<a href="../../books/malaysia.html">マレーシア</a>のMM2Hプログラムや、<a href="../../books/thailand.html">タイ</a>のリタイアメントビザは日本人の長期滞在の主要な選択肢。政策変更が頻繁なので、制度と国の構造を両輪で理解する。'},
                {'title': '教育移住・子育て', 'html': '<a href="../../books/singapore.html">シンガポール</a>・<a href="../../books/malaysia.html">マレーシア</a>は英語教育・国際校の選択肢が豊富で、日本人ファミリーの教育移住先として定着。教育制度と多民族社会の背景を掴んでおくと、学校選びで迷いにくい。'},
            ]},
            {'kind': 'related_series', 'links': [
                ('southeast-asia', '東南アジア9カ国シリーズを見る'),
                ('asean', 'ASEAN横串4冊シリーズを見る'),
            ]},
        ]
    },
]

def build_series_page(sdef):
    """データ駆動でシリーズページ1本を生成"""
    slug = sdef['slug']
    books_by_slug = {b['slug']: b for b in DATA}

    sections_html = []
    for sec in sdef['sections']:
        if sec['kind'] == 'books':
            cards = ''.join(render_series_card(books_by_slug[s]) for s in sec['slugs'] if s in books_by_slug)
            sections_html.append(f'''
<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>{sec['title']}</h2>
<p>{sec.get('desc', '')}</p>
</div>
<div class="books-grid grid-4">
{cards}
</div>
</div>
</section>''')
        elif sec['kind'] == 'related_books':
            cards = ''.join(render_series_card(books_by_slug[s]) for s in sec['slugs'] if s in books_by_slug)
            sections_html.append(f'''
<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>{sec['title']}</h2>
<p>{sec.get('desc', '')}</p>
</div>
<div class="books-grid grid-4">
{cards}
</div>
</div>
</section>''')
        elif sec['kind'] == 'guide':
            cards = ''.join(
                f'''<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">{c["title"]}</span></div>
<p class="cat-card-desc">{c["html"]}</p>
</div>''' for c in sec['cards']
            )
            sections_html.append(f'''
<section class="section-categories">
<div class="container">
<div class="section-heading"><h2>{sec['title']}</h2></div>
<div class="cat-grid">
{cards}
</div>
</div>
</section>''')
        elif sec['kind'] == 'related_series':
            links = ' '.join(
                f'<a href="../{s}/" class="view-all-link" style="margin-right:1rem">{label} →</a>'
                for s, label in sec['links']
            )
            sections_html.append(f'''
<section class="section-featured">
<div class="container">
<div class="view-all-wrap">{links}</div>
</div>
</section>''')

    body = f'''
<main class="series-page">
<section class="hero hero-large">
<div class="container">
<div class="series-crumb"><a href="../../books/">← すべての書籍</a></div>
<h1>{sdef['h1']}</h1>
<p class="hero-sub">{sdef['hero_sub']}</p>
<p class="hero-desc">{sdef['hero_desc']}</p>
</div>
</section>
{''.join(sections_html)}
</main>
'''
    canonical = f'{SITE_URL}/series/{slug}/'
    page = head(f'{sdef["seo_title"]} | {SITE_NAME}', sdef['meta_desc'], canonical) + body + footer()
    (ROOT / 'series' / slug).mkdir(parents=True, exist_ok=True)
    (ROOT / 'series' / slug / 'index.html').write_text(render(page, 2), encoding='utf-8')

def build_all_series():
    for sdef in SERIES:
        build_series_page(sdef)
    print(f'✓ /series/ {len(SERIES)}ページ')


# -----------------------------------------------------------
# About ページ
# -----------------------------------------------------------
def build_about():
    body = '''
<main class="page-content container">
<h1>Iris Instituteについて</h1>

<p>Iris Instituteは、国・地域・企業・産業といったテーマを体系的に読み解くための書籍を制作・出版している独立系の出版・研究プロジェクトです。</p>

<h2>活動内容</h2>
<p>ひとつのテーマを、歴史・地理・文化・政治・経済・戦略・財務など複数の視点から多角的に分析し、一冊の本として体系化することを活動の中心に据えています。ニュースや業界レポート、断片的な情報だけでは見えてこない「なぜ今そうなっているのか」「これからどこへ向かうのか」という構造的な問いに、公開情報と一次資料に基づいて答えることを目指しています。</p>

<h2>編集方針</h2>
<ul>
<li>政府統計・国際機関の公表資料・企業の有価証券報告書・査読論文などの一次資料を優先的に使用します</li>
<li>特定の立場を賞賛・批判するのではなく、構造と論理を提示することを重視します</li>
<li>専門用語や固有名詞には、初出時に必ず説明を加え、就活生や大学生でも読み進められる文章にします</li>
<li>数字を並べるだけでなく、その数字が何を意味するかを言語化します</li>
<li>成功事例だけでなく、失敗・矛盾・課題も同じ比重で扱います</li>
</ul>

<h2>刊行シリーズ</h2>
<ul>
<li><strong>世界を読み解くシリーズ</strong>：各国・地域を歴史・地理・文化・政治・経済の5視点で分析</li>
<li><strong>企業を読み解くシリーズ</strong>（順次刊行）：主要企業を歴史・事業・戦略・組織・財務・未来の6視点で分析</li>
<li><strong>投資・ビジネスシリーズ</strong>（順次刊行）：不動産・仮想通貨・生成AIなど、実務に直結するテーマを体系化</li>
<li><strong>Decoding the World Series</strong>：世界シリーズの英語版・多言語版</li>
</ul>

<h2>お問い合わせ</h2>
<p>書籍に関するご質問、講演・執筆・監修のご相談等は、Amazonの著者ページ経由でご連絡いただけます。</p>
</main>
'''
    page = head(f'Irisについて | {SITE_NAME}',
                f'{SITE_NAME}の活動内容と編集方針。世界を体系的に読み解くための書籍を制作しています。',
                SITE_URL + '/about.html') + body + footer()
    (ROOT / 'about.html').write_text(render(page, 0), encoding='utf-8')
    print('✓ about.html')

# -----------------------------------------------------------
# Privacy ページ
# -----------------------------------------------------------
def build_privacy():
    body = '''
<main class="page-content container">
<h1>プライバシーポリシー</h1>

<p>海外文化研究所Iris（以下「当サイト」）は、利用者のプライバシーを尊重し、個人情報の保護に努めます。</p>

<h2>アクセス解析について</h2>
<p>当サイトでは、サイト改善のためGoogle Analyticsなどのアクセス解析ツールを利用する場合があります。これらのツールはトラフィックデータ収集のためにCookieを使用しますが、個人を特定する情報は収集していません。</p>

<h2>Amazonアソシエイトプログラムについて</h2>
<p>当サイトはAmazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。</p>

<h2>免責事項</h2>
<p>当サイトの掲載情報は執筆時点の公開情報に基づいており、その完全性・正確性・有用性を保証するものではありません。書籍内の記述内容も同様です。当サイト及び書籍の内容に基づいて行われた行動により生じた損害について、一切の責任を負いません。</p>

<h2>お問い合わせ</h2>
<p>本ポリシーに関するお問い合わせは、Amazonの著者ページ経由でお願いします。</p>
</main>
'''
    page = head(f'プライバシーポリシー | {SITE_NAME}',
                'プライバシーポリシー・免責事項・Amazonアソシエイト表記',
                SITE_URL + '/privacy.html') + body + footer()
    (ROOT / 'privacy.html').write_text(render(page, 0), encoding='utf-8')
    print('✓ privacy.html')

# -----------------------------------------------------------
# Iris Libraries
# -----------------------------------------------------------
def amazon_search_url(title, author=''):
    q = urllib.parse.quote_plus(f'{title} {author}'.strip())
    return f'https://www.amazon.co.jp/s?k={q}&tag={AFFILIATE_TAG}'

def render_lib_iris_card(b, rank, lang='ja'):
    """Iris刊行書籍カード（カバー画像つき）"""
    cover = cover_url(b['asin'])
    if lang == 'en':
        amz = amazon_url_com(b['asin'])
        detail = f'../../../books/{b["slug"]}.html'
        badge = 'Iris title'
        btn_amazon = 'Amazon.com'
        btn_detail = 'Details'
        alt_suffix = 'cover'
    else:
        amz = amazon_url(b['asin'])
        detail = f'../../books/{b["slug"]}.html'
        badge = 'Iris刊行'
        btn_amazon = 'Amazonで見る'
        btn_detail = '本の詳細を見る'
        alt_suffix = '表紙'
    return f'''<div class="lib-book-card lib-book-iris">
<div class="lib-book-rank">{rank}</div>
<div class="lib-book-cover">
<a href="{amz}" target="_blank" rel="noopener sponsored">
<img src="{cover}" alt="{html.escape(b['title'])} {alt_suffix}" loading="lazy" width="100">
</a>
</div>
<div class="lib-book-body">
<div class="lib-book-header">
<span class="iris-badge">{badge}</span>
<h3 class="lib-book-title"><a href="{amz}" target="_blank" rel="noopener sponsored">{html.escape(b['title'])}</a></h3>
</div>
<p class="lib-book-subtitle">{html.escape(b.get('subtitle', ''))}</p>
<p class="lib-book-desc">{html.escape(b['short'])}</p>
<div class="lib-book-actions">
<a href="{amz}" class="btn-amazon" target="_blank" rel="noopener sponsored">{btn_amazon}</a>
<a href="{detail}" class="link-detail">{btn_detail}</a>
</div>
</div>
</div>'''

def render_lib_ext_card(book, rank):
    """外部書籍カード。ASIN があればカバー画像を表示、なければプレースホルダ"""
    has_asin = bool(book.get('asin'))
    if has_asin:
        amz = amazon_url(book['asin'])
        cover_html = f'''<div class="lib-book-cover">
<a href="{amz}" target="_blank" rel="noopener sponsored">
<img src="{cover_url(book['asin'])}" alt="{html.escape(book['title'])} 表紙" loading="lazy" width="100">
</a>
</div>'''
        btn_label = 'Amazonで見る'
    else:
        amz = amazon_search_url(book['title'], book.get('author', ''))
        cover_html = '''<div class="lib-book-cover lib-cover-placeholder" aria-hidden="true">
<span class="lib-cover-icon">📖</span>
</div>'''
        btn_label = 'Amazonで探す'
    author_pub = html.escape(f"{book.get('author', '')}　{book.get('publisher', '')}".strip())
    return f'''<div class="lib-book-card lib-book-ext">
<div class="lib-book-rank">{rank}</div>
{cover_html}
<div class="lib-book-body">
<div class="lib-book-header">
<h3 class="lib-book-title"><a href="{amz}" target="_blank" rel="noopener sponsored">{html.escape(book['title'])}</a></h3>
</div>
<p class="lib-book-meta">{author_pub}</p>
<p class="lib-book-desc">{html.escape(book['description'])}</p>
<div class="lib-book-actions">
<a href="{amz}" class="btn-amazon btn-amazon-sm" target="_blank" rel="noopener sponsored">{btn_label}</a>
</div>
</div>
</div>'''

def build_library_page(ldef):
    slug = ldef['slug']
    books_html_list = []
    for i, book in enumerate(ldef['books'], 1):
        if 'iris_slug' in book:
            b = BOOKS_BY_SLUG.get(book['iris_slug'])
            if b:
                books_html_list.append(render_lib_iris_card(b, i))
        else:
            books_html_list.append(render_lib_ext_card(book, i))

    total_books = len(ldef['books'])
    noindex = total_books < 10
    extra_head = '<meta name="robots" content="noindex">\n' if noindex else ''

    iris_series_html = ''
    if ldef.get('iris_series'):
        links = ' '.join(
            f'<a href="{{ROOT}}{s["url"]}" class="lib-series-link">{html.escape(s["label"])} →</a>'
            for s in ldef['iris_series']
        )
        iris_series_html = f'<div class="lib-series-cta">{links}</div>'

    affiliate_note = f'''<div class="lib-affiliate-note">
本ページはAmazon.co.jpを宣伝しリンクすることによって紹介料を獲得できる手段を提供することを目的に設定された、Amazonアソシエイト・プログラムの参加者が運営しています。
</div>'''

    body = f'''
<main class="lib-page">
<section class="hero">
<div class="container">
<div class="lib-crumb"><a href="{{ROOT}}/library/">← Iris Libraries</a></div>
<h1>{html.escape(ldef['title'])}</h1>
<p class="hero-sub">{html.escape(ldef.get('category', ''))}</p>
<p class="lib-intro">{html.escape(ldef['intro'])}</p>
{iris_series_html}
</div>
</section>

<section class="lib-books-section">
<div class="container">
<p class="lib-notice">掲載順は書籍の優劣を示すものではありません。編集部の選書基準については <a href="{{ROOT}}/library/policy/">選書ポリシー</a> をご覧ください。</p>
<div class="lib-books-list">
{''.join(books_html_list)}
</div>
{affiliate_note}
</div>
</section>
</main>
'''
    canonical = f'{SITE_URL}/library/{slug}/'
    page = head(ldef['seo_title'], ldef['meta_desc'], canonical,
                extra_head=extra_head) + body + footer()
    out_dir = ROOT / 'library' / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print(f'  ✓ library/{slug}/ ({total_books}冊{"・noindex" if noindex else ""})')

def build_library_index():
    # Map raw categories to display tabs
    TAB_MAP = {
        '国・地域':      '国・地域',
        '海外生活':      '海外生活',
        '東南アジア特集': '東南アジア特集',
        '企業・ビジネス': 'ビジネス',
        '投資・ビジネス': 'ビジネス',
        'テクノロジー':  'テーマ別',
        '文化・宗教':    'テーマ別',
        '文化':         'テーマ別',
        '歴史':         'テーマ別',
    }
    TAB_ORDER = ['国・地域', '海外生活', '東南アジア特集', 'ビジネス', 'テーマ別']

    cards_by_tab = {}
    counts_by_tab = {}
    for ldef in LIBRARY_DATA:
        cat = ldef.get('category', 'その他')
        tab = TAB_MAP.get(cat, 'テーマ別')
        total = len(ldef['books'])
        card = f'''<a href="{{ROOT}}/library/{ldef["slug"]}/" class="lib-index-card" data-tab="{tab}">
<h3 class="lib-index-title">{html.escape(ldef["title"])}</h3>
<p class="lib-index-meta">{html.escape(cat)}　{total}冊</p>
<p class="lib-index-intro">{html.escape(ldef["intro"][:60])}…</p>
</a>'''
        cards_by_tab.setdefault(tab, []).append(card)
        counts_by_tab[tab] = counts_by_tab.get(tab, 0) + 1

    all_cards = []
    for tab in TAB_ORDER:
        all_cards.extend(cards_by_tab.get(tab, []))

    tab_btns = '<button class="lib-tab active" data-filter="all">すべて <span class="lib-tab-count">{}</span></button>'.format(len(LIBRARY_DATA))
    for tab in TAB_ORDER:
        if tab in counts_by_tab:
            tab_btns += f'<button class="lib-tab" data-filter="{tab}">{html.escape(tab)} <span class="lib-tab-count">{counts_by_tab[tab]}</span></button>'

    body = f'''
<main class="lib-index-page">
<section class="hero hero-large">
<div class="container">
<h1>Iris Libraries</h1>
<p class="hero-sub">テーマ別おすすめ本10選</p>
<p class="hero-desc">Iris編集部が、国・地域・産業・テーマ別に「最初に読むべき10冊」を厳選して紹介します。Iris刊行書籍と、国内外の専門家・ジャーナリストによる書籍を組み合わせた選書です。</p>
<div class="lib-index-links">
<a href="{{ROOT}}/library/policy/" class="lib-policy-link">選書ポリシーを見る →</a>
</div>
</div>
</section>

<section class="lib-index-content">
<div class="container">
<div class="lib-tabs">
{tab_btns}
</div>
<div class="lib-index-status" id="lib-status"></div>
<div class="lib-index-grid" id="lib-grid">
{''.join(all_cards)}
</div>
<div class="lib-pagination" id="lib-pagination"></div>
</div>
</section>
</main>
<script>
(function(){{
  var PER_PAGE = 12;
  var tabs = document.querySelectorAll('.lib-tab');
  var allCards = Array.prototype.slice.call(document.querySelectorAll('.lib-index-card'));
  var status = document.getElementById('lib-status');
  var pagination = document.getElementById('lib-pagination');
  var currentFilter = 'all';
  var currentPage = 1;

  function getVisible() {{
    return allCards.filter(function(c) {{
      return currentFilter === 'all' || c.getAttribute('data-tab') === currentFilter;
    }});
  }}

  function render() {{
    var visible = getVisible();
    var total = visible.length;
    var totalPages = Math.ceil(total / PER_PAGE);
    if (currentPage > totalPages) currentPage = 1;
    var start = (currentPage - 1) * PER_PAGE;
    var end = start + PER_PAGE;

    allCards.forEach(function(c) {{ c.style.display = 'none'; }});
    visible.slice(start, end).forEach(function(c) {{ c.style.display = ''; }});

    // status
    var showing = Math.min(end, total);
    status.textContent = total + '件中 ' + (start + 1) + '〜' + showing + '件を表示';

    // pagination
    if (totalPages <= 1) {{
      pagination.innerHTML = '';
      return;
    }}
    var html = '';
    html += currentPage > 1
      ? '<button class="lib-page-btn" data-page="' + (currentPage - 1) + '">← 前へ</button>'
      : '<button class="lib-page-btn" disabled>← 前へ</button>';
    for (var p = 1; p <= totalPages; p++) {{
      html += p === currentPage
        ? '<span class="lib-page-num lib-page-current">' + p + '</span>'
        : '<button class="lib-page-num" data-page="' + p + '">' + p + '</button>';
    }}
    html += currentPage < totalPages
      ? '<button class="lib-page-btn" data-page="' + (currentPage + 1) + '">次へ →</button>'
      : '<button class="lib-page-btn" disabled>次へ →</button>';
    pagination.innerHTML = html;

    pagination.querySelectorAll('[data-page]').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        currentPage = parseInt(btn.getAttribute('data-page'));
        render();
        document.querySelector('.lib-index-content').scrollIntoView({{behavior:'smooth', block:'start'}});
      }});
    }});
  }}

  tabs.forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      tabs.forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      currentPage = 1;
      render();
    }});
  }});

  render();
}})();
</script>
'''
    canonical = f'{SITE_URL}/library/'
    page = head(f'Iris Libraries — テーマ別おすすめ本10選 | {SITE_NAME}',
                'Iris編集部が厳選した国・地域・企業テーマ別のおすすめ本10選。東南アジア・ASEAN・インドネシア・ベトナム・海外移住・総合商社など。',
                canonical) + body + footer()
    out_dir = ROOT / 'library'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 1), encoding='utf-8')
    print('  ✓ library/index.html')

def build_library_policy():
    body = '''
<main class="lib-page lib-policy-page">
<section class="hero">
<div class="container">
<div class="lib-crumb"><a href="{ROOT}/library/">← Iris Libraries</a></div>
<h1>Iris Libraries 選書ポリシー</h1>
<p class="lib-intro">Iris Libraries は、テーマ別に「最初に読むべき10冊」を提示する選書メディアです。編集部は下記の観点を大切にしながら書籍を選んでいます。</p>
</div>
</section>

<section class="lib-policy-section">
<div class="container">

<h2>選書について</h2>
<p>Iris Libraries は、各テーマに関心を持った方が「まず1冊」から段階的に深く学べるよう、性格の異なる書籍をバランスよく組み合わせて選書しています。編集部の判断と、公開されている書評や読者の反応などの参考情報を総合的に踏まえて選んでいます。</p>

<h3>内容のバランス</h3>
<p>入門書・通史・専門書・最新のビジネス書など、目的に応じて選べるよう性格の異なる書籍を組み合わせています。「まず1冊」から「さらに深く」まで、段階的に学べる構成を意識しています。</p>

<h3>テーマとの適合性</h3>
<p>各テーマの本質を掴むうえで役立つと編集部が判断した書籍を選んでいます。</p>

<h3>情報の鮮度</h3>
<p>最新の状況を反映した書籍を中心にしていますが、その分野の定番として読み継がれている書籍については刊行年を問わず選書に含めています。</p>

<h2>掲載順について</h2>
<p>各ページでは Iris刊行の書籍を先頭に配置していますが、それ以降の掲載順は書籍の優劣を示すものではありません。ご自身の関心と目的に応じてリストをご活用ください。</p>

</div>
</section>
</main>
'''
    canonical = f'{SITE_URL}/library/policy/'
    page = head(f'選書ポリシー | Iris Libraries — {SITE_NAME}',
                'Iris Libraries の選書ポリシー。編集部が書籍を選定する際の除外基準・優先基準・掲載順・更新方針・アソシエイトプログラムに関する開示。',
                canonical) + body + footer()
    out_dir = ROOT / 'library' / 'policy'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print('  ✓ library/policy/')

def build_all_library():
    print('Building Iris Libraries...')
    build_library_index()
    build_library_policy()
    for ldef in LIBRARY_DATA:
        build_library_page(ldef)

# -----------------------------------------------------------
# English library (/en/library/)
# -----------------------------------------------------------
def build_en_library_page(ldef):
    slug = ldef['slug']
    books_html = []
    for rank, entry in enumerate(ldef['books'], 1):
        if 'iris_slug' in entry:
            b = BOOKS_BY_SLUG.get(entry['iris_slug'])
            if not b:
                continue
            books_html.append(render_lib_iris_card(b, rank, lang='en'))
        else:
            # English external book — Amazon.com (primary) + Amazon.co.uk (secondary)
            asin = entry.get('asin', '')
            if asin:
                com_url = amazon_url_com(asin)
                uk_url = amazon_url_uk(asin)
                cover_html = f'''<div class="lib-book-cover">
<a href="{com_url}" target="_blank" rel="noopener sponsored">
<img src="{cover_url(asin)}" alt="{html.escape(entry['title'])} cover" loading="lazy" width="100">
</a></div>'''
                action = (f'<a href="{com_url}" class="btn-amazon" target="_blank" rel="noopener sponsored">Amazon.com</a>'
                          f'<a href="{uk_url}" class="btn-amazon-intl" target="_blank" rel="noopener sponsored">Amazon.co.uk</a>')
                title_link = com_url
            else:
                title_link = f'https://www.amazon.com/s?k={urllib.parse.quote_plus(entry["title"])}'
                cover_html = '<div class="lib-cover-placeholder"><span class="lib-cover-icon">📖</span></div>'
                action = f'<a href="{title_link}" class="btn-amazon" target="_blank" rel="noopener sponsored">Search Amazon</a>'
            meta = f'{html.escape(entry.get("pub_year",""))} · {html.escape(entry.get("publisher",""))}'
            desc = html.escape(entry.get('description', ''))
            books_html.append(f'''<div class="lib-book-card lib-book-ext">
<div class="lib-book-rank">{rank}</div>
{cover_html}
<div class="lib-book-body">
<h3 class="lib-book-title"><a href="{title_link}" target="_blank" rel="noopener sponsored">{html.escape(entry["title"])}</a></h3>
<p class="lib-book-author">{html.escape(entry.get("author",""))}</p>
<p class="lib-book-meta">{meta}</p>
<p class="lib-book-desc">{desc}</p>
<div class="lib-book-actions">{action}</div>
</div>
</div>''')

    body = f'''
<main class="lib-page">
<section class="hero">
<div class="container">
<div class="lib-crumb"><a href="{{ROOT}}/en/library/">← Iris Libraries</a></div>
<h1>{html.escape(ldef["title"])}</h1>
<p class="lib-intro">{html.escape(ldef["intro"])}</p>
</div>
</section>
<section class="lib-books-section">
<div class="container">
{''.join(books_html)}
</div>
</section>
<p class="lib-affiliate-note">As an Amazon Associate I earn from qualifying purchases.</p>
</main>
'''
    canonical = f'{SITE_URL}/en/library/{slug}/'
    extra = hreflang_block(JAPAN_LIB_HREFLANG) if slug == 'japan' else ''
    page = head(ldef['seo_title'], ldef['meta_desc'], canonical, lang='en', extra_head=extra) + body + footer(lang='en')
    out_dir = ROOT / 'en' / 'library' / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 3), encoding='utf-8')
    print(f'  ✓ en/library/{slug}/ ({len(ldef["books"])}冊)')

def build_en_library_index():
    cards = []
    for ldef in LIBRARY_EN_DATA:
        total = len(ldef['books'])
        cards.append(f'''<a href="{{ROOT}}/en/library/{ldef["slug"]}/" class="lib-index-card">
<h3 class="lib-index-title">{html.escape(ldef["title"])}</h3>
<p class="lib-index-meta">{total} books</p>
<p class="lib-index-intro">{html.escape(ldef["intro"][:80])}…</p>
</a>''')

    body = f'''
<main class="lib-index-page">
<section class="hero hero-large">
<div class="container">
<h1>Iris Libraries</h1>
<p class="hero-sub">10 essential books, by theme</p>
<p class="hero-desc">Iris editorial team curates 10 books on each country, company, and topic — combining Iris titles with the best external sources available.</p>
</div>
</section>
<section class="lib-index-content">
<div class="container">
<div class="lib-index-grid">
{''.join(cards)}
</div>
</div>
</section>
</main>
'''
    canonical = f'{SITE_URL}/en/library/'
    page = head('Iris Libraries — 10 Essential Books by Theme | Iris Institute',
                'Iris editorial curates 10 essential books on Japan, Mexico and more — history, politics, economy, culture.',
                canonical, lang='en') + body + footer(lang='en')
    out_dir = ROOT / 'en' / 'library'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print('  ✓ en/library/index.html')

def build_all_en_library():
    print('Building English Libraries...')
    build_en_library_index()
    for ldef in LIBRARY_EN_DATA:
        build_en_library_page(ldef)

# -----------------------------------------------------------
# sitemap.xml / robots.txt
# -----------------------------------------------------------
def build_sitemap():
    urls = [
        (SITE_URL + '/', '1.0'),
        (SITE_URL + '/books/', '1.0'),
    ]
    # シリーズページ自動生成
    for sdef in SERIES:
        urls.append((f'{SITE_URL}/series/{sdef["slug"]}/', '0.9'))
    # ライブラリページ
    urls.append((SITE_URL + '/library/', '0.8'))
    urls.append((SITE_URL + '/library/policy/', '0.5'))
    for ldef in LIBRARY_DATA:
        if len(ldef['books']) >= 10:
            urls.append((f'{SITE_URL}/library/{ldef["slug"]}/', '0.8'))
    urls += [
        (SITE_URL + '/about.html', '0.7'),
        (SITE_URL + '/en/', '0.9'),
        (SITE_URL + '/en/library/', '0.8'),
        *[(f'{SITE_URL}/en/library/{ldef["slug"]}/', '0.8') for ldef in LIBRARY_EN_DATA],
        (SITE_URL + '/en/about.html', '0.5'),
        (SITE_URL + '/es/', '0.8'),
        (SITE_URL + '/es/library/', '0.6'),
        *[(f'{SITE_URL}/es/library/{ldef["slug"]}/', '0.7') for ldef in LIBRARY_ES_DATA],
        (SITE_URL + '/es/about.html', '0.4'),
        (SITE_URL + '/de/', '0.8'),
        (SITE_URL + '/de/library/', '0.6'),
        *[(f'{SITE_URL}/de/library/{ldef["slug"]}/', '0.7') for ldef in LIBRARY_DE_DATA],
        (SITE_URL + '/de/about.html', '0.4'),
        (SITE_URL + '/fr/', '0.8'),
        (SITE_URL + '/fr/library/', '0.6'),
        *[(f'{SITE_URL}/fr/library/{ldef["slug"]}/', '0.7') for ldef in LIBRARY_FR_DATA],
        (SITE_URL + '/fr/about.html', '0.4'),
        (SITE_URL + '/privacy.html', '0.3'),
    ]
    for b in DATA:
        urls.append((f'{SITE_URL}/books/{b["slug"]}.html', '0.9'))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/0.9">\n'
    for url, prio in urls:
        xml += f'  <url><loc>{url}</loc><priority>{prio}</priority></url>\n'
    xml += '</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print(f'✓ sitemap.xml ({len(urls)} URLs)')

def build_robots():
    txt = f'''User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
'''
    (ROOT / 'robots.txt').write_text(txt, encoding='utf-8')
    print('✓ robots.txt')

# -----------------------------------------------------------
if __name__ == '__main__':
    build_index()
    build_all_books_pages()
    build_all_series()
    build_en_index()
    build_en_about()
    build_all_en_library()
    build_all_multilang()
    build_all_details()
    build_about()
    build_privacy()
    build_all_library()
    build_sitemap()
    build_robots()
    print('\n🎉 生成完了')
