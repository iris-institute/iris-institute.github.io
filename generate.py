#!/usr/bin/env python3
"""Iris サイト生成スクリプト"""
import json, os, re, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'data' / 'books.json').read_text(encoding='utf-8'))

SITE_NAME = 'Iris Institute'
SITE_URL = 'https://iris-institute.github.io'
SITE_TAGLINE = '世界を、体系的に読み解く。'
SITE_SUB = '国・企業・産業を、公開情報と一次資料から多角的に分析する。'

# -----------------------------------------------------------
# 共通テンプレート
# -----------------------------------------------------------
def cover_url(asin):
    return f'https://m.media-amazon.com/images/P/{asin}._SL500_.jpg'

def amazon_url(asin):
    return f'https://www.amazon.co.jp/dp/{asin}'

def head(title, description, canonical, og_image=None, extra_head='', lang='ja', omit_meta_description=False):
    og_image = og_image or f'{SITE_URL}/assets/og-default.png'
    if lang == 'en':
        nav = f'''<a href="{{ROOT}}/en/">Books</a>
<a href="{{ROOT}}/en/about.html">About</a>
<a href="{{ROOT}}/" style="opacity:0.6">日本語</a>'''
        home_link = '{ROOT}/en/'
    else:
        nav = f'''<a href="{{ROOT}}/">書籍一覧</a>
<a href="{{ROOT}}/about.html">Irisについて</a>
<a href="{{ROOT}}/en/" style="opacity:0.6">English</a>'''
        home_link = '{ROOT}/'
    meta_desc = '' if omit_meta_description else f'<meta name="description" content="{html.escape(description)}">\n'
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
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

def footer():
    year = datetime.now().year
    return f'''
<footer class="site-footer">
<div class="container">
<div>
<div class="footer-brand">{SITE_NAME}</div>
<div class="footer-copyright">© {year} {SITE_NAME}. All rights reserved.</div>
</div>
<div class="footer-links">
<a href="{{ROOT}}/">書籍一覧</a>
<a href="{{ROOT}}/about.html">Irisについて</a>
<a href="{{ROOT}}/privacy.html">プライバシーポリシー</a>
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
<span class="hero-stat"><strong>3</strong> 言語対応</span>
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
    page = head(title, desc, SITE_URL + '/') + body + footer()
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

    # SEO最適化タイトル・description
    if book['lang'] == 'en':
        topic = title.replace('Decoding ', '')
        seo_title = f'{title} | Understanding {topic} through 5 Lenses | {SITE_NAME}'
        seo_desc = f'{title}: {book["short"]} A comprehensive analysis of {topic} through history, geography, culture, politics and economics. Kindle edition available.'
    else:
        m = re.match(r'^(.+?)を読み解く', title)
        topic = m.group(1) if m else title
        seo_title = f'{title} | {topic}の歴史・経済・文化を体系的に学ぶ | {SITE_NAME}'
        seo_desc = f'{title}——{book["short"]} {topic}の歴史・地理・文化・政治・経済を5つの視点で分析。{topic} 経済 / {topic} 歴史 / {topic} 本 を探している方向けの入門書。Kindle Unlimited対応。'

    canonical = f'{SITE_URL}/books/{slug}.html'
    cover = cover_url(book['asin'])
    amazon = amazon_url(book['asin'])

    # 関連書籍：タグ重複数でスコアリング（同言語を優先、同一冊は除外）
    def score(other):
        if other['slug'] == slug:
            return -1
        overlap = len(set(book.get('tags', [])) & set(other.get('tags', [])))
        # 同言語ボーナス
        lang_bonus = 1 if other['lang'] == book['lang'] else 0
        return overlap * 10 + lang_bonus
    ranked = sorted(DATA, key=lambda x: (score(x), x['date']), reverse=True)
    related = [r for r in ranked if r['slug'] != slug][:4]
    related_cards = []
    for r in related:
        related_cards.append(f'''<article class="book-card">
