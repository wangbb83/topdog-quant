工程目录
- bak：历史代码，无需关注
- share_daily_qfq：每日日线行情，是行情的数据文件，一个代码的txt代表这只股票的日线行情数据，离线数据每日更新

项目说明
- 本项目用于扫描A股日线数据，识别两类涨停组合形态，并输出匹配结果
- 形态逻辑实现于 `pattern.py`，批量扫描与结果落盘在 `test_run.py`

数据获取
- `syncQuote.py` 使用 AkShare 拉取前复权日线，默认保存到 `share_daily_qfq/`
- 文件名为股票代码，支持 `.txt` 与 `.csv`，字段将自动转换为 `date/open/high/low/close/volume/amount`

形态规则摘要
- 自定义形态：涨停前一日收盘与60日均线偏离<=5.3%；连续4-6个涨停；随后一天非涨停且跌幅<=6%；再下一天涨停；再下一天开盘直接触及涨停
- 连板组合：A方案为连续4个涨停满足开盘/最低价条件；B方案为连续3个涨停满足同样条件

运行方式
- 扫描本地数据：`python test_run.py`
- 获取数据后再扫描：先运行 `python syncQuote.py`，再运行 `python test_run.py`

输出说明
- 结果写入 `result.txt`（JSON 格式），包含 `custom` 与 `combo` 两类匹配明细和计数

依赖
- pandas
- akshare（仅 `syncQuote.py` 需要）
- tqdm、tenacity（仅 `syncQuote.py` 需要）
