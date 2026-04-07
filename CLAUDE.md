# TEAMZ AI Hackathon — 2026-04-07

## Overview
TEAMZ AI Hackathon @ Happo-en, Tokyo (13:00-18:00 JST)
自作のAIアシスタント/アプリを構築し、Zeaburでデプロイして公開する。

## Architecture Decision
- **OpenClawは使わない** — 独自コードを構築してデプロイする
- **Zeabur** — 自作アプリのデプロイ・公開用（クレジットコード: `BUILDER0407`）
- **TiDB Cloud Zero** — 必要に応じてDB利用（サインアップ不要、30日無料、$1上限）
- **Agnes AI / Bright Data / Mem9 / Nosana / QoderWork** — スポンサーツール。審査で活用度が問われるため、可能な範囲で組み込む

## Judging Criteria
1. MVP完成度・動作するプロダクト
2. イノベーション（コンセプトの新しさ）
3. 実世界の課題解決
4. スポンサーテクノロジーの活用度

## Deploy
```bash
# Zeabur CLI でデプロイ
npx zeabur@latest deploy
```
詳細: `docs/setup/zeabur-deploy.md`

## Docs
プロジェクトドキュメントは `docs/` で管理:
- `docs/architecture.md` — アーキテクチャ設計
- `docs/setup/` — セットアップ手順
- `docs/sponsors/` — スポンサーツールのAPI・設定リファレンス

## Key Links
- Tutorial: https://tutorial.theaibuilders.dev/tutorials/Automation/openclaw
- Submission: tinyurl.com/openclawsubmit
- Chat: tinyurl.com/openclawchat
- Zeabur Template (参考): https://zeabur.com/templates/VTZ4FX
