#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-0.1"><span class="toc-item-num">0.1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li></ul></li><li><span><a href="#Cleaning-Trip-Data" data-toc-modified-id="Cleaning-Trip-Data-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Cleaning Trip Data</a></span></li><li><span><a href="#Demand-Patterns" data-toc-modified-id="Demand-Patterns-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Demand Patterns</a></span><ul class="toc-item"><li><span><a href="#Yearly-rental-patterns" data-toc-modified-id="Yearly-rental-patterns-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Yearly rental patterns</a></span></li><li><span><a href="#Weekly-Pattern-of-connected-EVS" data-toc-modified-id="Weekly-Pattern-of-connected-EVS-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Weekly Pattern of connected EVS</a></span></li><li><span><a href="#Daily-Pattern-of-connected-EVS" data-toc-modified-id="Daily-Pattern-of-connected-EVS-2.3"><span class="toc-item-num">2.3&nbsp;&nbsp;</span>Daily Pattern of connected EVS</a></span></li></ul></li></ul></div>

# ## Imports and Data loading

# In[1]:


# Display plots inline
get_ipython().run_line_magic('matplotlib', 'inline')

# Autoreload all package before excecuting a call
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[2]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from vppsim.data import load_car2go_demand


# # Cleaning Trip Data

# In[8]:


trips = pd.read_pickle("../data/processed/trips_big.pkl")


# In[17]:


trips[trips['trip_distance'].notna()]


# # Demand Patterns

# In[3]:


df = load_car2go_demand()


# In[4]:


df_charging = df


# In[26]:


def apply_smoother(df, days):
    DAY = 12*24
    
    df['ev_available_avg'] = df['ev_available'].rolling(window=int(days*DAY)).mean()
    df['ev_charging_avg'] = df['ev_charging'].rolling(window=int(days*DAY)).mean()
    df['ev_charging_soc_avg_rol'] = df['ev_charging_soc_avg'].rolling(window=int(days*DAY)).mean()
    df['capacity_avg_kwh'] = df['capacity_available_kwh'].rolling(window=int(days*DAY)).mean()
    
    return df

def plot(df, title, start=datetime(2016, 12, 1), end=datetime(2017, 5, 1)):
    start_idx = df_charging.index.searchsorted(start)
    end_idx = df_charging.index.searchsorted(end)

    
    X = df_charging.iloc[start_idx:end_idx][['ev_available_avg', 'ev_charging_avg', 'ev_charging_soc_avg_rol', 'capacity_avg_kwh']]
    return X.plot(figsize=(12,4), title=title)


# ## Yearly rental patterns

# In[17]:


df = apply_smoother(df, days=3)
plot(df, "Yearly rental patterns")


# ## Weekly Pattern of connected EVS

# In[27]:


df = apply_smoother(df, days=0.5)
plot(df, "Weekly rental patterns", start=datetime(2017, 1, 1), end=datetime(2017, 1, 7))


# ## Daily Pattern of connected EVS

# In[28]:


start = df_charging.index.searchsorted(datetime(2017, 1, 4))
end = df_charging.index.searchsorted(datetime(2017, 1, 5))

df = apply_smoother(df, days=1/24)
plot(df, "Daily rental patterns", start=datetime(2017, 1, 4), end=datetime(2017, 1, 5))

