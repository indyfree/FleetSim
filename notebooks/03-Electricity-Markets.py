#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Bulk-Data-Merit-Order" data-toc-modified-id="Bulk-Data-Merit-Order-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Bulk Data Merit Order</a></span><ul class="toc-item"><li><span><a href="#List-of-Tenders-(Ausschreibung)" data-toc-modified-id="List-of-Tenders-(Ausschreibung)-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>List of Tenders (Ausschreibung)</a></span></li><li><span><a href="#Result-of-Tenders-(Abgegebene-Angebote-/-Allocated-SRL)" data-toc-modified-id="Result-of-Tenders-(Abgegebene-Angebote-/-Allocated-SRL)-1.2"><span class="toc-item-num">1.2&nbsp;&nbsp;</span>Result of Tenders (Abgegebene Angebote / Allocated SRL)</a></span><ul class="toc-item"><li><span><a href="#Supply/Demand-Curve-according-to-bids-and-asks-(According-to-Kahlen)" data-toc-modified-id="Supply/Demand-Curve-according-to-bids-and-asks-(According-to-Kahlen)-1.2.1"><span class="toc-item-num">1.2.1&nbsp;&nbsp;</span>Supply/Demand Curve according to bids and asks (According to Kahlen)</a></span></li></ul></li><li><span><a href="#Activated-Control-Reserve-from-regelleistungen.net" data-toc-modified-id="Activated-Control-Reserve-from-regelleistungen.net-1.3"><span class="toc-item-num">1.3&nbsp;&nbsp;</span>Activated Control Reserve from regelleistungen.net</a></span><ul class="toc-item"><li><span><a href="#Calculate-15-min-Clearing-prices-by-looking-at-activated-reserve" data-toc-modified-id="Calculate-15-min-Clearing-prices-by-looking-at-activated-reserve-1.3.1"><span class="toc-item-num">1.3.1&nbsp;&nbsp;</span>Calculate 15-min Clearing prices by looking at activated reserve</a></span></li><li><span><a href="#Weekly-activated-secondary-control-reserve" data-toc-modified-id="Weekly-activated-secondary-control-reserve-1.3.2"><span class="toc-item-num">1.3.2&nbsp;&nbsp;</span>Weekly activated secondary control reserve</a></span></li></ul></li><li><span><a href="#Double-Check-Numbers" data-toc-modified-id="Double-Check-Numbers-1.4"><span class="toc-item-num">1.4&nbsp;&nbsp;</span>Double Check Numbers</a></span></li></ul></li><li><span><a href="#Calculate-Merit-order-for-each-Week" data-toc-modified-id="Calculate-Merit-order-for-each-Week-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Calculate Merit order for each Week</a></span></li></ul></div>

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

# In[4]:


df_tenders = pd.read_csv("../data/raw/balancing/tenders_2016_2017.csv", sep=';', index_col=False,
                     dayfirst=True, parse_dates=[0, 1, 2, 3,4], infer_datetime_format=True, decimal=',')
df_tenders = df_tenders[['DATE_FROM', 'DATE_TO', 'GATE_OPEN_TIME', 'GATE_COSURE_TIME', 'PRODUCT', 'TOTAL_DEMAND_[MW]']]
df_tenders.columns = ['from', 'to', 'gate_opening', 'gate_closure', 'product', 'demand_mw'] df_tenders.head(20)


# ## Result of Tenders (Abgegebene Angebote / Allocated SRL)

# Double checked with e.g. 
# - https://www.smard.de/blueprint/servlet/page/home/marktdaten/78?marketDataAttributes=%7B%22resolution%22:%22week%22,%22region%22:%22DE%22,%22from%22:1509490800000,%22to%22:1512945900000,%22moduleIds%22:%5B18000422,18000423%5D,%22selectedCategory%22:null,%22activeChart%22:true,%22language%22:%22de%22%7D#chart-legend
# 
# **Caution: When aggregating take into account not to sum up HT and NT!**

# In[265]:


df_results = pd.read_csv("../data/raw/balancing/results_2016_2017.csv", sep=';', index_col=False,
                     dayfirst=True, parse_dates=[0, 1], infer_datetime_format=True, decimal=',')

