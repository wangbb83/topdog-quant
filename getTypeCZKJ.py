#先引入后面可能用到的包（package）
import time

import pandas as pd
from datetime import datetime
try:
    import backtrader as bt
except ImportError:
    bt = None
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
import os
from pathlib import Path
from pattern import PatternFinder
#%matplotlib inline

RED_DAYS = 10
SPLITTER = ";"
ZHANGFU_11YANG = 11.3
CONSECTIVE_DAYS = 4
CHENGJIAOE_MIN = 5000000
LEAST_ZHANGFU_NIU = 5.70
ERR_1E6 = 1E-6
ZHANGFU_HWJ_20CM = 11.4
ZHANGFU_HWJ_10CM = 5.7
DISTANTCE_TO_M60_HWJ = 16.0
LOWEST_ZHANGFU_HWJ = -4.0

def getType26(path,dateStr=None):

    valDate = None
    #commet 1-3
    #valDate = "20210112"
    portionToM60 = -100.0

    entries = os.listdir(path)

    # 过滤出文件
    files = [f for f in entries if os.path.isfile(os.path.join(path, f))]
    try:
        for file_name in files:
            try:
                #comment 2-3
                #file_name = 'GME.txt'
                #file_name = '00020.txt'
                code_list = file_name.split(".")
                stock_codes = code_list[0]
                df_all = pd.read_csv(path + file_name, sep='	', encoding='gbk', skiprows=1, skipfooter=1,
                                 engine='python')
                today = (time.strftime('%Y%m%d', time.localtime(time.time())))
                df_all.columns = df_all.columns.str.strip()
                #comment 3-3
                if (int(today) - df_all.iloc[df_all.shape[0] - 1]['日期'] > 15):
                    #continue  # 停牌了
                    pass

                end_line = df_all[df_all['日期'] == dateStr].index[0]
                begin_line = end_line - 200#截取最近200天的数据，减少计算量

                if(begin_line < 0):
                    begin_line = 0

                df_temp = df_all.iloc[begin_line:end_line+1]
                df = df_temp.copy()
                df['return'] = df['收盘'].pct_change().fillna(-2)
                df['return'] = df['return'] * 100#每日涨幅
                df['avg5'] = df['收盘'].rolling(5).mean()#5日均价
                df['avg13'] = df['收盘'].rolling(13).mean()#13日均价
                df['avg21'] = df['收盘'].rolling(21).mean()
                df['avg60'] = df['收盘'].rolling(60).mean()#60日均价
                df['avg125'] = df['收盘'].rolling(125).mean()

                # df['openPortion'] = None
                col = df.shape[0] - 1  # 行号
                if valDate is None:
                    pass
                else:
                    col = df.loc[df['日期'] == int(valDate)].index[0]

                portionToM60LastDay5 = (df.iloc[col-4]['收盘'] - df.iloc[col-4]['avg60']) / df.iloc[col-4]['avg60'] * 100#该股离60日线的涨幅
                zhangtingZhangfu = getZhangtingZhangfu(stock_codes)#涨停的涨幅：10%，20%，30%，未考虑ST
                try:
                    if abs(portionToM60LastDay5)<=5.2 and df.iloc[col-3]['return']>=LEAST_ZHANGFU_NIU and df.iloc[col-3]['return']<=9.9\
                    and df.iloc[col-2]['return']>=-2.1 and df.iloc[col-2]['return']<=0.5 \
                    and df.iloc[col-1]['return']>=LEAST_ZHANGFU_NIU and df.iloc[col-1]['return']<=9.9\
                    and df.iloc[col]['return']>=0 and df.iloc[col]['return']<=0.5\
                    and (df.iloc[col-1]['最低']+ERR_1E6 >=df.iloc[col-1]['开盘']) and (df.iloc[col]['最低']+ERR_1E6 >=df.iloc[col]['开盘']):#开盘价为全天最低价
                        # 603516淳中科技类，T+15
                        file_handle_type_czkj = open("C:\\gupiao\\type26.txt", mode='a')
                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "27czkj" + "\r\n"
                        file_handle_type_czkj.write(ret)
                        file_handle_type_czkj.flush()
                        file_handle_type_czkj.close()
                except:
                    print(stock_codes+"find type27 exception")

                try:
                    #type 28,hwj 688256

                    if df.iloc[col]['收盘'] >df.iloc[col]['开盘'] and df.iloc[col-1]['收盘'] >df.iloc[col-1]['开盘'] and df.iloc[col-2]['收盘'] >df.iloc[col-2]['开盘']\
                    and df.iloc[col-3]['收盘'] >df.iloc[col-3]['开盘'] and df.iloc[col-4]['收盘'] >df.iloc[col-4]['开盘'] and df.iloc[col-5]['收盘'] >df.iloc[col-5]['开盘']:
                        if zhangtingZhangfu == 10:
                            pass
                        elif zhangtingZhangfu == 20 or zhangtingZhangfu == 30:
                            if df.iloc[col - 7]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-8]['收盘'] <= df.iloc[col-8]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 8]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-9]['收盘'] <= df.iloc[col-9]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if  df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 9]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-10]['收盘'] <= df.iloc[col-10]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if  df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 10]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-11]['收盘'] <= df.iloc[col-11]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 11]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-12]['收盘'] <= df.iloc[col-12]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-10]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 12]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-13]['收盘'] <= df.iloc[col-13]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-11]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-10]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 13]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-14]['收盘'] <= df.iloc[col-14]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-12]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-11]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-10]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 14]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-15]['收盘'] <= df.iloc[col-15]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-13]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-12]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-11]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-10]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                            elif df.iloc[col - 15]['return'] > ZHANGFU_HWJ_20CM and df.iloc[col-16]['收盘'] <= df.iloc[col-16]['avg60']:
                                if df.iloc[col]['avg5'] > df.iloc[col]['avg13'] and df.iloc[col]['avg13']>df.iloc[col]['avg21'] and df.iloc[col]['avg21'] > df.iloc[col]['avg60'] and df.iloc[col]['收盘'] > df.iloc[col]['avg125']\
                                and df.iloc[col]['收盘'] >df.iloc[col]['avg5'] and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<DISTANTCE_TO_M60_HWJ:
                                    if df.iloc[col-14]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-13]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-12]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-11]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-10]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-9]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-8]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-7]['return'] >LOWEST_ZHANGFU_HWJ\
                                    and df.iloc[col-6]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-5]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-4]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col-3]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-2]['return'] >LOWEST_ZHANGFU_HWJ and df.iloc[col-1]['return'] >LOWEST_ZHANGFU_HWJ \
                                    and df.iloc[col]['return'] >LOWEST_ZHANGFU_HWJ:
                                        file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                                        ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "28hwj" + "\r\n"
                                        file_handle_type_hwj.write(ret)
                                        file_handle_type_hwj.flush()
                                        file_handle_type_hwj.close()
                except:
                    print(stock_codes + "find type28 exception")

                try:
                    #type 30,dzjt 600611,20240709
                    zhangtingZhangfu = getZhangtingZhangfu(stock_codes)
                    if zhangtingZhangfu == 10:
                        if df.iloc[col]['return']>=9 and (df.iloc[col]['收盘'] + ERR_1E6 <  df.iloc[col]['开盘']) and (df.iloc[col]['收盘'] - df.iloc[col]['开盘'] + ERR_1E6 >= -0.04) and (df.iloc[col]['收盘'] - df.iloc[col]['开盘'] - ERR_1E6 <= 0.0) \
                        and df.iloc[col-1]['return']>=5.7 and df.iloc[col-1]['return']<=9.5 and df.iloc[col-1]['开盘']<=df.iloc[col-1]['avg60'] and df.iloc[col-1]['收盘']>=df.iloc[col-1]['avg60']:
                            file_handle_type_dzjt = open("C:\\gupiao\\type26.txt", mode='a')
                            ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "30dzjt" + "\r\n"
                            file_handle_type_dzjt.write(ret)
                            file_handle_type_dzjt.flush()
                            file_handle_type_dzjt.close()
                    else:
                        if df.iloc[col]['return']>=18 and (df.iloc[col]['收盘'] + ERR_1E6 <  df.iloc[col]['开盘']) and (df.iloc[col]['收盘'] - df.iloc[col]['开盘'] + ERR_1E6 >= -0.04) and (df.iloc[col]['收盘'] - df.iloc[col]['开盘'] - ERR_1E6 <= 0.0) \
                        and df.iloc[col-1]['return']>=11.4 and df.iloc[col-1]['return']<=19 and df.iloc[col-1]['开盘']<=df.iloc[col-1]['avg60'] and df.iloc[col-1]['收盘']>=df.iloc[col-1]['avg60']:
                            file_handle_type_dzjt = open("C:\\gupiao\\type26.txt", mode='a')
                            ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "30dzjt" + "\r\n"
                            file_handle_type_dzjt.write(ret)
                            file_handle_type_dzjt.flush()
                            file_handle_type_dzjt.close()
                except:
                    pass

                #begin to find skgf600376 20250902\rhrj300339
                try:
                    if getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])>=0.0 and getDiffPortion(df.iloc[col]['avg60'],df.iloc[col]['收盘'])<=8.8: #1.last day,close portion to MA60 more than 0 and less than 8.8%
                        # 2.day of gaokai, close portion more than 4.8%
                        # 3.day of gaokai ,not zhangting
                        # 4.open price next day of gaokai  - open price last day between (-0.05,0.05)
                        ret_rhrj = False
                        max_loss_skgf = -6.5
                        zhangtingZhangfu_adj = zhangtingZhangfu -0.1
                        if df.iloc[col-18]['return']>=4.8 and getDiffPortion(df.iloc[col-19]['收盘'],df.iloc[col-18]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-18]['return'])==False and (abs(df.iloc[col-17]['开盘']-df.iloc[col-18]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,18):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-17]['return']>=4.8 and getDiffPortion(df.iloc[col-18]['收盘'],df.iloc[col-17]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-17]['return'])==False and (abs(df.iloc[col-16]['开盘']-df.iloc[col-17]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,17):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-16]['return']>=4.8 and getDiffPortion(df.iloc[col-17]['收盘'],df.iloc[col-16]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-16]['return'])==False and (abs(df.iloc[col-15]['开盘']-df.iloc[col-16]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,16):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-15]['return']>=4.8 and getDiffPortion(df.iloc[col-16]['收盘'],df.iloc[col-15]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-15]['return'])==False and (abs(df.iloc[col-14]['开盘']-df.iloc[col-15]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,15):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-14]['return']>=4.8 and getDiffPortion(df.iloc[col-15]['收盘'],df.iloc[col-14]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-14]['return'])==False and (abs(df.iloc[col-13]['开盘']-df.iloc[col-15]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,14):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-13]['return']>=4.8 and getDiffPortion(df.iloc[col-14]['收盘'],df.iloc[col-13]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-13]['return'])==False and (abs(df.iloc[col-12]['开盘']-df.iloc[col-13]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,13):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-12]['return']>=4.8 and getDiffPortion(df.iloc[col-13]['收盘'],df.iloc[col-12]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-12]['return'])==False and (abs(df.iloc[col-11]['开盘']-df.iloc[col-12]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,12):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-11]['return']>=4.8 and getDiffPortion(df.iloc[col-12]['收盘'],df.iloc[col-11]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-11]['return'])==False and (abs(df.iloc[col-10]['开盘']-df.iloc[col-11]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,11):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-10]['return']>=4.8 and getDiffPortion(df.iloc[col-11]['收盘'],df.iloc[col-10]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-10]['return'])==False and (abs(df.iloc[col-9]['开盘']-df.iloc[col-10]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,10):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-9]['return']>=4.8 and getDiffPortion(df.iloc[col-10]['收盘'],df.iloc[col-9]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-9]['return'])==False and (abs(df.iloc[col-8]['开盘']-df.iloc[col-9]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,9):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-8]['return']>=4.8 and getDiffPortion(df.iloc[col-9]['收盘'],df.iloc[col-8]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-8]['return'])==False and (abs(df.iloc[col-7]['开盘']-df.iloc[col-8]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,8):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-7]['return']>=4.8 and getDiffPortion(df.iloc[col-8]['收盘'],df.iloc[col-7]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-7]['return'])==False and (abs(df.iloc[col-6]['开盘']-df.iloc[col-7]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,7):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        elif df.iloc[col-6]['return']>=4.8 and getDiffPortion(df.iloc[col-7]['收盘'],df.iloc[col-6]['开盘'])>=4.8 and iszhangtingWithZhangfu(zhangtingZhangfu_adj,df.iloc[col-6]['return'])==False and (abs(df.iloc[col-5]['开盘']-df.iloc[col-6]['开盘'])<=0.05+ERR_1E6):
                            ret_rhrj = True
                            for i in range(0,6):
                                if df.iloc[col-i]['return']<=max_loss_skgf:
                                    ret_rhrj = False
                                    break
                        if ret_rhrj == True:
                            file_handle_type_hwj = open("C:\\gupiao\\type26.txt", mode='a')
                            ret = str(df.iloc[col]['日期']) + SPLITTER + stock_codes + SPLITTER + "31rhrj" + "\r\n"
                            file_handle_type_hwj.write(ret)
                            file_handle_type_hwj.flush()
                            file_handle_type_hwj.close()
                    #end to find skgf\rhrj300339
                except:
                    pass
            except:
                print(stock_codes + "excpetion")


    finally:
        pass

def getZhangtingZhangfu(stockCode):
    ret = int(10)
    if stockCode.startswith("1") or stockCode.startswith("68") or stockCode.startswith("3"):
        ret = int(20)
    elif stockCode.startswith("4") or stockCode.startswith("8") or stockCode.startswith("9"):
        ret = int(30)
    return ret

def getDiffPortion(p1,p2):
    return float((p2-p1)/p1 *100)

def iszhangting(stockCode,closePortion):
    ret = False
    zhangtingZhangfu = getZhangtingZhangfu(stockCode)
    if closePortion +   ERR_1E6 >= zhangtingZhangfu:
        ret = True
    return ret


def iszhangtingWithZhangfu(zhangtingZhangfu,closePortion):
    ret = False
    if closePortion +   ERR_1E6 >= zhangtingZhangfu:
        ret = True
    return ret


def find_custom_pattern(file_path):
    finder = PatternFinder()
    return finder.find_custom_pattern(file_path)

if __name__ == '__main__':
    #2021-11-12
    # df = pd.read_excel("C:\\gupiao\\bak\\c操作计划\\交易记录.xlsx", sheet_name='净值NEW',converters={'日期':pd.to_datetime})
    # print(df)
    # days=77
    # dayList=[]
    # for i in range(days):
    #     dayList.append(i)
    # plt.rcParams['font.sans-serif']=['SimHei']
    # plt.plot(dayList,df['净值'])
    # plt.xlabel('天数')
    # plt.ylabel('净值')
    # plt.show()
    # pass

    # print("begin")
    # dateStr = 20251205
    # path = "C:\\gupiaoE\\gupiao\\qianFuQuan\\everyDayPrice\\"
    # #dateStr = 20240709 #600611dzjt
    # #dateStr = 20250811 #688256hwj
    # #dateStr = 20250902 #600376skgf
    # #dateStr = 20250717? #603516czkj
    # #path = "C:\\gupiaoE\\gupiao\\qianFuQuan\\everyDayPrice\\tmp\\"

    # getType26(path, dateStr)

    # Custom scan for the pattern requested, using local 002583.txt if present
    custom_file = Path("002583.txt")
    if custom_file.exists():
        print("custom pattern scan on", custom_file)
        matches = find_custom_pattern(custom_file)
        print("found", len(matches), "pattern(s)")
        for m in matches:
            print(m)
    else:
        print("002583.txt not found, skip custom pattern scan")

    print("end")
