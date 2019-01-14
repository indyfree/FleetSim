#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#List-of-Tenders-(Ausschreibung)" data-toc-modified-id="List-of-Tenders-(Ausschreibung)-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>List of Tenders (Ausschreibung)</a></span></li><li><span><a href="#Result-of-Tenders-(Abgegebene-Angebote-/-Allocated-SRL)" data-toc-modified-id="Result-of-Tenders-(Abgegebene-Angebote-/-Allocated-SRL)-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Result of Tenders (Abgegebene Angebote / Allocated SRL)</a></span></li><li><span><a href="#Activated-Control-Reserve-from-regelleistungen.net" data-toc-modified-id="Activated-Control-Reserve-from-regelleistungen.net-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Activated Control Reserve from regelleistungen.net</a></span></li><li><span><a href="#Validate-Activated-Control-Reserve-Numbers" data-toc-modified-id="Validate-Activated-Control-Reserve-Numbers-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Validate Activated Control Reserve Numbers</a></span></li><li><span><a href="#Clearing-Prices-of-Secondary-Reserve" data-toc-modified-id="Clearing-Prices-of-Secondary-Reserve-5"><span class="toc-item-num">5&nbsp;&nbsp;</span>Clearing Prices of Secondary Reserve</a></span></li><li><span><a href="#SMARD-Data" data-toc-modified-id="SMARD-Data-6"><span class="toc-item-num">6&nbsp;&nbsp;</span>SMARD Data</a></span><ul class="toc-item"><li><span><a href="#Average-activated-price-vs-clearing-price" data-toc-modified-id="Average-activated-price-vs-clearing-price-6.1"><span class="toc-item-num">6.1&nbsp;&nbsp;</span>Average activated price vs clearing price</a></span></li></ul></li></ul></div>

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
import seaborn as sns


# # List of Tenders (Ausschreibung)

# __Use for bidding time for agent__

# In[3]:


df_tenders = pd.read_csv("../data/raw/balancing/tenders_2016_2017.csv", sep=';', index_col=False,
                         dayfirst=True, parse_dates=[0, 1, 2, 3, 4], infer_datetime_format=True, decimal=',')
df_tenders = df_tenders[['DATE_FROM', 'DATE_TO', 'GATE_OPEN_TIME',
                         'GATE_COSURE_TIME', 'PRODUCT', 'TOTAL_DEMAND_[MW]']]
df_tenders.columns = ['from', 'to', 'gate_opening',
                      'gate_closure', 'product', 'demand_mw']
df_tenders.head(10)


# # Result of Tenders (Abgegebene Angebote / Allocated SRL)

# Double checked with e.g. 
# - https://www.smard.de/blueprint/servlet/page/home/marktdaten/78?marketDataAttributes=%7B%22resolution%22:%22week%22,%22region%22:%22DE%22,%22from%22:1509490800000,%22to%22:1512945900000,%22moduleIds%22:%5B18000422,18000423%5D,%22selectedCategory%22:null,%22activeChart%22:true,%22language%22:%22de%22%7D#chart-legend
# 
# **Caution: When aggregating take into account not to sum up HT and NT!**

# In[4]:


df_results = pd.read_csv("../data/processed/tender_results.csv",
                         parse_dates=[0, 1], infer_datetime_format=True)
df_results[(df_results["from"] == '2017-10-23') & (df_results["product_type"] == 'NEG') &
           (df_results["product_time"] == 'HT')].sort_values(['energy_price_mwh'], ascending=False)


# # Activated Control Reserve from regelleistungen.net

# In[5]:


df_activated = pd.read_csv("../data/processed/activated_control_reserve.csv",
                           parse_dates=[0], infer_datetime_format=True)
df_activated.head(10)


# # Validate Activated Control Reserve Numbers

