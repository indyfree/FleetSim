#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[2]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[4]:


#d = {'a': 1, 'b': 2}
d.update((k, v + 1) for k, v in d.items())
d


# In[15]:


e = {k: v for k, v in d.items() if v <= 5}
e


# In[43]:


bool(np.nan == 1)


# In[4]:


d = {}

def add(a):
    d[a[0]] = a[1]
    
add(("A", 1))
add(("A", 2))
d


# In[18]:


def reassign(list):
  list = [0, 1]

def append(list):
  list.append(1)

# list = [0]
reassign(list)
append(list)
list


# In[18]:


df = pd.read_csv('/home/morty/Downloads/stuttgart_trips.csv')


# In[37]:


df.drop(['Unnamed: 0', 'index'], axis=1).to_csv('~/Downloads/stuttgart.csv', index=False)


# In[38]:


pd.read_csv("/home/morty/Downloads/stuttgart.csv")


# In[12]:


from vppsim.data import load_car2go_trips, load_car2go_capacity

def determine_charging_stations(df):
    """Find charging stations where EV has been charged once (charging==1)."""

    df_stations = df.groupby(["coordinates_lat", "coordinates_lon"])["charging"].max()
    df_stations = df_stations[df_stations == 1]
    df_stations = df_stations.reset_index()
    return df_stations

def add_charging_stations(df_trips, df_stations):
    df_trips = df_trips.merge(
        df_stations,
        left_on=["end_lat", "end_lon"],
        right_on=["coordinates_lat", "coordinates_lon"],
        how="left",
    )

    df_trips.drop(["coordinates_lat", "coordinates_lon"], axis=1, inplace=True)
    df_trips.rename(columns={"charging": "end_charging"}, inplace=True)
    return df_trips


# In[ ]:


df = pd.read_csv("../data/raw/car2go/stuttgart.2016.12.01-2017.02.22.csv")


# In[19]:


df[df["name"] == ]


# In[24]:


df[["coordinates_lat", "coordinates_lon"]] = df[
    ["coordinates_lat", "coordinates_lon"]
].round(3)


df[(df["coordinates_lat"] == 9.148) & (df["coordinates_lat"] == 48.806)].describe()


# In[18]:


stations = determine_charging_stations(df)
stations[stations["coordinates_lat"] == 9.1478]

