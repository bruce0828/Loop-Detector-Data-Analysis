#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import calendar
import json
import time


# ## Option 1: Using API
# Data source for 30 days trial: [AerisWeather API](https://www.aerisweather.com/wizard/api/options?endpoint=observations-archive&action=id)

# In[ ]:


CLIENT_ID = '61UfYPJSt2aAJo2YyStp1'
CLIENT_SECRET = 'FnJ8fWgKdXs0vEri4oaiAqVz1oqWs6QhlhiPfgwi'
location = 'seattle,washington'
date = '04/20/2020'
url = 'https://api.aerisapi.com/observations/archive/{}?'.format(location)
params = {'from':'2017-02-27 5:00 PM',
          'to':'2017-02-29 5:00 PM',
          'format':'json',
          'filter':'allstations',
          'limit':1,
#           'fields':'periods.ob.weather,periods.ob.dateTimeISO',
          'client_id':CLIENT_ID,
          'client_secret':CLIENT_SECRET}

r = requests.get(url,params=params)
data = json.loads(r.text)



# ## Option 2: Free data

# In[2]:


def get_dates(sdate,edate):
    """ Get days between sdate and edate
    Parameters
    ----------
    sdate: 'YYYY-mm-dd'
    edate: 'YYYY-mm-dd'
    
    Return
    ------
    Days list
    """
    if edate == 'today':
        edatetime = datetime.datetime.today().date() - datetime.timedelta(days=1)
    else:
        edatetime = datetime.datetime.strptime(edate,'%Y-%m-%d').date()
        
    sdatetime = datetime.datetime.strptime(sdate,'%Y-%m-%d').date()
    days = (edatetime - sdatetime).days
    dates = list()
    for day in range(days+1):
        ndatetime = sdatetime + datetime.timedelta(days=day)
        ndate = datetime.datetime.strftime(ndatetime,'%Y-%m-%d')
        dates.append(ndate)
    return dates


# In[3]:


def get_weather(date):
    """ get weather data from almanac website
    Parameter: date, str, '2020-01-01'
    Return:    wea,  dict, includes date
    """
    
    url = 'https://www.almanac.com/weather/history/WA/Seattle/{}'.format(date)
    headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    r = requests.get(url,headers)
    soup = BeautifulSoup(r.text)
    table = soup.find_all('table',class_='weatherhistory_results')[0]

    items = table.find_all('h3')
    values = table.find_all('td')
    
    wea = dict()
    wea['date'] = date
    for i in range(len(items)):
        item = items[i].text
        value = values[i].text.replace(' °',' ')
        wea[item] = value
    return wea


# In[9]:


dates = get_dates('2011-01-01','today')

res = pd.DataFrame(columns=['Minimum Temperature', 'Mean Temperature', 'Maximum Temperature',
                           'Mean Sea Level Pressure', 'Mean Dew Point', 'Total Precipitation',
                           'Visibility', 'Snow Depth', 'Mean Wind Speed',
                           'Maximum Sustained Wind Speed', 'Maximum Wind Gust','date'])

t = 1
for date in dates:
    try:
        d = get_weather(date)
        df = pd.DataFrame.from_dict(d,orient='index').T
        res = pd.concat([res,df],axis=0)
    except:
        print('Errors on {}'.format(date))
        continue

    if t % 10 == 0:
        time.sleep(40)

    t += 1   
#     print(date,t)

res.set_index('date').to_csv(r'C:\Users\ZY\Desktop\seattle_weather2.csv',encoding='utf-8')