<a href="{r['slug']}.html" class="book-title-link">
<div class="book-cover"><img src="{cover_url(r['asin'])}" alt="{html.escape(r['title'])}" loading="lazy"></div>
<h2 class="book-title">{html.escape(r['title'])}</h2>
</a>
<p class="book-short">{html.escape(r['short'])}</p>
<div class="book-actions">
<a href="{amazon_url(r['asin'])}" class="btn-amazon" target="_blank" rel="noopener">Amazonで見る</a>
<a href="{r['slug']}.html" class="link-detail">本の詳細を見る</a>
</div>
</article>''')

    body = f'''
<main class="book-detail">
<div class="container">
<div class="book-detail-inner">
<aside class="book-detail-cover">
<img src="{cover}" alt="{html.escape(title)} 表紙">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">Kindleで購入</a>
</aside>
<article>
<div class="book-detail-meta">{book['category']} ／ {book['region']}</div>
<h1>{html.escape(title)}</h1>
<p class="book-subtitle">{html.escape(subtitle)}</p>

<h2>この本で分かること</h2>
{build_learn(book)}

<h2>本の紹介</h2>
{build_long_desc(book)}

<h2>主な目次</h2>
{build_toc(book)}

<h2>こんな人におすすめ</h2>
{build_who(book)}

<h2>Kindleで読む</h2>
<p><a href="{amazon}" class="btn-amazon-large" target="_blank" rel="noopener">Amazonで見る</a></p>
</article>
</div>

<section class="related-books">
<h2>関連書籍</h2>
<div class="related-grid">
{''.join(related_cards)}
</div>
</section>
</div>
</main>
<div class="sticky-buy">
<a href="{amazon}" class="btn-amazon" target="_blank" rel="noopener">Amazonで見る</a>
</div>
'''

    # 詳細ページはメタ説明を出さず、本文冒頭からGoogleに自動抽出させる
    # OG（SNS共有）用にはbook['short']を渡す
    page = head(seo_title, book['short'], canonical, cover,
                extra_head=json_ld(book), omit_meta_description=True) + body + footer()
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
    page = head(title, desc, SITE_URL + '/en/', lang='en') + body + footer()
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
    page = head(f'About | {SITE_NAME}', f'About {SITE_NAME}: our activities, editorial principles and book series.', SITE_URL + '/en/about.html', lang='en') + body + footer()
    (ROOT / 'en' / 'about.html').write_text(render(page, 1), encoding='utf-8')
    print('✓ en/about.html')

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

def build_series_southeast_asia():
    """東南アジア9カ国シリーズのテーマページ"""
    # 大陸部（インドシナ半島） → 半島部・島嶼部 の順
    order = ['thailand', 'vietnam', 'laos', 'cambodia', 'myanmar',
             'malaysia', 'singapore', 'indonesia', 'philippines']
    books_by_slug = {b['slug']: b for b in DATA}
    ordered = [books_by_slug[s] for s in order if s in books_by_slug]
    cards = ''.join(render_series_card(b) for b in ordered)

    # ASEAN横串シリーズ（関連リンク用）
    asean = [b for b in DATA if 'ASEAN総合' in b.get('tags', [])]

    body = f'''
<main class="series-page">
<section class="hero hero-large">
<div class="container">
<div class="series-crumb"><a href="../../books/">← すべての書籍</a></div>
<h1>東南アジア9カ国を国別に読み解く</h1>
<p class="hero-sub">タイ・ベトナム・インドネシアを一括りにしない。9つの国を、9冊で。</p>
<p class="hero-desc">東南アジアは「ASEAN」というひとつの経済圏として語られがちですが、その内側には歴史も宗教も政治体制もまったく異なる9つの国が並んでいます。仏教国のタイ・ラオス・カンボジア・ミャンマー、イスラム圏のインドネシア・マレーシア、キリスト教中心のフィリピン、社会主義のベトナム、そして都市国家シンガポール。一冊で「東南アジア」を片付けようとすると、この違いが見えなくなります。Iris Instituteは、9つの国を1冊ずつ、歴史・地理・文化・政治・経済の5つの視点で書き下ろしました。</p>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>大陸部（インドシナ半島）</h2>
<p>メコン川流域を中心とする5カ国。仏教文化圏でありながら、政治体制と経済発展のフェーズは大きく異なる。</p>
</div>
<div class="books-grid grid-4">
{"".join(render_series_card(books_by_slug[s]) for s in ['thailand', 'vietnam', 'laos', 'cambodia', 'myanmar'] if s in books_by_slug)}
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>海洋部・島嶼部</h2>
<p>マレー半島とその南の島々。多民族・多宗教が交わり、貿易と製造業のハブとして機能する4カ国。</p>
</div>
<div class="books-grid grid-4">
{"".join(render_series_card(books_by_slug[s]) for s in ['malaysia', 'singapore', 'indonesia', 'philippines'] if s in books_by_slug)}
</div>
</div>
</section>

