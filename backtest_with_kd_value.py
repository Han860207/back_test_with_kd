#!/usr/bin/env python
# coding: utf-8

# In[13]:


import pandas as pd
import requests
import time

class Stock :
    def __init__(self,start,end, stock_id ):
        self.start = start
        self.end = end
        self.stock_id = stock_id
## 計算KD值與買進賣出的操作方法均包含在Skills內部
class Skills :
    def minmaxlist(self,df):
        a = []
        b = []
        i = 0
        while i < len(df):
            a.append(min(df['Low'][i:i+9]))
            b.append(max(df['High'][i:i+9]))
            i+=1
        return a , b
    def rsv(self,df):
        return (df['Close']-df['min'])*100/(df['max']-df['min']) 
    def kd(self,df):
        n = len(df)-1
        K = [50] *len(df) 
        D = [50] *len(df)
        while n > 0 :
            K[n-1] = (2/3)*K[n] + (1/3)*df['RSV'][n-1]
            D[n-1] = (2/3)*D[n] + (1/3)*K[n-1]
            n-=1
        return K,D
    ### 將黃金交叉後的三天內都設定成買進訊號
    def gold(self,df):
        i = len(df)-1
        gold=[0] * len(df)
        while i > 0:
            if df['K'][i] < df['D'][i] and df['K'][i-1] >df['D'][i-1]:
                gold[i-1] = 1
                gold[i-2] = 1
                gold[i-3] = 1
            i-=1
        return gold
    ### 將死亡交叉後的三天內都設定成賣出訊號
    def dead(self,df):
        i = len(df)-1
        dead=[0] * len(df)
        while i > 0:
            if df['K'][i] > df['D'][i] and df['K'][i-1] <df['D'][i-1]:
                dead[i-1] = 1
                dead[i-2] = 1
                dead[i-3] = 1
            i-=1
        return dead
    ### 當 原K值 < 20 且 剛成為黃金交叉時進行買進
    def buy(self,df):
        i = len(df)-1
        buy = [0]*len(df)
        while i >=0 :
            if df['K'][i]< 20 and df['gold'][i] == 1:
                buy[i] = 1
            i-=1
        return buy
    ### 當 原K值 >80 且剛成為死亡交叉時進行賣出
    def sell(self,df):
        i = len(df)-1
        sell = [0]*len(df)
        while i >=0 :
            if df['K'][i] > 80 and df['dead'][i] == 1 :
                sell[i] = 1
            i-=1
        return sell
    ### 若手上已經持有卻仍舊有買進訊號時，不進行加倉，同理，若手上無該股卻有賣出訊號時不進行放空
    def mani(self,df):
        hold_token = 0
        i = len(df)-1
        buy_price=[]
        sell_price=[]
        buy_date=[]
        sell_date=[]
        while i >=0:
            if hold_token == 0 and df['buy'][i] == 1:
                hold_token =1
                buy_price.append(df['Close'][i])
                buy_date.append(df['Date'][i])
            elif hold_token == 1 and df['sell'][i] == 1:
                hold_token = 0
                sell_price.append(df['Close'][i])
                sell_date.append(df['Date'][i])
            i-=1
        return buy_price ,sell_price,buy_date,sell_date
    ### 統整報酬率
    def return_rate(self,buy_price,sell_price):
        holding=0
        result = []
        if len(buy_price) != len(sell_price):
            holding= buy_price.pop()
        for i in range(len(buy_price)):
            result.append(100*(sell_price[i]-buy_price[i])/buy_price[i])
        return holding ,result
### 鉅亨網的日期是以數字而非常用的yyyy-mm-dd ，故透過function進行轉換
def int_to_date(date) :
    temp = time.localtime(date)
    timeString = time.strftime("%Y-%m-%d %H:%M:%S", temp)
    return timeString.split(' ')[0]
def date_to_int(stamp) :
    struct = time.strptime(stamp ,'%Y-%m-%d %H:%M:%S')
    new_stamp = int(time.mktime(struct))
    return new_stamp
def get_data():
    stock_id = input()
    start_date = input('Please input start date as type yyyy-mm-dd') +' 00:00:00'
    end_date = input('Please input end date as type yyyy-mm-dd') +' 23:59:59'
    stock = Stock(start = start_date, end = end_date, stock_id=stock_id)
    ### 將日期轉成int以用來查詢
    int_start_date = date_to_int(stock.start)
    int_end_date = date_to_int(stock.end)
    url ='https://ws.api.cnyes.com/ws/api/v1/charting/history?resolution=D&symbol=TWS:%s:STOCK&from=%s&to=%s&quote=1'%(stock_id,int_end_date,int_start_date)                                                                                                               
    res = requests.get(url)
    data  = res.json()['data']
    ### 回傳 日期、最高價、最低價、開盤價與收盤價 的 dataframe
    timelist ,open_list ,close_list , high_list , low_list = [int_to_date(i) for i in data['t']],data['o'],data['c'],data['h'],data['l']
    temp_dict = {'Date':timelist,'Open':open_list,'Close':close_list,'High':high_list,'Low':low_list}
    df = pd.DataFrame(data =temp_dict)
    return df
### 將原本的dataframe 加工計算出所需的KD值與買賣訊號
def get_new_df(df):
    skills = Skills()
    df['min'],df['max']  = skills.minmaxlist(df)
    df['RSV'] = skills.rsv(df)
    df['K'],df['D'] = skills.kd(df)
    df['gold'] = skills.gold(df)
    df['dead'] = skills.dead(df)
    df['buy'] = skills.buy(df)
    df['sell'] = skills.sell(df)
    return df
def main():
    skills = Skills()
    df = get_data()
    new_df = get_new_df(df)
    buy_price ,sell_price,buy_date,sell_date = skills.mani(new_df)
    holding ,result = skills.return_rate(buy_price=buy_price,sell_price=sell_price)
    for i in range(len(buy_price)):
        print(buy_date[i],end= ' ')
        print('位於',buy_price[i],'買進' )
        print(sell_date[i] , end = ' ')
        print('位於',sell_price[i],'賣出' , '報酬率為 :', '{:.3f}'.format(result[i]),'%')
    money = 100
    for i in result :
        money = money + money *(i/100)
    print('總報酬率 : ','{:3f}'.format(money-100),'%')
    if holding != 0:
        print('目前持有價位:%s,買於:%s'%(holding,buy_date[-1]))
main()

