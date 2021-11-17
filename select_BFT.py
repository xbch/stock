# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 20:41:01 2021

@author: xbch
"""
import re,urllib
import os
import baostock as bs
import pandas as pd

###
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
        print(string)
        return 0.0
    return res

    
def build_dict():
    #创建上市公司名录字典
    path='./dictdata/'#存放获取的主板名录
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
            dict_[name]['现价']=str(getPrice(name))#记录当前价格
        f.close()
    return dict_


def getfiles(string):
    #获取资产负债表，利润表和现金流量表
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
    roe= bs.query_profit_data(code="sh.600000", year=2017, quarter=2)
    #### 打印结果集 ####
    result_list = []
    roe_list=[]
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        result_list.append(rs.get_row_data())
    while (roe.error_code == '0') & roe.next():
        # 获取一条记录，将记录合并在一起
        roe_list.append(roe.get_row_data())
    R_pe = pd.DataFrame(result_list, columns=rs.fields)
    R_roe = pd.DataFrame(roe_list, columns=roe.fields)
    #### 结果集输出到csv文件 ####
    R_pe.to_csv("./%s/%sPE.csv"%(folder,code), encoding="gbk", index=False)
    R_roe.to_csv("./%s/%sROE.csv"%(folder,code), encoding="gbk", index=False)
    return
##
def select_bft(dict_):
    
# =============================================================================
#     #主要参数
    y_dist=5#参考年限
    current_year=2020#AB股市值最低限
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
                    if(gp>gp_dist and np>np_dist and roe>roe_dist):#毛利率、净利率和净资产收益率均高于限值
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

#

###主程序###
#
if __name__=='__main__':
    dict_=build_dict()
#    print(dict_['300206'])
    yn=input('是否刷新表单数据？Y/N:')
    if yn=='Y' or yn=='y':
        getfiles('lrb')
        getfiles('zcfzb')
        getfiles('xjllb')


    lg = bs.login(user_id="anonymous", password="123456")
#    select_total(dict_)
    select_bft(dict_)
#    gethistory('300206','temp')
    bs.logout()