<section class="section-categories">
<div class="container">
<div class="section-heading">
<h2>目的別の読み方</h2>
</div>
<div class="cat-grid">
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">進出・出張前に</span></div>
<p class="cat-card-desc">赴任・出張の前に対象国の1冊を読めば、現地の商習慣や政治的な機微を掴んだ状態で入国できます。特に<a href="../../books/thailand.html">タイ</a>・<a href="../../books/vietnam.html">ベトナム</a>・<a href="../../books/indonesia.html">インドネシア</a>は日系企業の進出先として重要。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">投資判断に</span></div>
<p class="cat-card-desc">株式・不動産・直接投資のいずれでも、対象国の政治リスク・為替・産業構造を理解することが第一歩。<a href="../../books/indonesia.html">インドネシア</a>（人口2.7億）と<a href="../../books/vietnam.html">ベトナム</a>（若年層豊富）は成長市場として注目。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">大学のレポートに</span></div>
<p class="cat-card-desc">政治体制の比較・宗教と経済発展の関係・植民地時代の遺産など、東南アジア研究の出発点として。参考文献・出典を明示しているのでレポート作成にも使えます。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">旅行前の教養として</span></div>
<p class="cat-card-desc">観光ガイドが扱わない「その国の内側」を知って旅すると、見えるものが変わります。<a href="../../books/cambodia.html">カンボジア</a>のアンコール、<a href="../../books/myanmar.html">ミャンマー</a>の民主化前後、<a href="../../books/laos.html">ラオス</a>の静けさの理由。</p>
</div>
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>9カ国を横串で理解したい方へ</h2>
<p>個別国ではなくASEAN全体の視点でまとめて理解したい方は、下記の横串シリーズをおすすめします。</p>
</div>
<div class="books-grid grid-4">
{"".join(render_series_card(b) for b in asean)}
</div>
</div>
</section>
</main>
'''
    title = f'東南アジア9カ国を国別に読み解く | {SITE_NAME}'
    desc = 'タイ・ベトナム・ラオス・カンボジア・ミャンマー・マレーシア・シンガポール・インドネシア・フィリピンの9カ国を、それぞれ1冊で。歴史・地理・文化・政治・経済の5つの視点で東南アジア各国を体系的に読み解くシリーズ。'
    canonical = f'{SITE_URL}/series/southeast-asia/'
    page = head(title, desc, canonical) + body + footer()
    (ROOT / 'series' / 'southeast-asia').mkdir(parents=True, exist_ok=True)
    (ROOT / 'series' / 'southeast-asia' / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print('✓ /series/southeast-asia/')

def build_series_asean():
    """ASEAN横串4冊シリーズのテーマページ"""
    order = ['asean-history', 'asean-economy', 'asean-culture', 'asean-manufacturing']
    books_by_slug = {b['slug']: b for b in DATA}
    asean_books = [books_by_slug[s] for s in order if s in books_by_slug]

    # 9カ国リスト（関連リンク用）
    country_order = ['thailand', 'vietnam', 'laos', 'cambodia', 'myanmar',
                     'malaysia', 'singapore', 'indonesia', 'philippines']
    countries = [books_by_slug[s] for s in country_order if s in books_by_slug]

    body = f'''
