"""
セクター別 移動平均乖離率ランキング — データ取得パイプライン (yfinance無料版)
============================================================================
universe.py の主要銘柄ユニバースを yfinance で取得し、各銘柄の
移動平均乖離率を計算して、業種ごとに乖離の大きい順トップ50を
data/deviation.json に出力する。認証不要・当日データ。

乖離率 = (直近終値 / N日単純移動平均 - 1) * 100   (Nは MA_WINDOWS)

使い方:
    pip install yfinance pandas
    python pipeline/fetch_deviation.py
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from universe import SECTOR_UNIVERSE, all_pairs

OUT = Path(__file__).resolve().parent.parent / "data" / "deviation.json"

MA_WINDOWS = [25, 75]     # 計算する移動平均日数(先頭が主指標=ランキング基準)
PRIMARY_MA = MA_WINDOWS[0]
TOP_N = 50                # 業種ごとに出す上位件数


def download_closes(tickers: list[str], period: str = "6mo") -> pd.DataFrame:
    """日次終値(調整後)のフレーム。列は ".T" 無しの4桁コード。"""
    data = yf.download(tickers, period=period, interval="1d",
                       auto_adjust=True, progress=False, group_by="ticker")
    out = {}
    for t in tickers:
        try:
            s = data[t]["Close"].dropna() if len(tickers) > 1 else data["Close"].dropna()
            if len(s) > PRIMARY_MA:
                out[t.replace(".T", "")] = s
        except (KeyError, TypeError):
            continue
    return pd.DataFrame(out)


def main():
    pairs = all_pairs()                       # [(sector, code, name), ...]
    name_map = {code: name for _, code, name in pairs}
    sector_map = {code: sector for sector, code, _ in pairs}
    tickers = [f"{code}.T" for _, code, _ in pairs]
    print(f"取得対象: {len(tickers)}銘柄 / {len(SECTOR_UNIVERSE)}業種")

    prices = download_closes(tickers)
    if prices.empty:
        raise SystemExit("価格データを取得できませんでした")
    as_of = prices.index[-1].strftime("%Y-%m-%d")

    # 各銘柄の乖離率を計算
    records = []
    for code in prices.columns:
        s = prices[code].dropna()
        if len(s) < PRIMARY_MA:
            continue
        close = float(s.iloc[-1])
        devs = {}
        for w in MA_WINDOWS:
            if len(s) >= w:
                ma = float(s.iloc[-w:].mean())
                if ma > 0:
                    devs[f"dev{w}"] = round((close / ma - 1) * 100, 2)
        if f"dev{PRIMARY_MA}" not in devs:
            continue
        records.append({
            "code": code,
            "name": name_map.get(code, code),
            "sector": sector_map.get(code, "その他"),
            "close": round(close, 1),
            **devs,
        })

    # 業種ごとに |主指標乖離| の大きい順トップN
    primary_key = f"dev{PRIMARY_MA}"
    by_sector: dict[str, list] = {}
    for r in records:
        by_sector.setdefault(r["sector"], []).append(r)

    sectors_out = []
    for sector in SECTOR_UNIVERSE:            # 定義順を維持
        rows = by_sector.get(sector, [])
        rows.sort(key=lambda r: abs(r[primary_key]), reverse=True)
        sectors_out.append({
            "name": sector,
            "count": len(rows),
            "stocks": rows[:TOP_N],
        })

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": as_of,
        "source": "yfinance(主要銘柄ユニバース)",
        "ma_windows": MA_WINDOWS,
        "primary_ma": PRIMARY_MA,
        "top_n": TOP_N,
        "sectors": sectors_out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    total = sum(s["count"] for s in sectors_out)
    print(f"完了: {OUT} ({len(sectors_out)}業種 / {total}銘柄 / 基準日 {as_of})")


if __name__ == "__main__":
    main()