df_results.drop(['TYPE_OF_RESERVES', 'COUNTRY'], inplace=True, axis=1)
df_results.columns = ['from', 'to', 'product', 'capacity_price_mw','energy_price_mwh', 'payment_direction', 'offered_mw', 'allocated_mw']

df_results = pd.concat([df_results, pd.DataFrame(df_results["product"].str.split('_',1).tolist(),
                                   columns = ['product_type','product_time'])], axis = 1)
df_results.drop('product', axis=1, inplace=True)


# In[266]:


# Check for negative payment direction in positive control reserve
df_results.loc[df_results["product_type"] == "POS"]["payment_direction"].unique()


# In[267]:


# Make energy prices negative where provider has to pay for energy
df_results.loc[df_results['payment_direction'] == 'PROVIDER_TO_GRID',['energy_price_mwh']] = df_results['energy_price_mwh'] * (-1)
df_results.drop(["payment_direction"], axis=1, inplace=True)
df_results = df_results.sort_values(['from', 'product_type', 'product_time', 'energy_price_mwh'])


# In[273]:


print(df_results.size)
df_results.head(10)


# ### Supply/Demand Curve according to bids and asks (According to Kahlen)

# **Kahlen:** _The data for Stuttgart contains the individual bids and asks with the respective quantities and prices for each 15-minute time interval. From these bids and asks we form the demand and supply curves. The clearing point Q∗ sets the equilibrium, which determines whether the energy market operator settles the asks and bids placed by FleetPower (if the price P from the model is below the market price_ (P.71, Diss)

# In[34]:


time = "HT"
day = "2016-12-26"
df_plot = df_results.loc[(df_results["product_time"] == time) & (df_results["from"] == day)]

df_supply = df_plot.loc[df_plot["product_type"] == "POS"].sort_values(["energy_price_mwh"], ascending=False).copy()
df_supply["cum_capacity_mw"] = df_supply["allocated_mw"].cumsum()
df_supply.reset_index()

df_demand = df_plot.loc[df_plot["product_type"] == "NEG"].sort_values(["energy_price_mwh"]).copy()
df_demand["cum_capacity_mw"] = df_demand["allocated_mw"].cumsum()
df_demand.reset_index

fig, ax = plt.subplots()
plt.plot(df_supply.cum_capacity_mw, df_supply.energy_price_mwh, label='Supply: Positive control reserve')
plt.plot(df_demand.cum_capacity_mw, df_demand.energy_price_mwh, label='Demand: Negative control reserve')
ax.set_xlabel("Capacity [MW]")
ax.set_ylabel("Energy Price [EUR/MWh]")
plt.title('Merit Order Curve %s' % day)
plt.legend();
plt.show()


df_cp = pd.concat([df_supply, df_demand]).sort_values("cum_capacity_mw").reset_index()
ask = float("inf")
bid = 0
for price in df_cp.itertuples():
    if price.product_type == "POS":
        ask = price.energy_price_mwh
    else:
        bid = price.energy_price_mwh
    
    if bid > ask:
        print('Clearing Price: %s EUR/MWh' % bid)
        break;


#  **This is not an Auction where participants place bids & ask, the system operator plays the other part. Also not in 15min slots, how to get clearing price??**

# ## Activated Control Reserve from regelleistungen.net

# In[236]:


df_activated = pd.read_csv("../data/raw/balancing/activated_secondary_reserve_2016_2017.csv", sep=';', decimal=',', thousands='.', index_col=False, dayfirst=True, parse_dates=[0], infer_datetime_format=True)
df_activated.drop(['LETZTE AENDERUNG', 'ERSATZWERT','LETZTE AENDERUNG.1', 'QUAL. NEG', 'QUAL. POS'], axis=1, inplace=True)
df_activated.columns = ['date', 'from', 'to', 'neg_mw', 'pos_mw']
hours_minutes_from = df_activated['from'].str.split(":", expand=True)
df_activated['from'] = pd.to_datetime(df_activated['date'].astype(str) + " " + hours_minutes_from[0] + ":" + hours_minutes_from[1])

hours_minutes_to = df_activated['to'].str.split(":", expand=True)
df_activated['to'] = pd.to_datetime(df_activated['date'].astype(str) + " " + hours_minutes_to[0] + ":" + hours_minutes_to[1])

