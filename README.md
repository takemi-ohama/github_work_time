# GitHub Work Time

GitHubユーザー向けの工数管理Webアプリケーションです。日々の作業時間（工数）を日報形式で記録・集計できます。

## 機能

- **日報管理**: 作業内容・工数・プロジェクトを日単位で登録・編集・削除
- **一覧表示**: 日付別にグループ化した工数一覧（フィルタリング対応）
- **集計・分析**: 
  - プロジェクト別工数（ドーナツチャート）
  - 日別工数（棒グラフ）
  - 週別・月別工数（棒グラフ）
- **GitHub OAuth認証**: GitHubアカウントでログイン
- **デモモード**: OAuth設定なしでも動作確認可能

## 技術スタック

- Python / Flask 3.x
- SQLAlchemy + SQLite
- Bootstrap 5 + Chart.js
- Authlib (GitHub OAuth)
- pytest

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定（オプション）

`.env` ファイルを作成し、以下を設定します：

```env
SECRET_KEY=your-secret-key
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

> **注意**: `GITHUB_CLIENT_ID` を設定しない場合、デモモードで動作し、自動的にデモユーザーとしてログインします。

### 3. GitHub OAuth App の作成（本番利用時）

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. Application name: `GitHub Work Time`
3. Homepage URL: `http://localhost:5000`
4. Authorization callback URL: `http://localhost:5000/auth/callback`

### 4. アプリの起動

```bash
python run.py
# または
flask run
```

ブラウザで http://localhost:5000 を開きます。

## テスト実行

```bash
python -m pytest tests/ -v
```

## 使い方

1. ログイン後、**日報** から工数を登録します
2. 作業日・プロジェクト・タイトル・工数（時間）を入力します
3. **集計・分析** で期間を指定して工数の集計を確認できます

## ライセンス

MIT License
