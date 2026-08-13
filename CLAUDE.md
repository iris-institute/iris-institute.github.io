# Iris Institute サイト — 運用ルール

Iris Instituteの公式サイト（https://iris-institute.github.io/）のソース。
静的HTMLをPythonで生成し、GitHub Pagesで配信。

---

## ディレクトリ構成

```
iris-site/
├── generate.py            ← 全ページ生成スクリプト
├── data/
│   └── books.json         ← 書籍マスタデータ（追加はここ）
├── assets/
│   ├── style.css          ← 全ページ共通CSS
│   └── og-default.png     ← OGP用デフォルト画像
├── index.html             ← トップ（ランディング）
├── about.html             ← Irisについて
├── privacy.html           ← プライバシーポリシー
├── sitemap.xml            ← 自動生成
├── robots.txt             ← 自動生成
├── books/
│   ├── index.html         ← 全書籍一覧（地域別グルーピング）
│   └── {slug}.html        ← 各書籍詳細ページ
├── series/
│   └── {slug}/index.html  ← テーマ・シリーズページ
└── en/
    ├── index.html         ← 英語トップ
    └── about.html         ← 英語About
```

---

## 基本コマンド

```bash
cd ~/Desktop/iris-site
python3 generate.py           # 全ページを再生成
python3 -m http.server 8888   # ローカル確認 → http://localhost:8888/
git add -A && git commit -m "..." && git push origin main
```

pushすれば GitHub Pages が自動デプロイ（通常1〜3分）。

---

## 新刊が刊行されたら（KDPで「出版済み」になった直後）

### 1. `data/books.json` に1エントリ追加

```json
{
  "asin": "B0XXXXXXXX",
  "slug": "country-name-in-kebab",
  "title": "○○を読み解く",
  "subtitle": "サブタイトル全文",
  "category": "世界",
  "region": "アジア",
  "lang": "ja",
  "date": "2026-MM-DD",
  "tags": ["東南アジア", "新興国", "仏教文化", "アジア"],
  "short": "60〜80字の紹介文。カード表示に使う。"
}
```

**フィールド仕様：**
- `asin`：Amazon商品ページのURLから抽出（`/dp/` の後の文字列）
- `slug`：URLに使うスラッグ。英語kebab-case（例：`decoding-japan`, `real-estate-investment`）
- `title` / `subtitle`：本のタイトルそのまま（【図解】等の接頭辞は含めない）
- `category`：`世界` / `企業` / `投資・ビジネス` / `English` / `その他`
- `region`：`アジア` / `ヨーロッパ` / `北米・中南米` / `その他`
- `lang`：`ja` / `en` / `de` / `fr`
- `date`：出版日（YYYY-MM-DD、`/books/` の新刊順ソートで使う）
- `tags`：**関連本・シリーズページの分類キー。必ず適切なタグを付ける（後述）**
- `short`：カード表示用の1文説明（60〜80字目安）

### 2. Amazonカバー画像は自動取得

`https://m.media-amazon.com/images/P/{ASIN}._SL500_.jpg` を自動で参照するので、手動アップロード不要。

### 3. サイトを再生成してpush

```bash
python3 generate.py
git add -A && git commit -m "Add: {書名}"
git push origin main
```

これだけで、以下が自動更新される：
- `/books/{slug}.html` 詳細ページ生成
- `/books/` 一覧に追加
- 該当シリーズページ（`/series/*/`）に自動反映（タグベースなので）
- 関連本ロジックが再計算されて、他ページの「関連書籍」枠にも表示
- sitemap.xml に追加

---

## タグ設計（重要）

`tags` は関連本ロジックとシリーズページのフィルタリングに使うので、以下の一貫性を守る。

