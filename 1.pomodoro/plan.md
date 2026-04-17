# ポモドーロタイマー 段階的実装計画

## 方針

「テストできる単位で小さく作る」ことを軸に進める。
Step 2〜5 は DOM 不要なため、HTML/CSS の準備を待たず先行実装可能。

---

## Step 1: プロジェクト骨格の作成

**作成ファイル**
- `requirements.txt`（`Flask`、`pytest`、`pytest-flask`）
- `app.py` — `GET /` で `index.html` を返すだけ
- `templates/index.html` — タイトルと空の `<body>`
- `static/css/style.css`、`static/js/` ディレクトリ

**確認基準**: `flask run` でブランクページが表示される

---

## Step 2: `timer-core.js` — 純粋状態機械

**実装内容**
- `TimerCore` クラス（`IDLE / RUNNING / PAUSED / FINISHED` の状態遷移）
- `start()` / `pause()` / `reset()` / `tick()` / `getState()`
- DOM・`setInterval`・`Date` への依存ゼロ

**確認基準**: Node.js で `import` してコンソールから動作確認できる

---

## Step 3: `timer-core.test.js` — JS ユニットテスト

**実装内容**
- Vitest / Jest のセットアップ（`package.json`）
- `start()` → `tick()` でカウントダウンするか
- `FINISHED` 状態への遷移
- セッション種別（WORK / SHORT_BREAK / LONG_BREAK）の切替

**確認基準**: `npm test` がすべてグリーン

---

## Step 4: `timer.js` — `setInterval` ラッパー

**実装内容**
- `Timer` クラスが `TimerCore` を受け取り毎秒 `tick()` を呼ぶ
- `setInterval` / `clearInterval` をコンストラクタ注入

**確認基準**: Step 2 のテスト継続パス

---

## Step 5: `timer.test.js` — タイマーAPIのユニットテスト

**実装内容**
- フェイクタイマー（`vi.useFakeTimers()`）で `tick()` が毎秒呼ばれるか
- `pause()` でインターバルが止まるか

**確認基準**: `npm test` がすべてグリーン

---

## Step 6: `index.html` + `style.css` — 静的UIの構築

**実装内容**
- モード切替タブ（作業 / 短い休憩 / 長い休憩）
- タイマー表示エリア（`25:00`）
- 開始 / リセットボタン
- ポモドーロ回数インジケーター（`● ● ● ○`）
- CSS レイアウト・カラーテーマ

**確認基準**: ブラウザで静的な見た目が整う（動作不要）

---

## Step 7: `app.js` — DOM バインディング

**実装内容**
- `TimerCore` + `Timer` のインスタンス化
- ボタンクリックで `start()` / `pause()` / `reset()` 呼び出し
- 毎秒 `getState()` でタイマー表示を更新
- タブクリックでモード切替

**確認基準**: ブラウザでカウントダウンが動作する

---

## Step 8: セッション自動進行ロジック

**実装内容**
- `FINISHED` 検知 → 次のセッション種別へ自動移行
- 4回の WORK 完了で LONG_BREAK に切替
- インジケーターの `●` 更新

**確認基準**: 4回作業後に長い休憩へ自動遷移する

---

## Step 9: Phase 2 UX改善（順不同で追加可能）

| サブステップ | 内容 |
|---|---|
| 9a | SVG 円形プログレスバー |
| 9b | `document.title` にタイマー残時間表示 |
| 9c | セッション終了時の `Notification API` |
| 9d | アラーム音（`Web Audio API`） |
| 9e | モード切替アニメーション |

---

## Step 10: Flask バックエンド（Phase 3）

**実装内容と順番**

1. `repositories/session_repo.py` — インメモリ + JSON ファイル実装
2. `services/session_service.py` — バリデーション・集計
3. `app.py` に `/api/settings`・`/api/sessions` を追加
4. `tests/conftest.py` + `test_session_service.py` + `test_routes.py`
5. `app.js` にセッション完了時の `POST /api/sessions` 呼び出しを追加

**確認基準**: `pytest` がすべてグリーン、curl でAPIが応答する

---

## 依存関係サマリー

```
Step 1 (骨格)
  └── Step 2 (timer-core.js)
        └── Step 3 (timer-core テスト)
        └── Step 4 (timer.js)
              └── Step 5 (timer テスト)
  └── Step 6 (静的UI)
        └── Step 7 (app.js DOM バインディング)
              └── Step 8 (セッション自動進行)
                    └── Step 9a〜e (UX改善・順不同)
                    └── Step 10 (Flask API)
```
