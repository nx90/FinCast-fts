import argparse
import os
from datetime import datetime
import re

import numpy as np
import pandas as pd


def _ensure_datetime(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    return pd.to_datetime(s, errors="coerce")


def _load_parquet_series(parquet_path: str) -> pd.DataFrame:
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet not found: {parquet_path}")

    df = pd.read_parquet(parquet_path).reset_index()

    if "trade_time" in df.columns:
        df["date"] = pd.to_datetime(df["trade_time"], errors="coerce")
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        raise ValueError(f"Could not find 'trade_time' or 'date'. Columns are: {list(df.columns)}")

    if "Close" not in df.columns:
        if "close" in df.columns:
            df = df.rename(columns={"close": "Close"})
        else:
            raise ValueError(f"Could not find 'Close'/'close'. Columns are: {list(df.columns)}")

    out = df[["date", "Close"]].copy()
    out = out.dropna(subset=["date", "Close"]).sort_values("date")
    out = out.drop_duplicates(subset=["date"], keep="last")
    return out


def _fetch_today_1m_from_akshare(symbol_6: str) -> pd.DataFrame:
    try:
        import akshare as ak
    except Exception as e:
        raise RuntimeError(
            "AkShare is not available. Please install it in your environment (e.g. `pip install akshare`)."
        ) from e

    today = datetime.now().strftime("%Y%m%d")
    df = ak.stock_zh_a_hist_min_em(symbol=symbol_6, start_date=today, end_date=today, period="1", adjust="")

    if df is None:
        return pd.DataFrame(columns=["date", "Close"])

    if not isinstance(df, pd.DataFrame):
        # Some AkShare endpoints may return list/dict under edge cases; try to coerce.
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame(columns=["date", "Close"])

    if len(df) == 0:
        return pd.DataFrame(columns=["date", "Close"])

    col_time = "时间" if "时间" in df.columns else ("日期" if "日期" in df.columns else None)
    col_close = "收盘" if "收盘" in df.columns else ("close" if "close" in df.columns else None)
    if col_time is None or col_close is None:
        raise ValueError(f"Unexpected AkShare columns: {list(df.columns)}")

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[col_time], errors="coerce"),
            "Close": pd.to_numeric(df[col_close], errors="coerce"),
        }
    )
    out = out.dropna(subset=["date", "Close"]).sort_values("date")
    out = out.drop_duplicates(subset=["date"], keep="last")
    return out


def _symbol_to_akshare_6(symbol: str) -> str:
    """Return the 6-digit code for AkShare.

    Accepts inputs like: 002324.SZ / 600869.SH / 920270.BJ / 002324
    """
    s = symbol.strip().upper()
    if "." in s:
        s = s.split(".")[0]
    # keep only digits
    digits = re.sub(r"\D", "", s)
    return digits


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare FinCast inference CSV from local parquet (optionally merging AkShare today's 1-min data).")
    parser.add_argument("--symbol", default="600869.SH", help="Stock symbol, e.g. 002324.SZ or 600869.SH")
    parser.add_argument(
        "--data-dir",
        default=r"D:\qlib_source_data_supplement_1min\stock_1min",
        help="Directory containing <symbol>.parquet files",
    )
    parser.add_argument("--tail", type=int, default=2000, help="Keep last N rows")
    parser.add_argument(
        "--use-akshare",
        action="store_true",
        help="Merge today's 1-minute data fetched via AkShare (A-share) before exporting",
    )
    args = parser.parse_args()

    symbol = args.symbol.strip()
    parquet_name = f"{symbol}.parquet" if not symbol.endswith(".parquet") else symbol
    parquet_name = parquet_name.replace(".PARQUET", ".parquet")
    parquet_path = os.path.join(args.data_dir, parquet_name)

    project_root = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(project_root, "input")
    os.makedirs(input_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(parquet_name))[0]
    output_csv_path = os.path.join(input_dir, f"{base_name}.csv")

    print(f"Reading {parquet_path}...")
    try:
        local_df = _load_parquet_series(parquet_path)
    except Exception as e:
        print(f"Error reading parquet: {e}")
        return 1

    merged = local_df

    if args.use_akshare:
        ak_symbol = _symbol_to_akshare_6(symbol)
        if not ak_symbol:
            print(f"WARNING: Could not derive numeric code from symbol '{symbol}', skipping AkShare merge.")
        else:
            print(f"Fetching today's 1-min data via AkShare for {ak_symbol}...")
            try:
                today_df = _fetch_today_1m_from_akshare(ak_symbol)
                print(f"AkShare today rows: {len(today_df)}")
                if len(today_df) > 0:
                    merged = pd.concat([local_df, today_df], ignore_index=True)
                else:
                    print("WARNING: AkShare returned no rows for today; using parquet only.")
            except Exception as e:
                # Non-fatal: still allow preparing parquet-based inference file.
                print(f"WARNING: AkShare fetch failed ({e}); using parquet only.")

    merged["date"] = _ensure_datetime(merged["date"])
    merged = merged.dropna(subset=["date", "Close"]).sort_values("date")
    merged = merged.drop_duplicates(subset=["date"], keep="last")

    if args.tail and args.tail > 0:
        merged = merged.tail(args.tail)

    print(f"Saving last {len(merged)} rows to {output_csv_path}...")
    merged.to_csv(output_csv_path, index=False)
    print("Done. File created.")
    print(merged.tail())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