### 地域タグ（1つ必ず）
| タグ | 対象 |
|---|---|
| `東南アジア` | ASEAN10カ国 |
| `東アジア` | 中国・韓国・北朝鮮・台湾・香港・モンゴル |
| `南アジア` | インド・ネパール・パキスタン・バングラデシュ・スリランカ |
| `ヨーロッパ` | 欧州各国・旧ソ連圏（ジョージア含む） |
| `北米` | アメリカ・カナダ |
| `中南米` | メキシコ・中央アメリカ・南米（メキシコは両方付ける） |
| `オセアニア` | オーストラリア・NZ |
| `中東・アフリカ` | 中東・アフリカ諸国 |

### 属性タグ（複数可）
| タグ | 意味 |
|---|---|
| `先進国` / `新興国` / `超大国` | 発展段階 |
| `英語圏` | 英語が公用語または実用語 |
| `イスラム圏` / `仏教文化` / `キリスト教` | 主要宗教 |
| `社会主義` / `軍事政権` | 特殊な政治体制 |
| `資源国` / `製造業大国` / `金融ハブ` | 経済的特徴 |
| `地政学` | 現代の地政学的ホットスポット |
| `都市国家` / `多民族` / `旧宗主国` | その他特徴 |
| `ASEAN総合` | ASEAN横串シリーズ（9カ国個別ではなく） |
| `英語書籍` | 英語版であることを明示 |

### 特殊タグ
| タグ | 意味 |
|---|---|
| `企業` | 企業分析書 |
| `投資` / `不動産` / `金融` / `暗号資産` | 投資・金融テーマ |
| `テクノロジー` / `AI` / `IT` | 技術テーマ |
| `歴史` / `文化` / `宗教` | 分野テーマ |
| `戦争` | 戦争史 |
| `日本` | 日本を主題とする書籍 |

### 非「国」書籍のオーバーライド（必須）

「〇〇を読み解く」の〇〇が「国」でない書籍（企業・技術・投資・戦争・宗教など）は、
自動生成テンプレートが破綻するので、必ず以下の6フィールドを個別に指定する：

```json
{
  ...
  "seo_title": "書名 | サブフック文言",
  "seo_desc": "160字以内の自然文説明（キーワード詰め込み厳禁）",
  "learn": ["この本で分かること①", "②", "③", "④", "⑤"],
  "who": ["こんな人におすすめ①", "②", "③", "④", "⑤", "⑥"],
  "toc": ["第1章 見出し", "第2章 見出し", ...],
  "long_desc": ["段落1", "段落2", "段落3", "段落4"]
}
```

オーバーライドが**なければ**国前提のテンプレートが自動使用される。
現状オーバーライド済み：pacific-war / world-heritage / buddhism / crypto-investment /
real-estate-investment / google / generative-ai / asean-history / asean-economy /
asean-culture / asean-manufacturing の11冊。

### タグ付けの実例
- **ドイツ**: `["ヨーロッパ", "先進国", "製造業大国"]`
- **タイ**: `["東南アジア", "新興国", "仏教文化", "アジア"]`
- **Google**: `["企業", "IT", "テクノロジー", "アメリカ"]`
- **生成AI**: `["テクノロジー", "AI", "IT"]`
- **Decoding Japan**: `["東アジア", "先進国", "アジア", "英語書籍"]`

---

## シリーズ・テーマページの追加（SEOハブページ）

**方針**：書籍が3冊以上まとまったテーマは、専用の「シリーズページ」を作って、書名以外の検索ワード（例：「東アジア 本」「英語圏 移住」）を取りにいく。

### 追加手順：`generate.py` の `SERIES` リストに1エントリ追加するだけ

