#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li><li><span><a href="#Calculate-connected-EVs-and-accumulated-SoC" data-toc-modified-id="Calculate-connected-EVs-and-accumulated-SoC-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Calculate connected EVs and accumulated SoC</a></span></li><li><span><a href="#Weekly-Pattern-of-connected-EVS" data-toc-modified-id="Weekly-Pattern-of-connected-EVS-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Weekly Pattern of connected EVS</a></span></li></ul></div>

# ## Imports and Data loading

# In[6]:


# Display plots inline
get_ipython().run_line_magic('matplotlib', 'inline')

# Autoreload all package before excecuting a call
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[7]:


import pandas as pd
from datetime import datetime

from vppsim.data import load_car2go


# In[194]:


df = load_car2go()


# In[10]:


df.head(50)


# ## Calculate connected EVs and accumulated SoC

# In[193]:


charging = {}
total = {}

df_charging = list()

df_start = df.sort_values(by=['start_time'])

for rental in df.sort_values(by=['end_time']).itertuples():
    total[rental.EV] = rental.EV
    if rental.end_charging:
        charging[rental.EV] = rental.end_charging
    
    if df_start.iloc[df_start['timestamp'] == rental.timestamp, :].EV in charging:
        del charging[rental.EV]
        
    df_charging.append((rental.end_time, len(charging), len(total)))

                     
df_charging = pd.DataFrame(df_charging, columns=['timestamp', 'ev_charging', 'total_ev']) 
df_charging.timestamp = df_charging.timestamp.apply(lambda x: datetime.fromtimestamp(x))
df_charging.groupby(['timestamp']).max()


# In[ ]:


available = {}
charging = {}
connected = list()
total = {}

df_trips = df.sort_values(by=['end_time'])
for rental in df_trips.itertuples():
    if rental.EV in available:
        del available[rental.EV]
    if rental.EV in charging:
        del charging[rental.EV]
    if rental.end_charging:
        charging[rental.EV] = rental.end_soc
    total[rental.EV] = rental.end_soc
    available[rental.EV] = rental.EV
    connected.append((rental.end_time, len(charging), len(total), len(available)))

df_trips = pd.DataFrame(connected, columns=['timestamp', 'ev_charging', 'total_ev', 'available_ev']) 
df_trips.timestamp = df_trips.timestamp.apply(lambda x: datetime.fromtimestamp(x))
df_trips = df_trips.set_index(['timestamp'])


# ## Weekly Pattern of connected EVS

# In[174]:


start = df_trips.index.searchsorted(datetime(2017, 10, 10))
end = df_trips.index.searchsorted(datetime(2017, 10, 17))

df_trips['ev_charging_avg'] = df_trips['ev_charging'].rolling(window=12*6).mean()
df_trips.iloc[start:end].loc[:,['ev_charging', 'ev_charging_avg']].plot();


# In[22]:


df.groupby(['end_time']).sum()


# In[ ]:




