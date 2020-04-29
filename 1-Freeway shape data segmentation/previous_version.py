#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from shapely import wkt
import shapely
import os
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')

import warnings
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)



# ## Read data

# In[58]:


def csv_to_shp(fname=r'E:\8.3 UW事务\AI_Net\Traffix_index\road\state_lines_2016.csv'):
    """ 原始csv中geometry列转换为shapely.kwt, 返回geodataframe
    """
    df = pd.read_csv(fname)
    df.rename(columns={'st_astext':'geometry'},inplace=True)
    df.drop('geom',axis=1,inplace=True)
    gdf = df_to_gdf(df)
    gdf = gdf[['id','display','direction','geometry']]
    return gdf


def df_to_gdf(df):
    """ dataframe to geodataframe
    """
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df,geometry='geometry')
    return gdf


def read_cabinet(fname=r'E:\2_Data\线圈数据\Cabinet.csv'):
    cabinet = pd.read_csv(fname)
    return cabinet


def road_99():
    """ debug raw SR99 shapefile
    """
    nr = gpd.read_file(r'E:\8.3 UW事务\AI_Net\Traffix_index\road\99\nn99.shp')
    nr['display'] = 99
    nr['direction'] = ['i','d']
    return nr


# In[8]:


# get geodataframe
road = csv_to_shp()
r = road.dissolve(by=['display','direction']).reset_index()

# cabinet data
cabinet = read_cabinet()


# ## Segmentation

# In[117]:


def get_keymile_loc(route,mile):
    """ get the lon,lat of the nearest milepost from cabinte data
    Parameters:
    ---------- 5,  90,  99, 405, 520
    route: str,  ['005', '090', '099', '405', '520']
    mile: number
    
    Return:
    -------
    loc: [lon,lat]
    """
    cabinet = read_cabinet()
    r = cabinet[cabinet.Route == route]
    r['err'] = (r['Milepost'] - mile).abs()   # warning
    r.merge(r['Milepost'].apply(lambda r: abs(r - mile)),left_index=True,right_index=True)
    loc = r.loc[r.err == r.err.min(),['Lon','Lat']].iloc[0].tolist()
    return loc


def get_bounday(route,bound,step):
    """ segment miles based on bound and step
    Parameters: 
    -----------
    route: str,  ['005', '090', '099', '405', '520']
    bound: boundary, list, [a,b]
    step: distance
    
    Return:
    -------
    bshp: dataframe, extend from keymiles, columns=['mile', 'lon', 'lat', 'mile2', 'lon2', 'lat2']
    """
    keyMile = list(np.arange(bound[0],bound[1]+step-0.01,step))
    boundshp = []
    for mile in keyMile:
        loc = get_keymile_loc(route=route,mile=mile)
        boundshp.append([mile,loc[0],loc[1]])
    
    bshp = pd.DataFrame(boundshp,columns=['mile','lon','lat'])
    bshp[['mile2','lon2','lat2']] = bshp[['mile','lon','lat']].shift(-1)
    bshp.dropna(inplace=True)   
    
    # debug the start milepost of SR90 and SR520
    if route == '090' and bound[0] < 2.07:
        bshp.loc[0,['lon','lat']] = [-122.320788,47.593652]
    if route == '520' and bound[0] < 0.28:
        bshp.loc[0,['lon','lat']] = [-122.322762,47.642281]
    
    return bshp


def intersects(box,line):
    """ select subline in the box
    """
    intersect = box.intersection(line)
    
    # shapely.geometry.linestring.LineString
    # join shapely.geometry.multilinestring.MultiLineString to a linestring
    if type(intersect) == shapely.geometry.multilinestring.MultiLineString:
        intersect = shapely.ops.linemerge(intersect)  
    return intersect


# In[59]:


def segmentation(route,direct,vector,bound,step):
    """ segment road shapfile to the fixed-length link shapefile
    Parameters:
    -----------
    route: str,  ['005', '090', '099', '405', '520']
    direct: 'i'-increasing; 'd'-decreasing
    vector: 'E', 'W', 'S', 'N'
    bound: list, [a,b]
    step: based link length
    """   
    if route == '099':
        r = road_99()
    else:
        road = csv_to_shp()
        r = road.dissolve(by=['display','direction']).reset_index() 
    
    
    line = r[(r.display==int(route)) & (r.direction==direct)]
    linestring = line.iloc[0]['geometry']
    
    # bound box
    res = []
    bshp = get_bounday(route=route,bound=bound,step=step)
    for i in range(len(bshp)):
        [minm,maxm] = bshp.loc[i,['mile','mile2']].sort_values().tolist()
        [minx,maxx] = bshp.loc[i,['lon','lon2']].sort_values().tolist()
        [miny,maxy] = bshp.loc[i,['lat','lat2']].sort_values().tolist()
        
        if vector in ['S','N']:
            box = shapely.geometry.box(minx-100,miny,maxx+100,maxy)
        if vector in ['E','W']:
            box = shapely.geometry.box(minx,miny-50,maxx,maxy+50)

        intersect = intersects(box,linestring)    
        res.append([i,route,direct,minm,maxm,intersect.wkt])
        
    res = pd.DataFrame(res,columns=['id','route','direct','mile_min','mile_max','geometry'])
    return res


# In[39]:


step = 2
base =  [['005','N','i',[153,183],step],
        ['005','S','d',[153,183],step],
        ['090','E','i',[1,5],4],
        ['090','W','d',[1,5],4],
        ['090','E','i',[5,14],step],
        ['090','W','d',[5,14],step],
        ['405','N','i',[0,30],step],
        ['405','S','d',[0,30],step],
        ['520','E','i',[0,13],step],
        ['520','W','d',[0,13],step],
        ['099','N','i',[23,34],step],
        ['099','S','d',[23,34],step]]


# In[118]:


seg = pd.DataFrame(columns=['id','route','direct','mile_min','mile_max','geometry'])

for i in range(len(base)):
    rse = segmentation(route=base[i][0],direct=base[i][2],vector=base[i][1],bound=base[i][3],step=base[i][4])
    seg = pd.concat([seg,rse],axis=0,ignore_index=True)


# In[119]:


res = df_to_gdf(seg)


# In[121]:


res.to_file(r'E:\8.3 UW事务\AI_Net\Traffix_index\road\segments\step-2.shp')
res.to_csv(r'E:\8.3 UW事务\AI_Net\Traffix_index\road\segments\step-2.csv',index=False)


# In[95]:


res.head()


# In[122]:


fig,ax = plt.subplots(figsize=(7,7))
road = csv_to_shp()
r = road.dissolve(by=['display','direction']).reset_index()

# r.plot(ax=ax,color='black')

res['sign'] = np.random.random(len(res))
res.plot(column='sign',cmap='rainbow',ax=ax,)

# ax.scatter(bshp['lon'],bshp['lat'],c='r',s=30)
plt.ylim([47.4,47.9])
plt.xlim([-122.4,-122])

