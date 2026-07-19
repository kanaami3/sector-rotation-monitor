# Sector Rotation Monitor

トレンド転換・セクターローテーション監視サイト。
RRG(相対ローテーショングラフ) + トレンド転換アラート + 週次ブリーフ(AI自動生成)。

## 構成

```
site/
├── index.html                  # サイト本体(3ページ統合・data/*.json を読み込み)
├── data/
│   ├── market_data.json        # fetch_data.py が出力(相対力・騰落率)
│   └── brief.json              # generate_brief.py が出力(週次総括)
├── pipeline/
│   ├── fetch_data.py           # yfinanceで日本14業種バスケット取得→RS計算
│   └── generate_brief.py       # Claude APIで週次ブリーフ生成
└── .github/workflows/update.yml # 平日朝の自動更新
```

## ローカルで動かす

```bash
pip install yfinance pandas requests

# 1. 実データ取得(数分かかります)
python pipeline/fetch_data.py

# 2. (任意) 週次ブリーフをAI生成
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline/generate_brief.py

# 3. サイト表示(fetchを使うためローカルサーバー経由で)
python -m http.server 8000
# → http://localhost:8000 を開く
```

data/ が空でもサンプルデータで動作します(右上に「サンプルデータ」表示)。

## 自動運用(無料)

1. このフォルダをGitHubリポジトリにpush
2. Settings → Pages → Branch: main を選択(サイト公開)
3. Settings → Secrets → `ANTHROPIC_API_KEY` を登録(ブリーフ生成用・任意)
4. Actionsが平日朝7:30(JST)にデータ更新、月曜にブリーフ再生成

## データソースの差し替え

- 現在: yfinance(業種代表銘柄の等ウェイトバスケット)。手軽だが非公式APIのため個人利用向け
- 本格運用: `fetch_data.py` の `build_sector_series()` をJ-Quants API(東証33業種指数)に差し替え。
  出力JSONの形式は同じなのでフロントは変更不要

## 免責

本サイトは情報整理・学習目的であり、投資助言ではありません。