# _"Laut Monitoring-Bericht 2017 der Bundesnetzagentur betrug im Jahr 2016 die abgerufene Energiemenge in der negativen Sekundärreserve (SRL) 0,7 TWh sowie 1,4 TWh für die positive SRL"_
# 
# -- https://www.next-kraftwerke.de/wissen/regelenergie
# 
# -- https://www.smard.de/blueprint/servlet/page/home/marktdaten/78?marketDataAttributes=%7B%22resolution%22:%22year%22,%22region%22:%22DE%22,%22from%22:1451602800000,%22to%22:1514846700000,%22moduleIds%22:%5B18000427,18000426%5D,%22selectedCategory%22:18,%22activeChart%22:true,%22language%22:%22de%22%7D#chart-legend
# 
# Also shows this

# In[6]:


# Aggregated activated is in 15-min intervals of Capacity in MW, divide by 4 to get Amount of used energy TWh
activated_neg_2016 = df_activated[df_activated["from"] < datetime(
    2017, 1, 1)].neg_mw.sum() / 1000000 / 4
activated_pos_2016 = df_activated[df_activated["from"] < datetime(
    2017, 1, 1)].pos_mw.sum() / 1000000 / 4

print('Activated Control Reserve 2016 - Negative : %.2f TWh Positive %.2f TWh' %
      (activated_neg_2016, activated_pos_2016))


# # Clearing Prices of Secondary Reserve

# __Calculated assumed 15-min clearing prices for negative control reserve by looking at actual activated reserve__

# In[7]:


from evsim.data import load_balancing_data

df_clearing_prices = load_balancing_data()
df_clearing_prices.head()


# In[8]:


df_clearing_prices["day"] = df_clearing_prices["from"].dt.weekday
df_clearing_prices["hour"] = df_clearing_prices["from"].dt.hour

clipped_data = df_clearing_prices[["day", "hour", "clearing_price_mwh", "capacity_mw"]].clip(-50, 200)
f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="hour", y="capacity_mw", data=clipped_data, ax=ax1)
sns.violinplot(x="hour", y="clearing_price_mwh", data=clipped_data, ax=ax2)


# # SMARD Data

# SMARD: _Für die Sekundärregelung vorgehaltene Leistung bzw. Menge [MW], der durchschnittliche Leistungspreis der bezuschlagten Angebote [€/MW], die durchschnittlich abgerufene Leistung bzw. Menge [MWh] und der durchschnittliche Arbeitspreis aller jeweils aktivierten Angebote [€/MWh]_

# In[9]:


df_smard = pd.read_csv("../data/raw/balancing/smard_activated_srl_2016_2017.csv", sep=';', index_col=False,
                         dayfirst=True, parse_dates=[0], infer_datetime_format=True)
df_smard.columns=["date", "time", "acitvated_pos_mwh", "activated_neg_mwh", "energy_price_pos", "energy_price_neg", "allocated_pos_mw", "allocated_neg_mw", "capacity_price_pos", "capacity_price_neg"]


# Merge date and time columns
df_smard["date"] = pd.to_datetime(
    df_smard["date"].astype(str)
    + " "
    + df_smard["time"].astype(str)
)

df_smard.drop("time", axis=1, inplace=True)
df_smard.head()


# In[10]:


df_smard["day"] = df_smard["date"].dt.weekday
df_smard["hour"] = df_smard["date"].dt.hour

clipped_data = df_smard[["day", "hour", "energy_price_neg", "activated_neg_mwh"]].clip(-50, 200)
f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="hour", y="activated_neg_mwh", data=clipped_data, ax=ax1)
sns.violinplot(x="hour", y="energy_price_neg", data=clipped_data, ax=ax2)


# In[11]:


# Difference between average and clearing price
df_smard.groupby("hour")["energy_price_neg"].mean() - df_clearing_prices.groupby("hour")["clearing_price_mwh"].mean()


# ## Average activated price vs clearing price

# - Average price for activated energy is higher than clearing price. 
# - TSO wants the provider to pay higher prices
# - If we bid _higher_ than clearing price our bid will get accepted!
