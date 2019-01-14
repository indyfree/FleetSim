#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-0.1"><span class="toc-item-num">0.1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li></ul></li><li><span><a href="#Load-Trip-Data" data-toc-modified-id="Load-Trip-Data-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Load Trip Data</a></span><ul class="toc-item"><li><span><a href="#Determine-trips-where-EV-was-not-determined-as-charging-correctly" data-toc-modified-id="Determine-trips-where-EV-was-not-determined-as-charging-correctly-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Determine trips where EV was not determined as charging correctly</a></span></li></ul></li><li><span><a href="#Demand-Patterns" data-toc-modified-id="Demand-Patterns-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Demand Patterns</a></span><ul class="toc-item"><li><span><a href="#Yearly-rental-patterns" data-toc-modified-id="Yearly-rental-patterns-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Yearly rental patterns</a></span></li><li><span><a href="#Weekly-Pattern-of-connected-EVS" data-toc-modified-id="Weekly-Pattern-of-connected-EVS-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Weekly Pattern of connected EVS</a></span></li><li><span><a href="#Daily-Pattern-of-connected-EVS" data-toc-modified-id="Daily-Pattern-of-connected-EVS-2.3"><span class="toc-item-num">2.3&nbsp;&nbsp;</span>Daily Pattern of connected EVS</a></span></li></ul></li></ul></div>

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

from evsim.data import load_car2go_trips, load_car2go_capacity


# # Load Trip Data

# In[4]:


trips = load_car2go_trips()


# In[5]:


trips[trips['trip_distance'] == 0]


# ## Determine trips where EV was not determined as charging correctly

# In[8]:


trips_error = trips.sort_values(["EV", "start_time"])
trips_error["soc_n"] = trips_error["start_soc"].shift(-1)
errors = trips_error[(trips_error["soc_n"] - trips_error["end_soc"] >= 5) & (trips_error["end_charging"].isna())] 
errors


# # Demand Patterns

# In[5]:


df = load_car2go_capacity()


# In[6]:


df


# In[7]:


def apply_smoother(df, days):
    DAY = 12*24

    df['ev_available_vpp_avg'] = df['ev_available_vpp'].rolling(
        window=int(days*DAY)).mean()
    df['ev_charging_avg'] = df['ev_charging'].rolling(
        window=int(days*DAY)).mean()
    df['available_battery_capacity_kwh_avg'] = df['available_battery_capacity_kwh'].rolling(
        window=int(days*DAY)).mean()
    df['available_charging_capacity_kw_avg'] = df['available_charging_capacity_kw'].rolling(
        window=int(days*DAY)).mean()

    return df


def plot(df, title, start=datetime(2016, 12, 1), end=datetime(2017, 5, 1)):
    X = df.loc[start:end][[
        'ev_available_vpp_avg', 'ev_charging_avg', 'available_battery_capacity_kwh_avg', 'available_charging_capacity_kw_avg']]
    return X.plot(figsize=(12, 4), title=title)


# ## Yearly rental patterns

# In[8]:


df = apply_smoother(df, days=3)
plot(df, "Yearly rental patterns")


# ## Weekly Pattern of connected EVS

# In[9]:


df = apply_smoother(df, days=0.5)
plot(df, "Weekly rental patterns", start=datetime(
    2017, 1, 1), end=datetime(2017, 1, 7))


# ## Daily Pattern of connected EVS

# In[10]:


df = apply_smoother(df, days=1/24)
plot(df, "Daily rental patterns", start=datetime(
    2017, 1, 4), end=datetime(2017, 1, 5))

