#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-0.1"><span class="toc-item-num">0.1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li></ul></li><li><span><a href="#Load-Trip-Data" data-toc-modified-id="Load-Trip-Data-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Load Trip Data</a></span><ul class="toc-item"><li><span><a href="#Average-Charging-Speed" data-toc-modified-id="Average-Charging-Speed-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Average Charging Speed</a></span></li></ul></li><li><span><a href="#Error-Check" data-toc-modified-id="Error-Check-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Error Check</a></span><ul class="toc-item"><li><span><a href="#Trips-that-start-and-end-at-the-same-address" data-toc-modified-id="Trips-that-start-and-end-at-the-same-address-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Trips that start and end at the same address</a></span></li><li><span><a href="#EVs-charged-while-parking-without-being-at-charger" data-toc-modified-id="EVs-charged-while-parking-without-being-at-charger-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>EVs charged while parking without being at charger</a></span></li><li><span><a href="#EV-lost-Charge-at-Charger" data-toc-modified-id="EV-lost-Charge-at-Charger-2.3"><span class="toc-item-num">2.3&nbsp;&nbsp;</span>EV lost Charge at Charger</a></span></li><li><span><a href="#Determine-trips-where-EV-was-charging-before-appearing-at-charging-station" data-toc-modified-id="Determine-trips-where-EV-was-charging-before-appearing-at-charging-station-2.4"><span class="toc-item-num">2.4&nbsp;&nbsp;</span>Determine trips where EV was charging before appearing at charging station</a></span></li><li><span><a href="#Charged-on-trip-without-ending-at-charger" data-toc-modified-id="Charged-on-trip-without-ending-at-charger-2.5"><span class="toc-item-num">2.5&nbsp;&nbsp;</span>Charged on trip without ending at charger</a></span></li></ul></li><li><span><a href="#Demand-Patterns" data-toc-modified-id="Demand-Patterns-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Demand Patterns</a></span><ul class="toc-item"><li><span><a href="#Yearly-rental-patterns" data-toc-modified-id="Yearly-rental-patterns-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>Yearly rental patterns</a></span></li><li><span><a href="#Weekly-Pattern-of-connected-EVS" data-toc-modified-id="Weekly-Pattern-of-connected-EVS-3.2"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>Weekly Pattern of connected EVS</a></span><ul class="toc-item"><li><span><a href="#Example-Week" data-toc-modified-id="Example-Week-3.2.1"><span class="toc-item-num">3.2.1&nbsp;&nbsp;</span>Example Week</a></span></li></ul></li><li><span><a href="#Daily-Pattern-of-connected-EVS" data-toc-modified-id="Daily-Pattern-of-connected-EVS-3.3"><span class="toc-item-num">3.3&nbsp;&nbsp;</span>Daily Pattern of connected EVS</a></span></li></ul></li></ul></div>

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
import seaborn as sns

from evsim.data import load_car2go_trips, load_car2go_capacity


# # Load Trip Data

# In[3]:


trips = load_car2go_trips()
trips["start_time"] = trips["start_time"].apply(
    lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
)
trips["end_time"] = trips["end_time"].apply(
    lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
)
print("We are looking at %d trips!" % len(trips))
trips


# ## Average Charging Speed

# In[4]:


trips_charging = trips.sort_values(["EV", "start_time"])
trips_charging["n_EV"] = trips_charging["EV"].shift(-1)
trips_charging["n_soc"] = trips_charging["start_soc"].shift(-1)
trips_charging["n_time"] = trips_charging["start_time"].shift(-1)

trips_charging = trips_charging[trips_charging["EV"] == trips_charging["n_EV"]] # Only same EV
trips_charging = trips_charging[trips_charging["end_charging"] == 1] # EV is charging 
trips_charging = trips_charging[trips_charging["n_soc"] < 95] # Only count charging where EV was not fully charged

trips_charging["charged_soc"] = trips_charging["n_soc"] - trips_charging["end_soc"]
trips_charging = trips_charging[trips_charging["charged_soc"] > 10] # Charged more than 10 SoC

trips_charging["charged_duration"] = trips_charging["n_time"] - trips_charging["end_time"]
trips_charging["charged_minutes"] = trips_charging["charged_duration"].dt.total_seconds() / 60

trips_charging["charged_per_min"] = trips_charging["charged_soc"] / trips_charging["charged_minutes"]
hourly_soc = trips_charging["charged_per_min"].mean() * 60

EV_CAPACITY = 17.6
print("Average charged SoC per 5 Minutes %.2f%%." % (hourly_soc / 12))
print("Average charging station capacity %.2fkW." % ((hourly_soc / 100) * EV_CAPACITY))


# # Error Check

# ## Trips that start and end at the same address

# In[5]:


trips[(trips['start_address'] == trips['end_address'])].describe()


# **Comment:** All of them very short trip_duration (median at 5 minutes). Only 488 at charging station 
# Unprecise GPS?

# ## EVs charged while parking without being at charger 

# In[6]:


trips_error = trips.sort_values(["EV", "start_time"])

trips_error["n_EV"] = trips_error["EV"].shift(-1)
trips_error["n_soc"] = trips_error["start_soc"].shift(-1)

