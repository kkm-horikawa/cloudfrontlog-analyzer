# GitHub Copilot 指示

## コミットメッセージ生成ルール

コミットメッセージを生成する際は、以下のルールに従ってください：

- **必ず日本語で記述する**
- **Conventional Commits形式を使用する**（feat:, fix:, docs:, refactor:, style:, test:, chore:）
- **簡潔で明確に説明する**
- **変更内容を具体的に記述する**

### 例

- `feat: ユーザー認証機能を追加`
- `fix: ログアウト時のセッションエラーを修正`
- `refactor: API呼び出しロジックをリファクタリング`
- `docs: READMEにセットアップ手順を追記`

## コーディング規約

### Python (Backend)

- Django プロジェクト
- 型ヒントを使用
- Ruff でフォーマット

### TypeScript (Frontend)

- React + Vite プロジェクト
- 厳密な型チェック
- Biome でフォーマット・lint
- 相対パスでインポート
