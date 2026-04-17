# フロントエンド ドキュメント

## 現在の実装状態

**実装フェーズ**: Step 1（プロジェクト骨格）完了  
JavaScriptモジュールは未実装です。

---

## 実装済みファイル

### `templates/index.html`

Jinja2テンプレート。現在はページタイトルとCSSリンクのみ定義されており、`<body>` は空です。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ポモドーロタイマー</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
</body>
</html>
```

### `static/css/style.css`

スタイルシートファイルは作成済みですが、現時点ではコメント行のみで実装は空です。

---

## 計画中のJavaScriptモジュール（未実装）

`plan.md` に基づく実装予定のJSモジュール：

### `static/js/timer-core.js`（Step 2）

純粋状態機械。DOM・`setInterval`・`Date` への依存なし。

| メソッド | 説明 |
|---|---|
| `start()` | タイマーを開始（`IDLE`/`PAUSED` → `RUNNING`） |
| `pause()` | タイマーを一時停止（`RUNNING` → `PAUSED`） |
| `reset()` | タイマーをリセット（→ `IDLE`） |
| `tick()` | 1秒分カウントダウン、終了時に `FINISHED` へ遷移 |
| `getState()` | 現在の状態を返す |

### `static/js/timer.js`（Step 4）

`setInterval` ラッパー。`TimerCore` を受け取り毎秒 `tick()` を呼ぶ。  
`setInterval` / `clearInterval` はコンストラクタ注入でテスト可能にする設計。

### `static/js/app.js`（Step 7）

DOMバインディング層。

- `TimerCore` + `Timer` のインスタンス化
- ボタンクリックイベントで `start()` / `pause()` / `reset()` を呼び出し
- 毎秒 `getState()` でタイマー表示（`MM:SS` 形式）を更新
- タブクリックによるモード切替

---

## 計画中のUI構成（未実装）

Step 6（静的UI構築）で実装予定の画面要素：

| 要素 | 説明 |
|---|---|
| モード切替タブ | 作業 / 短い休憩 / 長い休憩 |
| タイマー表示 | `MM:SS` 形式のカウントダウン |
| 制御ボタン | 開始 / 一時停止 / リセット |
| ポモドーロ回数インジケーター | `● ● ● ○` 形式（4回で長い休憩） |
| 円形プログレスバー | SVGアニメーション（Phase 2） |

---

> JavaScriptモジュールの実装が進み次第、このドキュメントを更新してください。