# Fix time where 0:00 belongs to previous day
df_activated.loc[(df_activated['to'].dt.hour == 0) & (df_activated['to'].dt.minute == 0), 'to'] = df_activated.to + pd.DateOffset(days=1)

df_activated.drop('date', inplace=True, axis=1)
df_activated.describe()


# ### Calculate 15-min Clearing prices by looking at activated reserve

# In[280]:


# Calculate cumulative sums of every timeslot for every product
days = df_results["from"].unique()
types = df_results["product_type"].unique()
times = df_results["product_time"].unique()

cumsums = list()
for d in days:
    for typ in types:
        for t in times:
            cs = df_results.loc[(df_results["from"] == d)
                                & (df_results["product_type"] == typ)
                                & (df_results["product_time"] == t), ["allocated_mw"]].cumsum()
            cumsums.append(cs)

df_results["cumsum_allocated_mw"] = pd.concat(cumsums)


# In[301]:


get_ipython().run_cell_magic('time', '', 'clearing_prices = list()\n\nfor t in df_activated.iloc[0:1500, ].itertuples():\n    day = pd.to_datetime(t[1])\n    # Find out product time\n    product_time = "HT" if 8 <= day.hour < 20 else "NT"\n    # We are only interested in negative control reserve clearing prices\n    product_type = "NEG"\n    \n    # TODO: Bids are for the next week\n    cp = df_results.loc[(df_results["to"] >= pd.Timestamp(day.date()))\n                        & (df_results["from"] <= pd.Timestamp(day.date()))\n                        & (df_results["product_time"] == time)\n                        & (df_results["product_type"] == product_type)\n                        & (df_results["cumsum_allocated_mw"] >= t.neg_mw)].iloc[0]["energy_price_mwh"]\n    clearing_prices.append(cp)\n\n# print(clearing_prices)\n#df_activated["clearing_prices"] = clearing_prices')


# In[133]:





# __Q: Divide by 4 to get quarterly MwH?__

# ### Weekly activated secondary control reserve

# In[270]:


df_activated.groupby(df_activated.index // (4 * 24 * 7)).sum().head(10)


# ## Double Check Numbers

# _"Laut Monitoring-Bericht 2017 der Bundesnetzagentur betrug im Jahr 2016 die abgerufene Energiemenge in der negativen Sekundärreserve (SRL) 0,7 TWh sowie 1,4 TWh für die positive SRL"_
# 
# -- https://www.next-kraftwerke.de/wissen/regelenergie
# 
# -- https://www.smard.de/blueprint/servlet/page/home/marktdaten/78?marketDataAttributes=%7B%22resolution%22:%22year%22,%22region%22:%22DE%22,%22from%22:1451602800000,%22to%22:1514846700000,%22moduleIds%22:%5B18000427,18000426%5D,%22selectedCategory%22:18,%22activeChart%22:true,%22language%22:%22de%22%7D#chart-legend
# 
# Also shows this

# In[50]:


allocated_neg_2016 = df_results.loc[(df_results["from"] < datetime(2017, 1, 1)) &
                                    (df_results["product"] == "NEG_NT")].allocated_mw.sum()
allocated_pos_2016 = df_results.loc[(df_results["from"] < datetime(2017, 1, 1)) &
                                    (df_results["product"] == "POS_NT")].allocated_mw.sum()
print('Allocated Control Reserve 2016 - Negative : %.2f TW Positive %.2f TW' %
      (allocated_neg_2016 / 1000000, allocated_pos_2016 / 1000000))


# In[45]:


activated_neg_2016 = df_activated[df_activated["from"] < datetime(
    2017, 1, 1)].neg_mw.sum()
activated_pos_2016 = df_activated[df_activated["from"] < datetime(
    2017, 1, 1)].pos_mw.sum()
print('Activated Control Reserve 2016 - Negative : %.2f TW Positive %.2f TW' %
      (activated_neg_2016 / 1000000, activated_pos_2016 / 1000000))


# In[44]:


df_activated.set_index("from").groupby(pd.Grouper(freq='M')).sum().plot()


# # Calculate Merit order for each Week

# In[239]:


# Use index and then resample
# https://stackoverflow.com/questions/29706740/grouping-pandas-data-frame-by-time-intervals

