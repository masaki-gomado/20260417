# API リファレンス

## 概要

現在実装されているAPIエンドポイントは以下の通りです。

---

## エンドポイント一覧

### `GET /`

トップページ（ポモドーロタイマーUI）を返します。

**レスポンス**

| 項目 | 値 |
|---|---|
| ステータスコード | `200 OK` |
| Content-Type | `text/html; charset=utf-8` |

**レスポンス例**

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ポモドーロタイマー</title>
    ...
</head>
<body></body>
</html>
```

**エラーレスポンス**

| ステータスコード | 説明 |
|---|---|
| `404 Not Found` | 存在しないパスへのアクセス |

---

## 未実装エンドポイント（計画中）

以下のエンドポイントは `features.md` に定義されていますが、現時点では未実装です。

| メソッド | パス | 概要 |
|---|---|---|
| `GET` | `/api/settings` | 保存済み設定の取得 |
| `POST` | `/api/settings` | 作業時間・休憩時間のカスタマイズ保存 |
| `POST` | `/api/sessions` | 完了セッションの記録 |
