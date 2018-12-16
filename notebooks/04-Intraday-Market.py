#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[3]:


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
import seaborn as sns


# __EPEX Intraday continous market__
# 
# - Continuous trading 7 days a week, 24 hours a day, all year around  
# - Hourly contracts for the next day open at 15:00 pm (d-1) for DE, FR, CH & AT 
# - Hourly contracts for the next day open at 2.00 pm (d-1) for NL & BE 
# - 30-min contracts for the next day open at 15:30 (d-1) for CH, DE, FR 
# - 15-min contracts for the next day open at 4.00 pm (d-1) 

# In[16]:


df = pd.read_csv("../data/processed/intraday_prices.csv", parse_dates=[0], infer_datetime_format=True)
df["hour"] = df["delivery_date"].dt.hour

# Clip for better visibility of plots
df["unit_price_eur_mwh"] = df["unit_price_eur_mwh"].clip(-200,200)

f, ax = plt.subplots(1, 1)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="hour", y="unit_price_eur_mwh", data=df, ax=ax);

