import tushare as ts
import os
import pandas as pd
import numpy as np
import datetime as dt

import pymysql
from lib.connect_database import connect_server
from lib.connect_database import connect_engine

conn, cur = connect_server()

print('version: ' + ts.__version__)
now = dt.datetime.now()
DATA_DIR = 'E:\\Apolo\\raw_data'
STOCK_BASICS_DIR = os.path.join(DATA_DIR, 'stock_basics')
REPORT_DATA_DIR = os.path.join(DATA_DIR, 'report_data')
PROFIT_DATA_DIR = os.path.join(DATA_DIR, 'profit_data')
INDUSTRY_CLASSIFIED_DIR = os.path.join(DATA_DIR, 'industry_classified')
HISTORY_DATA_DIR = os.path.join(DATA_DIR, 'history_data')
STOCK_ID = os.path.join(DATA_DIR, 'stock_id')


# 获取沪深上市公司基本情况
def get_stock_basics():
    # if folder doest exists, then create.
    # todo: check if the data is the latest, no need to insert, otherwise insert or update.
    # todo: Exception
    if os.path.exists(STOCK_BASICS_DIR) is False:
        os.makedirs(STOCK_BASICS_DIR)
    df = ts.get_stock_basics()
    df['createDate'] = '{yyyy}{mm}{dd}'.format(yyyy=str(now.year),
                                               mm=str(now.strftime('%m')),
                                               dd=str(now.strftime('%d')))
    df.to_csv(os.path.join(STOCK_BASICS_DIR, '%s%s%s.csv' % (str(now.year),
                                                             str(now.strftime('%m')),
                                                             str(now.strftime('%d')))))
    engine = connect_engine()
    df.to_sql('stock_basics', engine, if_exists='append', index=True)  # append, to avoid modifying field type.
    print('Stock basics downloaded.')


# 获取某年某季度的业绩报表数据
def get_report_data(year, quarter):
    # todo: to check if the result exisit, don't download.
    if os.path.exists(REPORT_DATA_DIR) is False:
        os.makedirs(REPORT_DATA_DIR)
    df = ts.get_report_data(year, quarter)
    df['report_y_q'] = int('{yyyy}{q}'.format(yyyy=year, q=quarter))
    df = df.iloc[:, 0: 12]
    df.to_csv(os.path.join(REPORT_DATA_DIR, '%s_%s.csv' % (str(year), str(quarter))))
    engine = connect_engine()
    pd.DataFrame.to_sql(df, 'report_data', engine, if_exists='append', index=False)

    print('\n%s year %s quarter report data report downloaded.' % (str(year), str(quarter)))


def get_report_data_range(from_year, to_year):
    for y in np.arange(from_year, to_year+1):
        for q in np.arange(1, 4+1):
            get_report_data(y, q)


# 获取某年某季度的盈利能力数据
def get_profit_data(year, quarter):
    if os.path.exists(PROFIT_DATA_DIR) is False:
        os.makedirs(PROFIT_DATA_DIR)
    df = ts.get_profit_data(year, quarter)
    df['report_y_q'] = int('{yyyy}{q}'.format(yyyy=year, q=quarter))
    df.to_csv(os.path.join(PROFIT_DATA_DIR, '%s_%s.csv' % (str(year), str(quarter))))
    engine = connect_engine()
    pd.DataFrame.to_sql(df, 'profit_data', engine, if_exists='append', index=False)

    print('\n%s year %s quarter profit data report downloaded.' % (str(year), str(quarter)))


def get_profit_data_range(from_year, to_year):
    for y in np.arange(from_year, to_year+1):
        for q in np.arange(1, 4+1):
            get_profit_data(y, q)


# 按行业分类股票代号列表
def get_industry_classified():
    if os.path.exists(INDUSTRY_CLASSIFIED_DIR) is False:
        os.makedirs(INDUSTRY_CLASSIFIED_DIR)
    df = ts.get_industry_classified()
    df.to_csv(os.path.join(INDUSTRY_CLASSIFIED_DIR, '%s%s%s.csv' % (str(now.year),
                                                                    str(now.strftime('%m')),
                                                                    str(now.strftime('%d')))))
    df['createDate'] = '{yyyy}{mm}{dd}'.format(yyyy=str(now.year),
                                               mm=str(now.strftime('%m')),
                                               dd=str(now.strftime('%d')))
    engine = connect_engine()
    df.to_sql('industry_classified', engine, if_exists='append', index=False)
    print('Stock basics - industry classified downloaded.')


