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
    urls += [
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
    build_all_series()
    build_en_index()
    build_en_about()
    build_all_details()
    build_about()
    build_privacy()
    build_sitemap()
    build_robots()
    print('\n🎉 生成完了')