```python
{
    'slug': 'my-new-series',                    # URL: /series/my-new-series/
    'seo_title': 'タイトル | 副題',              # <title> タグ用（末尾に自動で | サイト名 が付く）
    'meta_desc': '150〜200字の説明文',
    'h1': 'ページ内のH1見出し',
    'hero_sub': '1行のサブタイトル',
    'hero_desc': '300〜600字のリード文（SEO重要）',
    'sections': [
        # 書籍リスト（複数可）
        {'kind': 'books',
         'title': 'セクション見出し',
         'desc': 'セクション説明',
         'slugs': ['thailand', 'vietnam', ...]},

        # 目的別ガイドカード（4枚）
        {'kind': 'guide', 'title': '目的別の読み方', 'cards': [
            {'title': '見出し', 'html': 'HTML可の説明文（<a href>で他書籍にリンク推奨）'},
            ...
        ]},

        # 関連書籍（別セクションで一部の書籍を紹介したい場合）
        {'kind': 'related_books', 'title': '...', 'desc': '...', 'slugs': [...]},

        # 関連シリーズへのリンク
        {'kind': 'related_series', 'links': [
            ('southeast-asia', '東南アジア9カ国シリーズを見る'),
            ('asean', 'ASEAN横串4冊シリーズを見る'),
        ]},
    ]
}
```

### 使えるセクション種別（`kind`）
| kind | 用途 |
|---|---|
| `books` | 書籍カード4列で表示。SLUGSに書籍slugを配列で指定。 |
| `related_books` | booksと見た目は同じ。別の見出し・説明を付けたい時に使う。 |
| `guide` | 4枚の「目的別カード」を表示（HTML可）。書籍への内部リンクを積極的に。 |
| `related_series` | 他のシリーズページへのボタンリンク。 |

### シリーズページ設計のコツ（SEO）

1. **`seo_title` は40〜60字**、狙うキーワードを2〜3個含める
   - 良い例：「東アジアを国別に読み解く 5冊——中国・台湾・韓国・北朝鮮・香港」
2. **`meta_desc` は120〜160字**、自然文で書く（キーワード詰め込みは厳禁）
3. **`hero_desc` は300〜600字**、Googleに「何のページか」を伝える本文
4. **`guide` セクションの `html`** は他書籍への内部リンクを積極的に貼る
5. **`related_series`** で少なくとも2つの他シリーズへ回遊させる

### 既存シリーズ一覧（19本）

**地域軸**
| slug | 内容 | 冊数 |
|---|---|---|
| `southeast-asia` | 東南アジア9カ国 | 9 |
| `asean` | ASEAN横串4冊 | 4 |
| `east-asia` | 東アジア5カ国 | 5 |
| `latin-america` | 中南米 | 3 |
| `english-speaking` | 英語圏4カ国 | 4 |
| `peninsula-nations` | 半島の国々 | 3 |

**テーマ軸**
| slug | 内容 | 冊数 |
|---|---|---|
| `international-affairs` | 地政学・国際情勢 | 6 |
| `buddhism` | 仏教＋仏教国 | 6 |
| `semiconductor-geopolitics` | 半導体地政学 | 3 |
| `brics-plus` | BRICS+ | 3 |
| `immigration-nations` | 移民国家 | 4 |
| `failed-states` | 崩れた国家 | 3 |
| `pro-japan` | 親日国 | 8 |
| `financial-hubs` | 世界の金融ハブ都市 | 3 |

**目的軸（読者ペルソナ）**
| slug | 内容 | 冊数 |
|---|---|---|
| `overseas-life` | 海外移住・ワーホリ | 12 |
| `expat-postings` | 海外駐在・赴任 | 10 |
| `overseas-entrepreneurship` | 海外起業・スタートアップ | 11 |
| `manufacturing` | 世界の製造業 | 11 |
| `investment-business` | 投資・ビジネス書 | 4 |

### 次に作る候補（3冊以上そろえば作れる）
- **総合商社5社比較**：三菱・三井・住友・伊藤忠・丸紅（執筆中の5冊揃ったら）
- **旧植民地・独立国家**：インド・フィリピン・ベトナム・インドネシア
- **金融ハブ都市**：香港・シンガポール・イギリス
- **仏教×独裁×分断**：ミャンマー・北朝鮮・ラオス（切り口テスト）
- **BRICS+拡張**：ブラジル・南アフリカ刊行後に「BRICS+ 5冊」に拡張
- **AI3強**：Google・生成AI＋（Amazon・OpenAI・Microsoftを追加した時）
- **投資分野まとめ**：仮想通貨・不動産・生成AI＋（半導体投資本など）

