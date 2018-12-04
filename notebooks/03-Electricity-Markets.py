#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Bulk-Data-Merit-Order" data-toc-modified-id="Bulk-Data-Merit-Order-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Bulk Data Merit Order</a></span><ul class="toc-item"><li><span><a href="#List-of-Tenders-(Ausschreibung)" data-toc-modified-id="List-of-Tenders-(Ausschreibung)-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>List of Tenders (Ausschreibung)</a></span></li><li><span><a href="#Result-of-Tenders-(Abgegebene-Angebote)" data-toc-modified-id="Result-of-Tenders-(Abgegebene-Angebote)-1.2"><span class="toc-item-num">1.2&nbsp;&nbsp;</span>Result of Tenders (Abgegebene Angebote)</a></span></li><li><span><a href="#Activated-Control-Reserve" data-toc-modified-id="Activated-Control-Reserve-1.3"><span class="toc-item-num">1.3&nbsp;&nbsp;</span>Activated Control Reserve</a></span></li></ul></li><li><span><a href="#Balancing-Market-(regelleistungen)" data-toc-modified-id="Balancing-Market-(regelleistungen)-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Balancing Market (regelleistungen)</a></span></li><li><span><a href="#Calculate-Merit-Order" data-toc-modified-id="Calculate-Merit-Order-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Calculate Merit Order</a></span></li></ul></div>

# In[2]:


# Display plots inline
get_ipython().run_line_magic('matplotlib', 'inline')

# Autoreload all package before excecuting a call
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[3]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# # Bulk Data Merit Order

# ## List of Tenders (Ausschreibung)

# In[231]:


df_tenders = pd.read_csv("../data/raw/tenders_2016_2017.csv", sep=';', index_col=False,
                     dayfirst=True, parse_dates=[0, 1, 2, 3,4], infer_datetime_format=True, decimal=',')
df_tenders = df_tenders[['DATE_FROM', 'DATE_TO', 'GATE_OPEN_TIME', 'GATE_COSURE_TIME', 'PRODUCT', 'TOTAL_DEMAND_[MW]']]
df_tenders.columns = ['from', 'to', 'gate_opening', 'gate_closure', 'product', 'demand_mw']
df_tenders.head(20)


# ## Result of Tenders (Abgegebene Angebote)

# In[230]:


df_results = pd.read_csv("../data/raw/results_2016_2017.csv", sep=';', index_col=False,
                     dayfirst=True, parse_dates=[0, 1], infer_datetime_format=True, decimal=',')
df_results.drop(['TYPE_OF_RESERVES', 'COUNTRY'], inplace=True, axis=1)
df_results.columns = ['from', 'to', 'product', 'capacity_price_mw','energy_price_mwh', 'payment_direction', 'offered_mw', 'allocated_mw']
df_results['payment_direction'].replace(['GRID_TO_PROVIDER', 'PROVIDER_TO_GRID'], ['GP', 'PG'], inplace=True)
df_results.head(20)


# ## Activated Control Reserve

# In[225]:


df_activated = pd.read_csv("../data/raw/balancing/activated_secondary_reserve_2016_2017.csv", sep=';', decimal=',', thousands='.', index_col=False, dayfirst=True, parse_dates=[0], infer_datetime_format=True)
df_activated.drop(['LETZTE AENDERUNG', 'ERSATZWERT','LETZTE AENDERUNG.1', 'QUAL. NEG', 'QUAL. POS'], axis=1, inplace=True)
df_activated.columns = ['date', 'from', 'to', 'neg_mw', 'pos_mw']
#print(df_activated)
hours_minutes_from = df_activated['from'].str.split(":", expand=True)
df_activated['from'] = pd.to_datetime(df_activated['date'].astype(str) + " " + hours_minutes_from[0] + ":" + hours_minutes_from[1])

hours_minutes_to = df_activated['to'].str.split(":", expand=True)
df_activated['to'] = pd.to_datetime(df_activated['date'].astype(str) + " " + hours_minutes_to[0] + ":" + hours_minutes_to[1])

# Fix time where 0:00 belongs to previous day
df_activated.loc[(df_activated['to'].dt.hour == 0) & (df_activated['to'].dt.minute == 0), 'to'] = df_activated.to + pd.DateOffset(days=1)

df_activated.drop('date', inplace=True, axis=1)
df_activated.head(10)