<main class="series-page">
<section class="hero hero-large">
<div class="container">
<div class="series-crumb"><a href="../../books/">← すべての書籍</a></div>
<h1>ASEANを学べる4冊——歴史・経済・文化・製造業DX</h1>
<p class="hero-sub">ひとつのテーマで9カ国を貫く、ASEAN全体像の入り口。</p>
<p class="hero-desc">ASEANは加盟10カ国、人口6.7億人、GDP約4兆ドルという巨大な経済圏です。この規模を扱うとき、「国ごとに9冊読む」のとは別に、「ひとつのテーマで9カ国を貫いて見る」というアプローチが必要になります。歴史なら植民地支配と冷戦の影響を横並びで、経済なら産業構造とサプライチェーンを比較して、文化なら宗教・言語・食を対比しながら理解する。Iris Instituteは、そのための横串4冊を書き下ろしました。</p>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>ASEAN横串シリーズ</h2>
<p>ひとつのテーマで9カ国を貫く4冊。ビジネス・研究・進出準備のいずれにも使える構成。</p>
</div>
<div class="books-grid grid-4">
{"".join(render_series_card(b) for b in asean_books)}
</div>
</div>
</section>

<section class="section-categories">
<div class="container">
<div class="section-heading">
<h2>4冊の使い分け</h2>
</div>
<div class="cat-grid">
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">まず全体像から</span></div>
<p class="cat-card-desc"><a href="../../books/asean-history.html">ASEANの歴史</a>から入ると、9カ国が今の姿になった背景がわかります。植民地支配・独立戦争・冷戦・ASEAN設立という共通の骨格を掴んでから、他のテーマ書に進むと理解が深まります。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">ビジネス・投資には</span></div>
<p class="cat-card-desc"><a href="../../books/asean-economy.html">ASEANの経済</a>と<a href="../../books/asean-manufacturing.html">ASEANの製造業</a>のセット。産業構造・サプライチェーン・EV/半導体シフト・スマートファクトリー化まで、投資判断や進出戦略に直結する情報が集約されています。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">現地に赴任する前に</span></div>
<p class="cat-card-desc"><a href="../../books/asean-culture.html">ASEANの文化</a>で宗教・言語・食・慣習の違いを掴むと、赴任先での摩擦や誤解を減らせます。仏教国・イスラム圏・キリスト教中心国が混在する地域の商習慣を理解する助けになります。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">大学の研究に</span></div>
<p class="cat-card-desc">地域研究・国際関係・開発経済の授業やレポートで、9カ国を横並びで比較する視点は評価されやすい切り口です。4冊の参考文献・データ出典もそのまま利用できます。</p>
</div>
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>特定の国を深掘りしたい方へ</h2>
<p>横串で全体像を掴んだあとは、対象国の1冊で深く読み込むと理解が立体化します。</p>
</div>
<div class="books-grid grid-4">
{"".join(render_series_card(b) for b in countries[:4])}
</div>
<div class="view-all-wrap">
<a href="../southeast-asia/" class="view-all-link">9カ国シリーズ一覧を見る →</a>
</div>
</div>
</section>
</main>
'''
    title = f'ASEANを学べる本 4選——歴史・経済・文化・製造業を横串で | {SITE_NAME}'
    desc = 'ASEAN10カ国・人口6.7億人・GDP4兆ドルの経済圏を体系的に学べる4冊。歴史・経済・文化・製造業DXという4つの視点で9カ国を貫く、ASEAN全体像の入り口。ビジネス・投資・研究の出発点として。'
    canonical = f'{SITE_URL}/series/asean/'
    page = head(title, desc, canonical) + body + footer()
    (ROOT / 'series' / 'asean').mkdir(parents=True, exist_ok=True)
    (ROOT / 'series' / 'asean' / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print('✓ /series/asean/')

def build_series_overseas_life():
    """海外移住・ワーホリ・長期滞在の前に読む国別書籍"""
    books_by_slug = {b['slug']: b for b in DATA}

    # ワーホリ協定国（日本と協定あり、Iris刊行済み）
    wh_slugs = ['australia', 'canada', 'uk', 'germany', 'korea', 'taiwan', 'hongkong']
    # 移住・長期滞在人気国（ワーホリ非対象）
    migration_slugs = ['america', 'singapore', 'thailand', 'malaysia', 'philippines']

    wh_cards = ''.join(render_series_card(books_by_slug[s]) for s in wh_slugs if s in books_by_slug)
    mig_cards = ''.join(render_series_card(books_by_slug[s]) for s in migration_slugs if s in books_by_slug)

    body = f'''
