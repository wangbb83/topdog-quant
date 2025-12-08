from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


class ColumnRenameMap:
    """行情列名映射实体类，集中管理字段重命名，供全局复用。"""

    MAP: Dict[str, str] = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "pct_chg",
    }


class PatternFinder:
    """专门用于检测股票价格形态的工具类。"""

    def __init__(self, open_limit_tol: float = 0.001, limit_open_buffer: float = 0.005) -> None:
        # open_limit_tol：判断开盘是否触及涨停价的容忍度
        # limit_open_buffer：用于放宽涨停收益率判断的缓冲值
        self.open_limit_tol = open_limit_tol
        self.limit_open_buffer = limit_open_buffer

    @staticmethod
    def _get_limit_up_pct(code: str) -> int:
        """
        根据股票代码前缀返回对应的涨停幅度。
        A股：常规10%，科创/创业/BJ 20%，ST 30%。
        """
        if code.startswith(("1", "68", "3")):
            return 20
        if code.startswith(("4", "8", "9")):
            return 30
        return 10

    @staticmethod
    def _load_price_df(file_path: str) -> pd.DataFrame:
        """
        读取日线数据并生成形态识别所需的基础指标。
        兼容本地同步得到的UTF-8 CSV和旧版GBK制表符文本。
        """
        read_attempts = [
            dict(sep=",", encoding="utf-8", engine="python"),
            dict(sep=",", encoding="utf-8-sig", engine="python"),
            dict(sep="\t", encoding="gbk", skiprows=1, skipfooter=1, engine="python"),
            dict(sep=",", encoding="gbk", engine="python"),
        ]
        last_exc = None
        df = None
        for params in read_attempts:
            try:
                df = pd.read_csv(file_path, **params)
                break
            except Exception as exc:
                last_exc = exc
                continue
        if df is None:
            raise last_exc

        df.rename(columns=ColumnRenameMap.MAP, inplace=True)

        base_cols = ["date", "open", "high", "low", "close", "volume", "amount"]
        if all(col in df.columns for col in base_cols):
            df = df[base_cols + [c for c in df.columns if c not in base_cols]]
        else:
            if len(df.columns) >= 7:
                df = df.iloc[:, :7]
                df.columns = base_cols

        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="%Y%m%d")
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["ret"] = df["close"].pct_change()
        df["ma60"] = df["close"].rolling(60).mean()
        return df

    def find_custom_pattern(self, file_path: str) -> List[Dict[str, Any]]:
        """
        规则：
        1) 涨停前一日收盘与60日均线偏离在5.3%以内（可为负）。
        2) 连续4-6个涨停。
        3) 随后一天非涨停且跌幅不超过6%。
        4) 再下一天涨停，且再下一天开盘直接触及涨停。
        """
        code = Path(file_path).stem
        limit_pct = self._get_limit_up_pct(code)
        limit_threshold = limit_pct / 100.0 - self.limit_open_buffer

        df = self._load_price_df(file_path)
        results: List[Dict[str, Any]] = []

        for i in range(60, len(df) - 3):
            # 第一个涨停日
            if df.loc[i, "ret"] < limit_threshold:
                continue

            # 条件1：前一日距离MA60
            ma60_prev = df.loc[i - 1, "ma60"]
            if pd.isna(ma60_prev) or ma60_prev == 0:
                continue
            dist_prev = (df.loc[i - 1, "close"] - ma60_prev) / ma60_prev * 100
            if dist_prev >= 5.3:
                continue

            # 统计连续涨停天数
            j = i
            cnt_limit = 0
            while j < len(df) and df.loc[j, "ret"] >= limit_threshold:
                cnt_limit += 1
                j += 1
            if cnt_limit < 4 or cnt_limit > 6:
                continue

            # 涨停结束后的第一天不能大跌，也不能继续涨停
            if j >= len(df):
                continue
            if df.loc[j, "ret"] < -0.06:
                continue
            if df.loc[j, "ret"] >= limit_threshold:
                continue

            # 下一天必须再涨停
            if j + 1 >= len(df) or df.loc[j + 1, "ret"] < limit_threshold:
                continue

            # 再下一天开盘需直接触及涨停
            if j + 2 >= len(df):
                continue
            prev_close = df.loc[j + 1, "close"]
            next_open = df.loc[j + 2, "open"]
            if next_open < prev_close * (1 + limit_pct / 100.0 - self.open_limit_tol):
                continue

            results.append(
                {
                    "code": code,
                    "first_limit_date": df.loc[i, "date"].date(),
                    "before_first_limit_date": df.loc[i - 1, "date"].date(),
                    "before_dist_pct": round(dist_prev, 2),
                    "limit_run_len": cnt_limit,
                    "first_non_limit_date": df.loc[j, "date"].date(),
                    "first_non_limit_ret_pct": round(df.loc[j, "ret"] * 100, 2),
                    "next_limit_date": df.loc[j + 1, "date"].date(),
                    "next_open_limit_date": df.loc[j + 2, "date"].date(),
                    "next_open_pct_vs_prev_close": round((next_open / prev_close - 1) * 100, 2),
                }
            )
        return results

    def find_limit_combo_pattern(self, file_path: str) -> List[Dict[str, Any]]:
        """
        规则：
        方案A：
            1) 涨停前一日收盘与60日均线的偏离 < 5.3%（可为负）。
            2) 连续4个涨停，要求：
               - 第1、2个涨停：开盘涨幅不超过3%；
               - 第3个涨停：开盘涨停且最低价 < 开盘价；
               - 第4个涨停：开盘涨幅在[-3%, 3%]，且开盘价为全日最低价。
        方案B：
            1) 同上偏离要求；
            2) 连续3个涨停：
               - 第1个：开盘涨幅不超过3%；
               - 第2个：开盘涨停且最低价 < 开盘价；
               - 第3个：开盘涨幅在[-3%, 3%]，且开盘价为全日最低价。
        返回匹配列表，标注方案类型（A/B）。
        """
        code = Path(file_path).stem
        limit_pct = self._get_limit_up_pct(code)
        limit_threshold = limit_pct / 100.0 - self.limit_open_buffer

        df = self._load_price_df(file_path)
        results: List[Dict[str, Any]] = []

        def open_pct(idx: int) -> float:
            prev_close = df.loc[idx - 1, "close"]
            if prev_close == 0:
                return 0.0
            return (df.loc[idx, "open"] / prev_close - 1) * 100

        def within_ma60(idx: int) -> float:
            ma60_prev = df.loc[idx, "ma60"]
            if pd.isna(ma60_prev) or ma60_prev == 0:
                return 1e9
            return (df.loc[idx, "close"] - ma60_prev) / ma60_prev * 100

        n = len(df)
        for i in range(60, n):
            # 前一日偏离要求
            dist_prev = within_ma60(i - 1)
            if dist_prev >= 5.3:
                continue

            # 方案A：4连板组合
            if i + 3 < n:
                cond = (
                    df.loc[i, "ret"] >= limit_threshold
                    and df.loc[i + 1, "ret"] >= limit_threshold
                    and df.loc[i + 2, "ret"] >= limit_threshold
                    and df.loc[i + 3, "ret"] >= limit_threshold
                )
                if cond:
                    o0, o1, o2, o3 = open_pct(i), open_pct(i + 1), open_pct(i + 2), open_pct(i + 3)
                    cond12 = o0 <= 3.0 and o1 <= 3.0
                    open_limit_3 = o2 >= limit_pct - self.open_limit_tol * 100
                    low_below_open_3 = df.loc[i + 2, "low"] < df.loc[i + 2, "open"]
                    cond4_open = -3.0 < o3 <= 3.0
                    open_is_low_4 = df.loc[i + 3, "low"] <= df.loc[i + 3, "open"] + 1e-6

                    if cond12 and open_limit_3 and low_below_open_3 and cond4_open and open_is_low_4:
                        results.append(
                            {
                                "code": code,
                                "pattern": "A",
                                "start_date": df.loc[i, "date"].date(),
                                "dates": [
                                    df.loc[i, "date"].date(),
                                    df.loc[i + 1, "date"].date(),
                                    df.loc[i + 2, "date"].date(),
                                    df.loc[i + 3, "date"].date(),
                                ],
                                "open_pcts": [round(o0, 2), round(o1, 2), round(o2, 2), round(o3, 2)],
                                "before_ma60_dist_pct": round(dist_prev, 2),
                            }
                        )

            # 方案B：3连板组合
            if i + 2 < n:
                cond = (
                    df.loc[i, "ret"] >= limit_threshold
                    and df.loc[i + 1, "ret"] >= limit_threshold
                    and df.loc[i + 2, "ret"] >= limit_threshold
                )
                if cond:
                    o0, o1, o2 = open_pct(i), open_pct(i + 1), open_pct(i + 2)
                    cond1 = o0 <= 3.0
                    open_limit_2 = o1 >= limit_pct - self.open_limit_tol * 100
                    low_below_open_2 = df.loc[i + 1, "low"] < df.loc[i + 1, "open"]
                    cond3_open = -3.0 < o2 <= 3.0
                    open_is_low_3 = df.loc[i + 2, "low"] <= df.loc[i + 2, "open"] + 1e-6

                    if cond1 and open_limit_2 and low_below_open_2 and cond3_open and open_is_low_3:
                        results.append(
                            {
                                "code": code,
                                "pattern": "B",
                                "start_date": df.loc[i, "date"].date(),
                                "dates": [
                                    df.loc[i, "date"].date(),
                                    df.loc[i + 1, "date"].date(),
                                    df.loc[i + 2, "date"].date(),
                                ],
                                "open_pcts": [round(o0, 2), round(o1, 2), round(o2, 2)],
                                "before_ma60_dist_pct": round(dist_prev, 2),
                            }
                        )

        return results


__all__ = ["PatternFinder", "ColumnRenameMap"]
