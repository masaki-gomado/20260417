# ポモドーロタイマー Webアプリ アーキテクチャ案

## 基本方針

- タイマーロジックはすべて**クライアントサイド（JavaScript）で完結**させる
- Flaskは**ページ配信**と**設定・履歴のAPI提供**に徹する
- ユニットテストのしやすさを考慮し、**副作用・DOM・HTTP依存を各レイヤーに閉じ込める**

---

## ディレクトリ構成

```
1.pomodoro/
├── app.py                          # Flask エントリーポイント（ルート定義のみ）
├── requirements.txt
├── services/
│   └── session_service.py          # セッション集計・バリデーション（Flask非依存）
├── repositories/
│   └── session_repo.py             # データアクセス（インターフェース分離）
├── tests/                          # Python ユニットテスト
│   ├── conftest.py                 # pytest フィクスチャ（app, client）
│   ├── test_session_service.py     # サービス層テスト（Flask不要）
│   └── test_routes.py              # ルートテスト（pytest-flask）
├── static/
│   ├── css/
│   │   └── style.css               # タイマーUI・アニメーション
│   └── js/
│       ├── timer-core.js           # 純粋関数・状態機械（DOM依存ゼロ）
│       ├── timer.js                # setInterval ラッパー（依存注入対応）
│       ├── app.js                  # DOM操作・UIバインディング専用
│       └── __tests__/             # JS ユニットテスト（Jest / Vitest）
│           ├── timer-core.test.js
│           └── timer.test.js
└── templates/
    └── index.html                  # メインページ
```

---

## レイヤー設計

### Flask（バックエンド）

ルートハンドラは薄く保ち、ビジネスロジックはサービス層に委譲する。

| エンドポイント       | 役割                         |
|------------------|------------------------------|
| `GET /`          | `index.html` 配信            |
| `GET/POST /api/settings` | タイマー時間設定の保存・取得  |
| `POST /api/sessions`     | 完了セッションの記録（任意）  |

### サービス層（Python）

Flask に非依存な純粋 Python クラス。リポジトリを依存注入することでテスト時にモックへ差し替え可能。

```python
# services/session_service.py
class SessionService:
    def __init__(self, repo):
        self._repo = repo  # テスト時はインメモリリポジトリを注入

    def record_session(self, session_type: str, duration: int):
        if session_type not in ("work", "short_break", "long_break"):
            raise ValueError(f"Invalid session type: {session_type}")
        return self._repo.save({"type": session_type, "duration": duration})
```

### JavaScript（フロントエンド）

副作用・DOM・タイマーAPIを3ファイルに分離する。

#### `timer-core.js` — 純粋状態機械

DOM・`setInterval`・`Date` に一切依存せず、引数を受け取って新しい状態を返す純粋クラス。
Jest/Vitest で `jsdom` なしにテスト可能。

```
状態遷移: IDLE → RUNNING → PAUSED → FINISHED
セッション種別: WORK(25分) → SHORT_BREAK(5分) → LONG_BREAK(15分)
```

```javascript
export class TimerCore {
  constructor({ workDuration = 1500, shortBreak = 300, longBreak = 900 } = {}) { ... }
  tick()      { /* 残り秒数を1減らして新しい state を返す */ }
  start()     { ... }
  pause()     { ... }
  reset()     { ... }
  getState()  { return { ...this.state }; }  // イミュータブルに返す
}
```

#### `timer.js` — setInterval ラッパー

`setInterval` / `clearInterval` をコンストラクタで注入可能にし、テスト時にフェイクタイマーへ差し替えられるようにする。

```javascript
export class Timer {
  constructor(core, {
    setInterval   = window.setInterval,
    clearInterval = window.clearInterval,
  } = {}) {
    this._core          = core;
    this._setInterval   = setInterval;   // テスト時にフェイクタイマーを注入
    this._clearInterval = clearInterval;
  }
}
```

#### `app.js` — UI バインディング

DOM操作・ボタンイベント・通知（`Notification API`）・音声再生のみを担当。
ビジネスロジックは持たない。

---

## データフロー

```
ユーザー操作 (click)
    │
    ▼
app.js（イベントハンドラ）
    │ メソッド呼び出し
    ▼
timer.js（setInterval ラッパー）
    │ 毎秒呼び出し
    ▼
timer-core.js（状態更新・純粋関数）
    │ 新しい state を返す
    ▼
app.js（DOM更新・通知）
    │ セッション完了時のみ
    ▼
Flask API POST /api/sessions（セッション記録・任意）
```

---

## UIコンポーネント構成

```
┌──────────────────────────────────┐
│  [作業] [短い休憩] [長い休憩]      ← モード切替タブ
│                                  │
│          25:00                   ← タイマー表示（大）
│                                  │
│      [開始] [リセット]             ← コントロール
│                                  │
│  セッション: ● ● ● ○              ← ポモドーロ回数インジケーター
└──────────────────────────────────┘
```

---

## テスタビリティの設計方針

| 観点               | 設計上の対策                                          |
|------------------|-----------------------------------------------------|
| JSタイマーロジック | `TimerCore` を純粋クラスに分離（DOM・副作用ゼロ）      |
| JSタイマーAPI    | `setInterval` を依存注入でモック差替え可能に            |
| JS DOM操作       | `app.js` を UIバインディング専用に限定                 |
| Flaskルート      | ロジックをサービス層に委譲、ルートは薄く保つ             |
| データアクセス    | Repository パターンでテスト時にインメモリ実装に差替え可能 |

---

## 実装フェーズ

| フェーズ | 内容                                               |
|-------|----------------------------------------------------|
| Phase 1 | タイマー動作・モード切替・カウントダウン（コア機能）  |
| Phase 2 | アニメーション・通知API・アラーム音（UX改善）       |
| Phase 3 | Flask APIによる設定保存・セッション履歴（永続化）    |