<main class="series-page">
<section class="hero hero-large">
<div class="container">
<div class="series-crumb"><a href="../../books/">← すべての書籍</a></div>
<h1>海外移住・ワーホリ・長期滞在の前に読む国別書籍</h1>
<p class="hero-sub">ビザや保険の情報だけでは足りない。「その国が今どうなっているか」を、赴く前に。</p>
<p class="hero-desc">ワーホリで1年間住むにせよ、駐在や移住で5年10年暮らすにせよ、行き先の国が今どんな政治体制で、どんな経済状況で、どんな社会問題を抱えているかを知らずに飛び込むのは、思っている以上にストレスがかかります。労働ビザの条件・物価・治安・気候といった実務情報はガイドブックや在留邦人ブログで足りますが、「なぜオーストラリアは移民に厳しくなってきているのか」「なぜドイツでは家が借りにくいのか」「シンガポールの生活コストが上がり続けている理由は何か」といった構造的な話は、体系的な本でないと掴めません。Iris Instituteの国別書籍は、そうした「行く前に理解しておきたい構造」を、歴史・地理・文化・政治・経済の5つの視点で1冊にまとめています。</p>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>ワーホリ協定国を読む（7カ国）</h2>
<p>日本と<strong>ワーキング・ホリデー協定</strong>を結んでいる国のうち、Iris Instituteが刊行済みの7カ国。ビザ申請の前に、行き先の国のニュース背景を1冊で押さえておくと、現地での判断力がまったく違います。</p>
</div>
<div class="books-grid grid-4">
{wh_cards}
</div>
</div>
</section>

<section class="section-categories">
<div class="container">
<div class="section-heading">
<h2>ワーホリ協定国 別・行き先選びの視点</h2>
</div>
<div class="cat-grid">
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">英語圏に行きたい</span></div>
<p class="cat-card-desc"><a href="../../books/australia.html">オーストラリア</a>・<a href="../../books/canada.html">カナダ</a>・<a href="../../books/uk.html">イギリス</a>の3択。物価・気候・移民政策・仕事の見つけやすさが大きく違います。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">ヨーロッパで暮らしたい</span></div>
<p class="cat-card-desc"><a href="../../books/germany.html">ドイツ</a>は英語だけでも仕事は見つかるが、生活は独語が必須。Zeitenwende以降の政策変化と住宅難の背景を知っておくと動きやすい。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">アジアで挑戦したい</span></div>
<p class="cat-card-desc"><a href="../../books/korea.html">韓国</a>・<a href="../../books/taiwan.html">台湾</a>・<a href="../../books/hongkong.html">香港</a>。日本から近く、生活文化のギャップも比較的小さい。ただし政治・経済状況は毎年変わるので、最新の1冊で確認を。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">"ワーホリで何をするか"を先に考える</span></div>
<p class="cat-card-desc">語学習得・キャリア形成・費用回収・純粋な体験——目的別に最適な国は違います。行き先を決める前に、候補国の経済構造と仕事事情を1冊読むだけで判断精度が上がります。</p>
</div>
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>ワーホリ非対象・移住や長期滞在で人気の国（5カ国）</h2>
<p>ワーキングホリデー協定はないものの、駐在・起業・リタイアメント移住・留学で日本人に人気の国。ビザの取り方が難しい分、腰を据えて長く住む前提で読む1冊。</p>
</div>
<div class="books-grid grid-4">
{mig_cards}
</div>
</div>
</section>

