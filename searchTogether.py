# -*- coding: utf-8 -*-
"""
Created on Sat Jun  5 15:53:20 2021

@author: xbch

#基于《三线开花》1250策略，三线并进
"""

import baostock as bs
import numpy as np
import pandas as pd
import re,urllib
import os
import time

def getPrice(string):
    #### 获取最新价####

    snum=int(string)
    if(snum<301000):
        code='sz'+string
    else:
        code='sh'+string
    try:
        res = urllib.request.urlopen('http://hq.sinajs.cn/list=%s'%code).read()
    #    print(res.decode(encoding='gbk'))
        res=res.decode(encoding='gbk').split('=')[1]
        res=float(res.split(',')[3])
#        print(res)
    except:
        print('The price of'+string+' is not found.')
        return 0.0
    return res

def build_dict():
    path='./dictdata/'
    dirs=os.listdir(path)
    dict_={}
    for file in dirs:
        f=open(path+file,'r')
        data=f.readlines()
        #建立字典关键词
        keylist=data[0].strip().split('\t')
        #建立字典
        for i in range(1,len(data)-1):
            datalist=data[i].strip().split('\t')
            name=datalist[0]
            dict_[name]={}
            for j in range(1,3):
                dict_[name][keylist[j]]=datalist[j]
#            dict_[name]['现价']=str(getPrice(name))
        f.close()
    return dict_
#def ave(la,a,maxl):
#    lb=[]
#    for i in range(maxl):
#        lb.append(np.mean(la[-1-a+1-i:-1-i]))
#    return lb
def ave(la,a,maxl):
    lb=[]
    length=len(la)
    for i in range(maxl):
        lb.append(np.mean(la[length-a-i:length-i]))
    return lb
def judge(string,i):
    
    step0=180
    s=True
    step=i#检验周期跨度
    maxl=2*step+step0#最长统计均线：三倍周期，以减少计算量
    
    snum=int(string)
    if(snum<301000):
        code='sz.'+string
    else:
        code='sh.'+string
    try:
        #get history_data
        date=time.strftime("%Y-%m-%d", time.localtime()) 
        rs = bs.query_history_k_data_plus(code,
            "date,close,preclose,amount",frequency="d", adjustflag="2")
        data_list = []
        while (rs.error_code == '0') & rs.next():
             # 获取一条记录，将记录合并在一起
             data_list.append(rs.get_row_data())
        result = pd.DataFrame(data_list, columns=rs.fields)
        close_list=list(map(float,result['close']))
#        print(close_list)
        amount_list=list(map(float,result['amount']))
        if(len(close_list)<300):return False#不考虑上市300天以内的股票
        #
        close_1=ave(close_list,1,maxl)
        close_20=ave(close_list,20,maxl)
        close_120=ave(close_list,120,maxl)
        close_250=ave(close_list,250,maxl)
#        print(close_20)
        amount_1=ave(amount_list,1,maxl)
        
        now_20_120=close_20[0]-close_120[0]
        now_120_250=close_120[0]-close_250[0]
        
        old_20_120=close_20[step-1]-close_120[step-1]
        old_120_250=close_120[step-1]-close_250[step-1]
        
        f_over=0.05
        
#        if1=(now_20_120>(1-f_over)*old_20_120 ) and (old_20_120>(1-f_over)*now_20_120)
#        if2=(now_120_250>(1-f_over)*old_120_250 ) and (old_120_250>(1-f_over)*now_120_250)
        
        factor=(now_20_120 * old_120_250)/(now_120_250 * old_20_120)
        if(factor>(1-f_over) and factor<(1+f_over) and now_20_120>0 and now_120_250>0):s=False
        
        if(s):return False
        
        for i in range(step0):
            if(close_20[i]>close_120[i] and close_20[i+1]<close_120[i+1]):
                for j in range(step):
                    if(close_20[i+j+1]>close_250[i+j+1] and close_20[i+j+2]<close_250[i+j+2]):
                        return True
        
        
        return False
    except Exception as e:
        #print(e)
        return False
def find(dict_):
    step=int(input('please input the step by int:'))
    f=open('found_by_Together.txt','w')
    sum_hy={}#统计行业次数
    for key in dict_.keys():
        r=judge(key,step)
        if(r==True):
            hy=dict_[key]['细分行业']
            if(hy in sum_hy.keys()):
                sum_hy[hy]=sum_hy[hy]+1
            else:
                sum_hy[hy]=1
            print(key+'  '+dict_[key]['名称']+'  '+hy+str(sum_hy[hy]))
            f.write(key+'  '+dict_[key]['名称']+'  '+hy+str(sum_hy[hy])+'\n')
#            continue
    return
if __name__=='__main__':
    print('building dict')
    dict_=build_dict()
    lg = bs.login(user_id="anonymous", password="123456")
    find(dict_)
    bs.logout()