THRESHOLD = 15 
errors = trips_error[
    (trips_error["EV"] == trips_error["n_EV"]) # Same EV
    & (trips_error["n_soc"] - trips_error["end_soc"] > THRESHOLD) # Difference in SoC 
    & (trips_error["end_charging"] == 0) # Was not determined as charging last trip
]
print("%d EVs charged without beeing at charger behaviour %d times." % (len(errors.EV.unique()), len(errors)))


# **Comment**: Some EVs increase in SoC even if not beeing at a charging station (according to data)
# 
# **Simulation Solution**: TODO: Remove from dataset

# ## EV lost Charge at Charger

# In[7]:


trips_error = trips.sort_values(["EV", "start_time"])

trips_error["n_EV"] = trips_error["EV"].shift(-1)
trips_error["n_soc"] = trips_error["start_soc"].shift(-1)

errors = trips_error[
    (trips_error["EV"] == trips_error["n_EV"]) # Same EV
    & (trips_error["n_soc"] - trips_error["end_soc"] < -10) # Negative Charge at Charger
    & (trips_error["end_charging"] == 1) 
]
print("%d EVs lost charge despite beeing at charger behaviour %d times." % (len(errors.EV.unique()), len(errors)))


# **Comment**: Can happen if immediatly parked back at charger w/ same GPS and address. Also happens when adding charger to GPS points where not been charged in real data
#     
# **Simulation Solution**: Nothing yet. Not effecting Simulation badly since SoC are lower than in Simulation

# ## Determine trips where EV was charging before appearing at charging station

# In[8]:


trips_charged = trips.sort_values(["EV", "start_time"])

charged = trips_charged[
    (trips_charged["end_charging"] == 1)
    & (trips_charged["end_soc"] - trips_charged["start_soc"] > 5)
]
print("%d EVs were charged before showing up at charger %d times." % (len(charged.EV.unique()), len(charged)))


# **Comment:** Charging EVs don't show in the data when they reach a certain threshold, and show up again at around 75% charge.
# **Simulation Solution:** Add extra charge to battery when detected. (Done)

# ## Charged on trip without ending at charger

# In[9]:


errors = trips[
    (trips_error["end_charging"] == 0) # Was not determined as charging last trip
    & (trips_error["end_soc"] - trips_error["start_soc"] > 5)
]
print("%d EVs were charged on a trip, which didn't end at a charger %d times." % (len(errors.EV.unique()), len(errors)))


# **Comment**: Some EVs get charged on trips, no logical explanation found yet.
# 
# **Simulation Solution:**: Add extra charge to battery when detected. (done)

# # Demand Patterns

# In[10]:


df = load_car2go_capacity()
df["timestamp"] = df["timestamp"].apply(lambda x : datetime.fromtimestamp(x))
df = df.set_index("timestamp")


# In[11]:


print(len(df))
df.loc[df.index > "2017-02-23 23:35"].head()


# In[12]:


df.describe()


# In[13]:


def apply_smoother(df, days):
    DAY = 12*24

    df['vpp_avg'] = df['vpp'].rolling(
        window=int(days*DAY)).mean()
    df['charging_avg'] = df['charging'].rolling(
        window=int(days*DAY)).mean()
    df['fleet_soc_avg'] = df['fleet_soc'].rolling(
        window=int(days*DAY)).mean()
    df['vpp_capacity_kw_avg'] = df['vpp_capacity_kw'].rolling(
        window=int(days*DAY)).mean()

    return df


def plot(df, title, start=datetime(2016, 12, 1), end=datetime(2017, 5, 1)):
    X = df.loc[start:end][[
        'vpp_avg', 'charging_avg', 'fleet_soc_avg', 'vpp_capacity_kw_avg']]
    return X.plot(figsize=(12, 4), title=title)


# ## Yearly rental patterns

# In[14]:


df = apply_smoother(df, days=3)
plot(df, "Yearly rental patterns");


# ## Weekly Pattern of connected EVS

# In[20]:


df["day"] = df.index.weekday

f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="day", y="rent", data=df, ax=ax1)
sns.violinplot(x="day", y="charging", data=df, ax=ax2);


# In[16]:


df["hour"] = df.index.hour

f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="hour", y="fleet_soc", data=df, ax=ax1)
sns.violinplot(x="hour", y="charging", data=df, ax=ax2);


# **Comment**: EVs get fully charged during morning/noon and are not able to be used as vpp anymore

# ### Example Week

# In[17]:


df = apply_smoother(df, days=0.5)
plot(df, "Weekly rental patterns", start=datetime(
    2017, 3, 1), end=datetime(2017, 3, 7))


# ## Daily Pattern of connected EVS

# In[18]:


df["hour"] = df.index.hour

f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5)
sns.violinplot(x="hour", y="fleet_soc", data=df, ax=ax1)
sns.violinplot(x="hour", y="vpp", data=df, ax=ax2);


# In[19]:


df = apply_smoother(df, days=1/24)
plot(df, "Daily rental patterns", start=datetime(
    2017, 3, 6), end=datetime(2017, 3, 7));