<section class="section-categories">
<div class="container">
<div class="section-heading">
<h2>移住・長期滞在 目的別の読み方</h2>
</div>
<div class="cat-grid">
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">キャリア形成・グローバル就労</span></div>
<p class="cat-card-desc"><a href="../../books/america.html">アメリカ</a>と<a href="../../books/singapore.html">シンガポール</a>。給与水準は世界最高峰だが、ビザ取得のハードルと生活コストも相応。産業構造と労働市場を理解して行くべき国。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">物価が安く暮らしやすい</span></div>
<p class="cat-card-desc"><a href="../../books/thailand.html">タイ</a>・<a href="../../books/malaysia.html">マレーシア</a>・<a href="../../books/philippines.html">フィリピン</a>。リタイアメント移住の定番。ただし政治情勢と為替リスクは毎年変わるので、赴任・移住前に必ず最新の1冊を。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">MM2H・ロングステイビザ</span></div>
<p class="cat-card-desc"><a href="../../books/malaysia.html">マレーシア</a>のMM2Hプログラムや、<a href="../../books/thailand.html">タイ</a>のリタイアメントビザは日本人の長期滞在の主要な選択肢。政策変更が頻繁なので、制度と国の構造を両輪で理解する。</p>
</div>
<div class="cat-card static">
<div class="cat-card-header"><span class="cat-card-title">教育移住・子育て</span></div>
<p class="cat-card-desc"><a href="../../books/singapore.html">シンガポール</a>・<a href="../../books/malaysia.html">マレーシア</a>は英語教育・国際校の選択肢が豊富で、日本人ファミリーの教育移住先として定着。教育制度と多民族社会の背景を掴んでおくと、学校選びで迷いにくい。</p>
</div>
</div>
</div>
</section>

<section class="section-featured">
<div class="container">
<div class="section-heading">
<h2>他の地域も読む</h2>
<p>移住・ワーホリ以外の視点でも読める国別書籍を用意しています。</p>
</div>
<div class="view-all-wrap">
<a href="../southeast-asia/" class="view-all-link">東南アジア9カ国シリーズを見る →</a>
<a href="../asean/" class="view-all-link" style="margin-left:1rem">ASEAN横串4冊シリーズを見る →</a>
</div>
</div>
</section>
</main>
'''
    title = f'海外移住・ワーホリ・長期滞在の前に読む国別書籍 12選 | {SITE_NAME}'
    desc = 'ワーホリ協定国7カ国（オーストラリア・カナダ・イギリス・ドイツ・韓国・台湾・香港）と、移住人気国5カ国（アメリカ・シンガポール・タイ・マレーシア・フィリピン）を、それぞれ1冊で。政治・経済・社会の構造を理解して渡航するための書籍リスト。'
    canonical = f'{SITE_URL}/series/overseas-life/'
    page = head(title, desc, canonical) + body + footer()
    (ROOT / 'series' / 'overseas-life').mkdir(parents=True, exist_ok=True)
    (ROOT / 'series' / 'overseas-life' / 'index.html').write_text(render(page, 2), encoding='utf-8')
    print('✓ /series/overseas-life/')

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
# sitemap.xml / robots.txt
# -----------------------------------------------------------
def build_sitemap():
    urls = [
        (SITE_URL + '/', '1.0'),
        (SITE_URL + '/books/', '1.0'),
        (SITE_URL + '/series/southeast-asia/', '0.9'),
        (SITE_URL + '/series/asean/', '0.9'),
        (SITE_URL + '/series/overseas-life/', '0.9'),
        (SITE_URL + '/about.html', '0.7'),
        (SITE_URL + '/en/', '0.9'),
        (SITE_URL + '/en/about.html', '0.5'),
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
    build_series_southeast_asia()
    build_series_asean()
    build_series_overseas_life()
    build_en_index()
    build_en_about()
    build_all_details()
    build_about()
    build_privacy()
    build_sitemap()
    build_robots()
    print('\n🎉 生成完了')
