#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[1]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:


df = pd.read_csv("../data/raw/car2go/stuttgart.2017.05.01-2017.10.31.csv")


# In[3]:


df.rename(columns={'9.13089': 'coordinates_lat', '48.7754': 'coordinates_lon', '0': 'charging'}, inplace=True)
df.columns


# In[4]:


df["coordinates_lat"] = df["coordinates_lat"].round(4)
df["coordinates_lon"] = df["coordinates_lon"].round(4)
charging_stations = df.groupby(["coordinates_lat", "coordinates_lon"])["charging"].max()
charging_stations = charging_stations[charging_stations == 1].reset_index()

df.merge(charging_stations, on=["coordinates_lat", "coordinates_lon"], how='left')


# In[7]:


df


# In[35]:





# In[12]:



df_first = df.groupby(["name", "address"]).first()
df_first.describe()


# In[11]:


df_g = df.groupby(["name", "address"]).mean()
df_g.describe()


# In[13]:


df_last = df.groupby(["name", "address"]).last()
df_last.describe()


# In[14]:


df_g[(df_g["charging"] != 0) & (df_g["charging"] != 1)]


# In[21]:


df_diff = df_first.charging - df_g.charging
df_diff[df_diff < 0]

