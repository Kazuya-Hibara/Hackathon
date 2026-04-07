# Zeabur デプロイ手順

## 認証
```bash
npx zeabur@latest auth login
```

## デプロイ（プロジェクトルートで実行）
```bash
npx zeabur@latest deploy
```
フレームワーク自動検出 → プロジェクト選択/作成 → デプロイ完了後URLが表示される。

## クレジットコード
`BUILDER0407`（2026-04-07 のみ有効）
Dedicated Server プランで使用。

## サービス管理
```bash
npx zeabur@latest service restart      # 再起動
npx zeabur@latest deployment get       # ステータス確認
npx zeabur@latest deployment log -t=runtime  # ランタイムログ
npx zeabur@latest deployment log -t=build    # ビルドログ
```

## 環境変数
Zeabur ダッシュボード → サービス → Variable タブで設定。
CLI からは設定不可、Web UI を使用。
