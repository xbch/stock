# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 19:49:46 2021

@author: Administrator
"""
import re,urllib
import xlwt
from bs4 import BeautifulSoup
from time import sleep
import os
import baostock as bs
import pandas as pd
#import time
import datetime
#import urllib

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
            for j in range(1,len(datalist)):
                dict_[name][keylist[j]]=datalist[j]
            dict_[name]['现价']=str(getPrice(name))
        f.close()
    return dict_
def getfiles(string):
    prelist=[0,300,600,601,603]
    for pre in prelist:
        for count in range(int(pre*1000+1),int(pre*1000+1000)):
            url='http://quotes.money.163.com/service/%s_'%(string)+str(count).zfill(6)+'.html'
            while True:
                try:
                    content = urllib.request.urlopen(url,timeout=2).read()
                    with open('./%s/'%(string)+str(count).zfill(6)+'%s.csv'%(string),'wb') as f:
                        f.write(content)
                        break
                except Exception as e:
                    if str(e)=='HTTP Error 404: Not Found':
                        break
                    else:
                        print(string+str(count).zfill(6)+':'+str(e))
                        break
#
def gethistory(string,folder='history'):
    #### 登陆系统 ####
#    lg = bs.login(user_id="anonymous", password="123456")
    #### 获取沪深A股估值指标(日频)数据 ####
    # peTTM    动态市盈率
    # psTTM    市销率
    # pcfNcfTTM    市现率
    # pbMRQ    市净率
    snum=int(string)
    if(snum<301000):
        code='sz.'+string
    else:
        code='sh.'+string
    rs = bs.query_history_k_data(code,
        "date,close,peTTM,pbMRQ,psTTM,pcfNcfTTM", 
        frequency="d", adjustflag="3")
    #### 打印结果集 ####
    result_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        result_list.append(rs.get_row_data())
    result = pd.DataFrame(result_list, columns=rs.fields)
    
    #### 结果集输出到csv文件 ####
    result.to_csv("./%s/%s.csv"%(folder,code), encoding="gbk", index=False)
    return

def select_total(dict_):
    
# =============================================================================
#     #主要参数
    y_dist=5#参考年限
    svalue_dist=10.0#AB股市值最低限
    yylr_dist=0.0#判断营业利润最低值
    yylr_rate_dist=1.0#营业利润增长率最低值，1.0代表0.0%
    cf_dist=0.0#现金流最低值
    roe_dist=0.10#净资产收益率最低值
    cwgg_dist=4.0#财务杠杆比例最高限
    ycxzc_dist=0.03#一次性支出占营业利润的最高百分比
    
# =============================================================================
    
    fwrite=open('result.txt','w')
    fwrite.write('代码\t名称\t现价\t行业\n')
    for key in dict_.keys():
        #0、判断市值是否高于某值
        try:
            if(float(dict_[key]['AB股总市值'].strip('亿'))>svalue_dist):
                dict_[key]['测试通过']=1
            else:
                dict_[key]['测试通过']=0
                print(key,dict_[key]['AB股总市值'])
                continue
            cwgg=100.0/(100.0-float(dict_[key]['资产负债率%']))
            if(cwgg<cwgg_dist):
                dict_[key]['测试通过']=1
            else:
                dict_[key]['测试通过']=0
                print(key,'财务杠杆',cwgg)
                continue
        except Exception as e:
#            print(e)
            dict_[key]['测试通过']=0
            continue
        #1、判断是否一直获取营业利润
        #利润表
#        print('step 1')
        try:
            f=open('./lrb/'+str(key).zfill(6)+'lrb.csv','r')
            lines=f.readlines()
#            yearlist=[]
#            yylrlist=[]
            num_y=0
            ylist=lines[0].split(',')
            yylrlist=lines[33].split(',')#营业利润
            ycxzclist=lines[35].split(',')#一次性支出
            tmyylr=0.0
            if(len(ylist)<(y_dist*4-3)):#统计年限过短，pass
                dict_[key]['测试通过']=0 
                continue
#            print(ylist)
            for i in range(1,len(ylist)):
                year,month,day=re.split('[/-]',ylist[i])#.split('/')
#                print(month)
                if(int(month)>9):
                    yylr=float(yylrlist[i])
                    ycxzc=float(ycxzclist[i])
                    #判断一次性支出是否较多
                    if(ycxzc>ycxzc_dist*yylr):
                        print(key,'ycxzc',ycxzc)
                        dict_[key]['测试通过']=0
                        break
                    if(yylr>yylr_dist):
                        num_y=num_y+1
                        if(num_y==1):
                            tmyylr=yylr
                            continue
                        #4、判断营业利润是否一直增长，未要求增长率
                        if(tmyylr>yylr_rate_dist*yylr):
                            tmyylr=yylr
                        else:
                            dict_[key]['测试通过']=0
                            break
                        if(num_y>=y_dist):
                            break
                    else:
#                        print(year,lrlist[i])
                        dict_[key]['测试通过']=0
                        break
        except Exception as e:
#            print(e)
            dict_[key]['测试通过']=0
            continue
        if(dict_[key]['测试通过']==0):
            continue
        #2、判断是否一直产生现金流
        #现金流量表
        try:
            f=open('./xjllb/'+str(key).zfill(6)+'xjllb.csv','r')
            lines=f.readlines()
#            yearlist=[]
#            yylrlist=[]
            num_y=0
            ylist=lines[0].split(',')
            cflist=lines[89].split(',')#现金流
            jlrlist=lines[57].split(',')#净利润
            for i in range(1,len(ylist)):
                year,month,day=re.split('[/-]',ylist[i])#.split('/')
                if(int(month)>9):
                    if(float(cflist[i])>cf_dist):
                        num_y=num_y+1
                        if(num_y>=y_dist):
                            break
                    else:
#                        print(key,year,'cf',cflist[i])
                        dict_[key]['测试通过']=0
                        break
        except Exception as e:
            print(e)
            dict_[key]['测试通过']=0
            continue
        if(dict_[key]['测试通过']==0):
            continue
        #资产负债表
        try:
            f=open('./zcfzb/'+str(key).zfill(6)+'zcfzb.csv','r')
            lines=f.readlines()
#            yearlist=[]
#            yylrlist=[]
            num_y=0
            ylist=lines[0].split(',')
            syzqylist=lines[107].split(',')#所有者权益
            for i in range(1,len(ylist)):
                year,month,day=re.split('[/-]',ylist[i])#.split('/')
                if(int(month)>9):
                    roe=float(jlrlist[i])/float(syzqylist[i])
                    #3、净资产收益率5年内不低于10%
                    if(roe>roe_dist):
                        num_y=num_y+1
                        if(num_y>=y_dist):
                            break
                    else:
                        print(key,year,'zcfzb',str(roe),jlrlist[i])
                        dict_[key]['测试通过']=0
                        break
        except Exception as e:
            print(e)
            dict_[key]['测试通过']=0
            continue
        if(dict_[key]['测试通过']==1):
            fwrite.write(str(key).zfill(6)+'\t'+dict_[key]['名称']+'\t'+dict_[key]['现价']+'\t'+dict_[key]['细分行业']+'\n')
            gethistory(key)
    #
    fwrite.close()
    return

def select_bft(dict_,cyear=2021):
    
# =============================================================================
#     #主要参数
    y_dist=5#参考年限
    current_year=cyear#当前年
    gp_dist=0.60#判断gpMargin毛利率最低值
    np_dist=0.30#npMargin净利率最低值
#    cf_dist=0.0#现金流最低值
    roe_dist=0.15#净资产收益率最低值
#    cwgg_dist=4.0#财务杠杆比例最高限
#    ycxzc_dist=0.03#一次性支出占营业利润的最高百分比
    
# =============================================================================
    
    fwrite=open('result_bft.txt','w')
    fwrite.write('代码\t名称\t现价\t行业\n')
#    lg = bs.login(user_id="anonymous", password="123456")
    
    for key in dict_.keys():
        #0、判断市值是否高于某值
        try:
            dict_[key]['bft']=0
            snum=int(key)
            if(snum<301000):
                code='sz.'+key
            else:
                code='sh.'+key
            for i in range(current_year-y_dist,current_year):
                rs_profit = bs.query_profit_data(code, year=i, quarter=4)
    #            data=rs_profit.get_row_data()
                if(rs_profit.error_code == '0') & rs_profit.next():
                    result_profit = pd.DataFrame([rs_profit.get_row_data()], columns=rs_profit.fields)
                    gp=float(result_profit['gpMargin'][0])
                    np=float(result_profit['npMargin'][0])
                    roe=float(result_profit['roeAvg'][0])
                    if(gp>gp_dist and np>np_dist and roe>roe_dist):
                        dict_[key]['btf']=1
    #                    print(i,gp)
                    else:
                        dict_[key]['btf']=0
                        break
                else:
                    dict_[key]['btf']=0
                    break
            if(dict_[key]['btf']==1):
                print('get ',key)
                gethistory(key,'bft')
                fwrite.write(str(key).zfill(6)+'\t'+dict_[key]['名称']+'\t'+dict_[key]['现价']+'\t'+dict_[key]['细分行业']+'\n')
        except Exception as e:
            print(key,e)
            continue
    fwrite.close()
    return

###主程序###
#
if __name__=='__main__':
    print('building dict')
    dict_=build_dict()
#    print(dict_['300206'])
    yn=input('是否刷新表单数据？Y/N:')
    if yn=='Y' or yn=='y':
        cyear=input('current year is:')
        getfiles('lrb')
        getfiles('zcfzb')
        getfiles('xjllb')
    #
#    f=open('./lrb/300206lrb.csv','r')
#    lines=f.readlines()
#    print(lines[0].split('\t'))
    lg = bs.login(user_id="anonymous", password="123456")
    select_total(dict_)
    select_bft(dict_,int(cyear))
#    gethistory('300206','temp')
    bs.logout()