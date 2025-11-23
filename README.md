# CloudFront Log Analyzer

CloudFrontのアクセスログを検索・分析するためのWebアプリケーション

## 🚀 Docker Composeで起動（推奨）

AWS認証情報を設定後、以下のコマンドで起動できます:

```bash
# AWS認証情報を設定（未設定の場合）
aws configure --profile default

# Docker Composeで起動
docker compose up -d

# ログ確認
docker compose logs -f

# 停止
docker compose down
```

起動後、ブラウザで http://localhost:5173 を開いてください。

必要な権限:
- `cloudfront:ListDistributions`
- `cloudfront:GetDistributionConfig`
- `s3:ListBucket`
- `s3:GetObject`

---

## クイックスタート（ローカル開発）

### 1. AWS認証情報の設定

AWSプロファイルを設定します（未設定の場合）:

```bash
aws configure --profile <profile_name>
# AWS Access Key ID、Secret Access Key、Regionを入力
```

### 2. バックエンド起動

**必要な環境:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
cd backend
uv sync                              # 依存関係インストール
uv run python manage.py migrate      # DB初期化
uv run python manage.py runserver    # サーバー起動 (http://localhost:8000)
```

### 3. フロントエンド起動

**必要な環境:** Node.js 22+

```bash
cd frontend
npm install    # 依存関係インスト`ール
npm run dev    # サーバー起動 (http://localhost:5173)
```

### 4. 使い方

1. ブラウザで http://localhost:5173 を開く
2. AWSプロファイル名を入力（例: `default`）
3. 「Load Distributions」をクリック
4. ディストリビューションを選択
5. 検索条件を入力（URLパス、日付、時刻）
6. 「Search Logs」をクリック

---

## 技術スタック

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS 4
- Biome (lint/format)

### Backend
- Django 5.2 + Django REST Framework
- boto3 (AWS SDK)
- uv (パッケージ管理)

## アーキテクチャ

```
cloudfront-analyzer-webapp/
├── frontend/    # React アプリケーション
└── backend/     # Django API サーバー
```

AWS認証情報はバックエンドのみで管理し、ブラウザから直接AWSにアクセスしない安全な設計です。

## API エンドポイント

### GET /api/cloudfront/distributions/
CloudFrontディストリビューション一覧を取得

**Query Parameters:**
- `profile`: AWS CLIプロファイル名（デフォルト: `default`）

**Response:**
```json
[
  {
    "id": "E3K6JPV795PQRV",
    "domain": "d3l9lc6hpw1f9p.cloudfront.net",
    "aliases": ["defaulttech.co.jp"]
  }
]
```

### POST /api/cloudfront/logs/search/
CloudFrontログを検索

**Query Parameters:**
- `profile`: AWS CLIプロファイル名（デフォルト: `default`）

**Request Body:**
```json
{
  "distributionId": "E3K6JPV795PQRV",
  "targetUrl": "/nattoku/special/91265/77164/",
  "dateTime": "2025-11-12T13:42:00+09:00",
  "timeWindowMinutes": 5
}
```

**Response:**
```json
[
  {
    "date": "2025-11-12",
    "time": "04:42:15",
    "clientIp": "203.0.113.42",
    "method": "GET",
    "uriStem": "/nattoku/special/91265/77164/",
    "statusCode": 200,
    ...
  }
]
```

## 開発者向け情報

### Frontend

```bash
cd frontend
npm run lint:fix    # リント・フォーマット
npm run build       # 本番ビルド
```

### Backend

```bash
cd backend
uv run python manage.py test    # テスト実行
```

## その他の情報

### ログ検索の仕様
- 検索時刻はJSTで入力され、内部でUTCに変換されます
- デフォルトで指定時刻の前後5分間を検索します

## Dockerクリーンアップ

### 基本: コンテナを停止して削除

```bash
docker-compose down
```

### ボリュームも一緒に削除（ログキャッシュも消える）

```bash
docker-compose down -v
```

### イメージも削除（完全クリーンアップ）

```bash
docker-compose down --rmi all
```

### さらにビルドキャッシュも削除したい場合

```bash
docker builder prune
```

### よく使うパターン

#### 設定を変更したのでイメージを再ビルドしたい場合

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### または一発で

```bash
docker-compose up -d --build --force-recreate
```

### 個別コンテナを削除

#### 実行中のコンテナを確認

```bash
docker ps -a
```

#### 特定のコンテナを削除

```bash
docker rm -f cloudfront-analyzer-frontend
docker rm -f cloudfront-analyzer-backend
```

#### イメージも確認

```bash
docker images
```

#### 特定のイメージを削除

```bash
docker rmi cloudfront-anarizer-webapp-frontend
docker rmi cloudfront-anarizer-webapp-backend
```