def query_stock_code(stock_code, to_year=2017, total_year=5):
    cur.execute("select count(code) as b from stock_code where code=%s", stock_code)
    exist = cur.fetchall()
    if exist[0][0]:
        print('The stock code exist already.')
    else:
        print('The stock code do NOT exist. Start to download data...')
        cur.execute("insert into stock_code (code) values (%s)", stock_code)
        get_history_data(str(stock_code), to_year, total_year)

    conn.commit()
    conn.close()


def get_history_data(code, to_year, total_year):
    PATH = os.path.join(HISTORY_DATA_DIR, code)
    if os.path.exists(PATH) is False:
        os.makedirs(PATH)

    engine = connect_engine()

    for y in np.arange(to_year-total_year, to_year, 1):
        print('Start to download {yyyy}'.format(yyyy=y))
        start = '{yyyy}-01-01'.format(yyyy=y)
        end = '{yyyy}-12-31'.format(yyyy=y)
        df = ts.get_k_data(code, autype='qfq', start=start, end=end)
        df.to_csv(os.path.join(PATH, '{yyyy}.csv'.format(yyyy=y)))
        df.to_sql('history_data', engine, if_exists='append', index=False)
        print('completed.')

    print('Start to download {yyyy}'.format(yyyy=to_year))
    start = '{yyyy}-01-01'.format(yyyy=to_year)
    end = str(dt.date.today())
    df = ts.get_k_data(code, autype='qfq', start=start, end=end)
    df.to_csv(os.path.join(PATH, '{f}_{t}.csv'.format(f=to_year, t=end)))
    df.to_sql('history_data', engine, if_exists='append', index=False)
    print('completed.')


def get_sse50(year, quarter):
    if os.path.exists('./data/sse50') is False:
        os.makedirs('./data/sse50')
    df = ts.get_sz50s()
    df.to_csv('./data/sse50/sse50_%s_%s.csv' % (str(year), str(quarter)))
    print('\n%s year %s quarter sse50 downloaded.' % (str(year), str(quarter)))


def filter_stock_list_sse50(date):
    sse50 = pd.read_csv('./data/sse50/2017_2.csv', encoding='gbk')
    stock_list = pd.read_csv('./data/stock_basics/20170601.csv', encoding='gbk')
    data = pd.merge(sse50, stock_list, on=['code'], how='left')
    data = data[(data['timeToMarket'] < date)]
    data = data[['code', 'name_x', 'area', 'industry', 'timeToMarket']]
    data = pd.DataFrame(data)
    data = data.fillna({'area': 'miss', 'industry': 'miss'})
    data.to_csv('./data/sse50/2017_2_Filtered.csv')


def stock_master(date):
    sm = pd.DataFrame(pd.read_csv('./data/stock_basics/20170525.csv', encoding='gbk'))
    sm = sm[(sm['timeToMarket'] < date)]
    sm = sm.sort_values(by=['code'], ascending=True)
    print(sm.head(10))
    print(type(sm['code']))
    print(sm['code'])


if __name__ == '__main__':
    # get_sse50(2017, 2)
    # filter_stock_list_sse50(20120101)
    # get_profit_data(2013, 1)
    # get_profit_data_range(2014,2017)
    # get_report_data(2013,1)
    # get_report_data_range(2013, 2017)
    # get_industry_classified()
    # get_stock_basics()
    # df=ts.get_k_data('600000')
    # print(df)
    query_stock_code(600000, 2017)
    # cur.execute("insert into stock_code (code) values (600000)")
    # get_history_data('600000', 2017)
    # conn, cur = connect_server()
    # cur.execute("select * from york")
    # result = cur.fetchall()
    # print(result)
    # conn,cur = connect_server()
    # cur.execute("select * from york")
    # result = cur.fetchall()
    # print(result)


