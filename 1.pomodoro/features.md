# ポモドーロタイマー 実装機能一覧

## Phase 1 — コア機能（最優先）

### タイマー機能
- [ ] カウントダウン表示（`MM:SS` 形式）
- [ ] 開始 / 一時停止 / 再開
- [ ] リセット（現在のセッションをゼロに戻す）
- [ ] タイマー終了の検知

### モード切替
- [ ] 作業（25分）
- [ ] 短い休憩（5分）
- [ ] 長い休憩（15分）
- [ ] タブ切替でモードを変更（手動）

### セッション管理
- [ ] 4回の作業セッションで長い休憩に自動移行
- [ ] ポモドーロ回数インジケーター（● ● ● ○ 形式）
- [ ] 現在のセッション種別の状態保持（`IDLE / RUNNING / PAUSED / FINISHED`）

---

## Phase 2 — UX改善

### 通知・フィードバック
- [ ] セッション終了時のブラウザ通知（`Notification API`）
- [ ] アラーム音の再生（`Web Audio API` または音声ファイル）
- [ ] タブタイトルへのタイマー残時間表示（`document.title`）

### アニメーション
- [ ] タイマー進行に合わせた円形プログレスバー（SVG）
- [ ] モード切替時のトランジション

---

## Phase 3 — 永続化（Flask API）

### 設定
- [ ] `GET /api/settings` — 保存済み設定の取得
- [ ] `POST /api/settings` — 作業時間・休憩時間のカスタマイズ保存

### セッション履歴
- [ ] `POST /api/sessions` — 完了セッションの記録
- [ ] 累計ポモドーロ数・作業時間の集計表示（任意）

---

## フロントエンド構成ファイル別の実装内容

| ファイル | 実装内容 |
|---|---|
| `static/js/timer-core.js` | 状態機械・`tick()` / `start()` / `pause()` / `reset()` |
| `static/js/timer.js` | `setInterval` ラッパー（依存注入対応） |
| `static/js/app.js` | DOM バインディング・通知・音声 |
| `static/css/style.css` | タイマーUI・アニメーション・モード別カラーテーマ |
| `templates/index.html` | モード切替タブ・タイマー表示・コントロールボタン |

## バックエンド構成ファイル別の実装内容

| ファイル | 実装内容 |
|---|---|
| `app.py` | ルート定義（`GET /`、`/api/settings`、`/api/sessions`） |
| `services/session_service.py` | バリデーション・集計ロジック |
| `repositories/session_repo.py` | データアクセス（JSON/SQLite） |