---

## 詳細ページの中身（自動生成）

`/books/{slug}.html` に含まれる要素：
- タイトル・サブタイトル・表紙・Amazonボタン（Kindle・ペーパーバック共通）
- 「この本で分かること」（自動生成、5項目）
- 「本の紹介」（自動生成、300〜500字。SEO用の自然文）
- 「主な目次」（自動生成、5章分の概要）
- 「こんな人におすすめ」（自動生成、6項目）
- 「関連書籍」（タグ重複スコアで自動計算、4冊表示）
- 構造化データ（Book schema.org、JSON-LD）
- OG画像は書籍カバーを自動指定

**メタ説明は詳細ページのみ意図的に空**にしてある（Googleが本文冒頭を自動抽出するため）。書籍固有のキーワード詰め込みを避け、自然な検索スニペットにする方針。

---

## トップページの「注目書籍」変更方法

`generate.py` の `build_index()` 内で指定：

```python
FEATURED_SLUGS = ['pacific-war', 'asean-history', 'asean-culture', 'asean-economy']
```

4冊固定（デスクトップ横並び4列）。時期に応じて手動で入れ替え。

---

## サイト全体の設計思想

### 動線設計
```
検索・SNS → 詳細ページ → Amazon（購入）
                     ↓
                 関連書籍4冊で回遊
                     ↓
                 シリーズページで面的に理解
                     ↓
                 別の詳細ページへ

トップ → カテゴリー入口 → /books/ 一覧 → 詳細ページ
```

### SEO戦略（3段構え）
1. **詳細ページ**（40+）：「○○を読み解く」等の書名検索を取る
2. **シリーズページ**（8）：「東アジア 本」等のテーマ検索を取る
3. **カテゴリー・一覧ページ**：ドメイン評価と回遊を作る

### コンテンツ更新頻度目標
- 新刊：週1〜2冊（→ 詳細ページ・カテゴリー自動反映）
- シリーズページ：月1本追加（3冊以上そろったテーマから）
- トップページ「注目書籍」：月1回入れ替え

---

## Amazonアソシエイト・アフィリエイト

- **トラッキングID**：`leonjornal-22`
- **設定場所**：`generate.py` 冒頭の `AFFILIATE_TAG` 定数
- **反映方式**：
  - 全書籍のAmazonリンク（`/dp/{ASIN}`）に自動で `?tag=leonjornal-22` が付く
  - Kindle Unlimited登録リンクも同タグ付きで生成（`KU_SIGNUP_URL`）
- **配置場所**：
  - 各書籍詳細ページの「Kindleで読む」直下にKU登録CTA
  - `/books/` ページ末尾に大きめのKU登録セクション
- **開示**：privacy.htmlに「Amazonアソシエイト・プログラム参加」を明記済み
- **タグ変更する場合**：`generate.py` の `AFFILIATE_TAG = 'leonjornal-22'` を書き換えて `python3 generate.py` すれば全リンクに一括反映

---

## トラブルシューティング

### 生成エラー
- `data/books.json` のJSON構文エラー：`python3 -c "import json; json.load(open('data/books.json'))"` で確認
- カバー画像404：ASINが間違っている、または書籍が非公開の可能性

### GitHub Pagesに反映されない
- pushしたか確認：`git log --oneline -1`
- ビルド状況確認：`gh api repos/iris-institute/iris-institute.github.io/pages/builds/latest --jq '.status'`
- ブラウザキャッシュ：Cmd+Shift+R で強制リロード

### 関連本が意図と違う
- 対象書籍と関連させたい書籍の `tags` を確認し、重複タグを増やす
- スコアリング：タグ重複×10 + 同言語ボーナス1

---

## 参考リンク

- 本番サイト：https://iris-institute.github.io/
- リポジトリ：https://github.com/iris-institute/iris-institute.github.io
- サイトマップ：https://iris-institute.github.io/sitemap.xml
- Search Console：https://search.google.com/search-console/
