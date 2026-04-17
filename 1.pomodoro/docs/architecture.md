# アーキテクチャ概要

## 現在の実装状態

**実装フェーズ**: Step 1（プロジェクト骨格）完了

---

## 技術スタック

| 区分 | 技術 |
|---|---|
| バックエンド | Python / Flask 3.1.0 |
| フロントエンド | HTML / CSS（JS未実装） |
| テスト | pytest 8.3.5 / pytest-flask 1.3.0 |

---

## ディレクトリ構成

```
1.pomodoro/
├── app.py                  # Flaskアプリケーション本体
├── requirements.txt        # 依存パッケージ
├── templates/
│   └── index.html          # トップページHTMLテンプレート
├── static/
│   ├── css/
│   │   └── style.css       # スタイルシート（未実装）
│   └── js/                 # JavaScriptモジュール（未実装）
├── tests/
│   ├── __init__.py
│   └── test_app.py         # アプリケーションテスト
├── docs/                   # ドキュメント
├── features.md             # 機能仕様
└── plan.md                 # 実装計画
```

---

## アプリケーション構成

### バックエンド（`app.py`）

- Flask の `Flask(__name__)` でアプリケーションインスタンスを生成
- `GET /` ルートで `index.html` テンプレートをレンダリング
- `debug=False` で起動

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")
```

### フロントエンド（`templates/index.html`）

- Jinja2テンプレートエンジンを使用
- `url_for()` でCSSファイルを静的ファイルとして参照
- 現時点ではページ本体（`<body>`）は空

---

## 計画中のアーキテクチャ（未実装）

`plan.md` に基づく今後の実装予定レイヤー構成：

```
フロントエンド（JS）
├── timer-core.js     純粋状態機械（DOM依存なし）
├── timer.js          setIntervalラッパー
└── app.js            DOMバインディング・通知・音声

バックエンド（Python）
├── routes (app.py)   APIエンドポイント
├── services/         バリデーション・ビジネスロジック
└── repositories/     データアクセス（JSON/SQLite）
```

タイマー状態は `IDLE / RUNNING / PAUSED / FINISHED` の4状態で管理される予定です。
