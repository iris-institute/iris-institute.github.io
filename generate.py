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
    # 新刊順、トップは12冊
    books_sorted = sorted(DATA, key=lambda b: b['date'], reverse=True)
    top_books = books_sorted[:12]
    cards = [render_card(b, 'books/') for b in top_books]

    body = f'''
<main>
<section class="hero">
<div class="container">
<h1>{SITE_TAGLINE}</h1>
<p>{SITE_SUB}</p>
</div>
</section>

<section class="books-section">
<div class="container">
<div class="book-count">新刊 {len(top_books)} 冊</div>
<div class="books-grid">
{''.join(cards)}
</div>
<div class="view-all-wrap">
<a href="books/" class="view-all-link">すべての書籍を見る →</a>
</div>
</div>
</section>
</main>
'''

    title = f'{SITE_NAME} — 世界を体系的に読み解く'
    desc = f'{SITE_TAGLINE} {SITE_SUB} 国・地域・企業を多角的に分析した書籍を出版しています。'
    page = head(title, desc, SITE_URL + '/') + body + footer()
    (ROOT / 'index.html').write_text(render(page, 0), encoding='utf-8')
    print(f'✓ index.html (新刊{len(top_books)}冊)')

def build_all_books_pages():
    """/books/index.html, /books/page-2.html etc. ページネーション付き一覧"""
    PER_PAGE = 24
    books_sorted = sorted(DATA, key=lambda b: b['date'], reverse=True)
    total = len(books_sorted)
    num_pages = (total + PER_PAGE - 1) // PER_PAGE

    # フィルターボタン
    filter_buttons = ['<button class="filter-btn active" data-filter="all">すべて</button>']
    for c in ['世界', '企業', '投資・ビジネス', 'その他']:
        if any(b['category'] == c for b in DATA):
            filter_buttons.append(f'<button class="filter-btn" data-filter="cat-{c}">{c}</button>')
    if any(b['lang'] == 'en' for b in DATA):
        filter_buttons.append('<button class="filter-btn" data-filter="lang-en">English</button>')
    if any(b['lang'] == 'de' for b in DATA):
        filter_buttons.append('<button class="filter-btn" data-filter="lang-de">Deutsch</button>')
    if any(b['lang'] == 'fr' for b in DATA):
        filter_buttons.append('<button class="filter-btn" data-filter="lang-fr">Français</button>')

    for p in range(1, num_pages + 1):
        start, end = (p - 1) * PER_PAGE, p * PER_PAGE
        page_books = books_sorted[start:end]
        cards = [render_card(b, '') for b in page_books]

        # ページネーション
        pag = []
        if p > 1:
            prev = 'index.html' if p == 2 else f'page-{p-1}.html'
            pag.append(f'<a href="{prev}" class="pag-link">← 前へ</a>')
        else:
            pag.append('<span class="pag-link disabled">← 前へ</span>')

        for pp in range(1, num_pages + 1):
            url = 'index.html' if pp == 1 else f'page-{pp}.html'
            if pp == p:
                pag.append(f'<span class="pag-page current">{pp}</span>')
            else:
                pag.append(f'<a href="{url}" class="pag-page">{pp}</a>')

        if p < num_pages:
            pag.append(f'<a href="page-{p+1}.html" class="pag-link">次へ →</a>')
        else:
            pag.append('<span class="pag-link disabled">次へ →</span>')

        pagination_html = f'<nav class="pagination">{" ".join(pag)}</nav>' if num_pages > 1 else ''

        body = f'''
<main>
<section class="hero">
<div class="container">
<h1>すべての書籍</h1>
<p>Iris Instituteが刊行する全書籍の一覧です。</p>
</div>
</section>

<section class="filters">
<div class="container">
<div class="filter-group">
<span class="filter-label">絞り込み：</span>
{''.join(filter_buttons)}
</div>
</div>
</section>

<section class="books-section">
<div class="container">
<div class="book-count" id="book-count">{start+1}〜{min(end, total)} 冊目 ／ 全 {total} 冊</div>
<div class="books-grid" id="books-grid">
{''.join(cards)}
</div>
{pagination_html}
</div>
</section>
</main>
<script>
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    const cards = document.querySelectorAll('.book-card');
    let count = 0;
    cards.forEach(c => {{
      const show = (f === 'all') || c.classList.contains(f);
      c.style.display = show ? '' : 'none';
      if (show) count++;
    }});
    document.getElementById('book-count').textContent = 'このページ内: ' + count + ' 冊表示';
  }});
}});
</script>
'''
        page_title = f'すべての書籍 (Page {p}/{num_pages}) | {SITE_NAME}' if num_pages > 1 else f'すべての書籍 | {SITE_NAME}'
        page_desc = f'{SITE_NAME}が刊行する全{total}冊の書籍一覧。国・地域・企業・産業を多角的に分析。'
        canonical = f'{SITE_URL}/books/' if p == 1 else f'{SITE_URL}/books/page-{p}.html'
        page = head(page_title, page_desc, canonical) + body + footer()
        fname = 'index.html' if p == 1 else f'page-{p}.html'
        (ROOT / 'books' / fname).write_text(render(page, 1), encoding='utf-8')
    print(f'✓ /books/ 一覧ページ {num_pages}ページ')

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
        (SITE_URL + '/about.html', '0.7'),
        (SITE_URL + '/en/', '0.9'),
        (SITE_URL + '/en/about.html', '0.5'),
        (SITE_URL + '/privacy.html', '0.3'),
    ]
    # /books/ ページネーション
    num_pages = (len(DATA) + 23) // 24
    for p in range(2, num_pages + 1):
        urls.append((f'{SITE_URL}/books/page-{p}.html', '0.9'))
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
    build_en_index()
    build_en_about()
    build_all_details()
    build_about()
    build_privacy()
    build_sitemap()
    build_robots()
    print('\n🎉 生成完了')
