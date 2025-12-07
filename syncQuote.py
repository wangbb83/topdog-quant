import akshare as ak
import pandas as pd
from tqdm import tqdm
from tenacity import retry, wait_fixed, stop_after_attempt
import time, os

SAVE_DIR = "share_daily_qfq"
os.makedirs(SAVE_DIR, exist_ok=True)

# 取全市场代码表
code_df = ak.stock_info_a_code_name()   # 字段包含 symbol/code/name 等
codes = code_df['code'].tolist()        # e.g. 000001

@retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
def fetch_daily_qfq(code:str, start="20000101", end="20300101"):
    # AKShare: stock_zh_a_hist(symbol, period="daily", start_date, end_date, adjust="qfq")
    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
    # 规范字段
    df.rename(columns={
        "日期":"date","开盘":"open","收盘":"close","最高":"high","最低":"low",
        "成交量":"volume","成交额":"amount","涨跌幅":"pct_chg"
    }, inplace=True)
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df[['date','open','high','low','close','volume','amount','pct_chg']]

def save_all_codes2file():
    for code in tqdm(codes, desc="前复权日线"):
        save_code2file(code)

def save_code2file(code:str):
    path = os.path.join(SAVE_DIR, f"{code}.csv")
    if os.path.exists(path): 
        return
    try:
        df = fetch_daily_qfq(code)
        if not df.empty:
            df.to_csv(path, index=False, encoding="utf-8-sig")
        time.sleep(0.3)   # 建议间隔，避免被目标站限流
    except Exception:
        pd.DataFrame().to_csv(path, index=False)
    

if __name__ == '__main__':
    save_code2file("002583")