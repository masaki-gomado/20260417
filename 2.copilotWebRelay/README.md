# Copilot Web Relay - AI チャット Web アプリケーション

GitHub Copilot SDK を使ったブラウザ上で動作する AI チャットアプリケーションです。

## アーキテクチャ

```
ブラウザ (React + TypeScript + Vite)
    ↕ WebSocket
Express + WS サーバー (Node.js)
    ↕ JSON-RPC
Copilot SDK / CLI
```

## 機能

- **ストリーミングレスポンス** — AI の応答をリアルタイムで表示
- **Markdown レンダリング** — コードブロック、テーブル、リスト等に対応
- **モダンな UI** — ダーク/ライトモード自動対応、レスポンシブデザイン
- **自動再接続** — WebSocket 切断時に自動的に再接続

## セットアップ

```bash
# 依存関係のインストール
npm run install:all
npm install
```

## 開発

```bash
# バックエンドとフロントエンドを同時起動
npm run dev
```

- フロントエンド: http://localhost:5173
- バックエンド API: http://localhost:3001
- WebSocket: ws://localhost:3001/ws

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | React 19, TypeScript, Vite |
| バックエンド | Node.js, Express 5, ws |
| AI | @github/copilot-sdk (gpt-5.4) |
| Markdown | react-markdown, remark-gfm |
