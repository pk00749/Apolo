#encoding:utf-8

from sqlalchemy import Table,Column,Integer,DECIMAL,String,Date,MetaData,ForeignKey
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy import exc
from config import Config
from table_creator import Table_creator
import datetime
import tushare as ts
import pandas as pd

class Db_connector:
    '''
    This class is used to connect to mysql server and 
    select, insert, delete data 
    '''
    def __init__(self):
        #get the user configuration of db info:
        user_config = Config()
        user_db_param = user_config.get_config_db_info()
        self.db_host = user_db_param['host']
        self.db_port = user_db_param['port']
        self.db_user = user_db_param['user']
        self.db_pass = user_db_param['pass']
        
        
        #create db if not exists
        self.str_db_k_data = 'db_k_data' #k_data database
        self.create_db(self.str_db_k_data)
        
        #stock classification database
        self.str_db_stock_classification = 'db_stock_class' #stock classification database
        self.create_db(self.str_db_stock_classification)
           
        #create table
        self.table_creator = Table_creator()
        
    def create_db(self,db_name):
        #connect engine
        engine = self.create_db_engine() #the main engin
        #create db if not exists
        engine.execute("create database if not exists %s"%(db_name)) #create database
        print('Create db: '+db_name+' if not exist')
        engine.dispose() #stop all the engine connection
        
    def create_db_engine(self,db_name=''):
        #connect to mysql server
        engine=create_engine('mysql+pymysql://'+self.db_user\
                                 +':'+self.db_pass\
                                 +'@'+self.db_host\
                                 +':'+self.db_port\
                                 +'/'+db_name\
                                 +'?charset=utf8') #use mysqlconnector to connect db
        print("engine:"+db_name+' OK')
        return engine
        
    def insert_to_db_no_duplicate(self,df,table_name,engine):
        
        try:
            df.to_sql(name=table_name,con=engine,if_exists='append',index=False)
        except exc.IntegrityError:
            print("Data duplicated, try to insert one by one")
            #df is a dataframe
            num_rows =  len(df)
            #iterate one row at a time
            for i in range(num_rows):
                try:
                    #try inserting the row
                    df[i:i+1].to_sql(name=table_name,con=engine,if_exists='append',index=False)
                except exc.IntegrityError:
                    #ignore duplicates
                    pass
        
    def update_db_k_data(self,stock_code):
        
        #create k_data db engine
        engine = self.create_db_engine(self.str_db_k_data)
        
        #set the table name
        table_name = 'k_data_'+stock_code
        table_k_table = self.table_creator.get_table_k_data(table_name) 
        table_k_table.create(engine,checkfirst=True)   #create table
        print("Create k_data table:%s ok!"%(table_name))
        
        #get the start date 
        result = engine.execute("select max(%s) from %s"%(table_k_table.c.date,table_name))
        last_date = result.fetchone()[0]
        if last_date==None:
            start_date = datetime.date(2000,1,1) #default start date
        else:
            start_date=last_date+datetime.timedelta(days=1)
            
        #get the end date
        end_date = datetime.date.today()
        
        if(start_date<end_date):
            str_start_date = start_date.strftime("%Y-%m-%d")
            str_end_date = end_date.strftime("%Y-%m-%d")
        else:
            str_end_date = end_date.strftime("%Y-%m-%d")
            str_start_date = str_end_date
        print('start date:'+str_start_date+' ; end date:'+str_end_date)
        #get the k_data from Tushare
        k_data= ts.get_k_data(code=stock_code,start=str_start_date,end=str_end_date)
        print(k_data)
        
        #insert data to database
        k_data.to_sql(table_name,engine,if_exists='append',index=False)
        
        #close the engine pool
        engine.dispose()
        
    def update_stock_list(self):
        
        ##update sz50 list:
        #engine = self.create_db_engine(self.str_db_stock_classification)
        #table_sz50_list = self.table_creator.get_table_sz50_list()
        #table_sz50_list.create(engine,checkfirst=True)
        #print("Create %s list table ok!"%table_sz50_list.name)
        ##get the sz50 list from Tushare
        #sz50_list = ts.get_sz50s()
        ##insert sz50 list 
        #sz50_list.to_sql(table_sz50_list.name,engine,if_exists='append',index=False)
        #print("Insert %s data ok!"%table_sz50_list.name)
        
        #update hs300(沪深300) list:
        table_hs300_list = self.table_creator.get_table_hs300_list()
        table_hs300_list.create(engine,checkfirst=True)
        print("Create %s list table ok!"%table_hs300_list.name)
        #get the list from Tushare
        hs300_list = ts.get_hs300s()
        print('get %s data ok!'%table_hs300_list.name)
        #insert list 
        self.insert_to_db_no_duplicate(hs300_list,table_hs300_list.name,engine)
        print("Insert %s data ok!"%table_hs300_list.name)
        
        
        ##update zz500(中证500) list:
        #table_zz500_list = self.table_creator.get_table_zz500_list()
        #table_zz500_list.create(engine,checkfirst=True)
        #print("Create %s list table ok!"%table_zz500_list.name)
        ##get the list from Tushare
        #zz500_list = ts.get_zz500s()
        #print('get %s data ok!'%table_zz500_list.name)
        ##insert list 
        #self.insert_to_db_no_duplicate(zz500_list,table_zz500_list.name,engine)
        #print("Insert %s data ok!"%table_zz500_list.name)
        
        #close the engine pool
        engine.dispose()
    
if __name__=='__main__':
    test=Db_connector()
    #test.update_db_k_data('000002')
    test.update_stock_list()
    print("ok")
    