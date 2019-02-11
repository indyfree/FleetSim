#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[22]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from evsim.data import load_car2go_trips, load_car2go_capacity


# In[125]:


df = load_car2go_trips(160)


# In[142]:


t = pd.date_range(datetime.utcfromtimestamp(df.start_time.min()), datetime.utcfromtimestamp(df.end_time.max()), freq="5min")
t.astype(np.int64) // 10**9

print(len(t))


# In[140]:


df.start_time.unique()


# In[67]:


a = df
a["s"] = a.start_time.apply(lambda x: datetime.utcfromtimestamp(x))
a["d"] = a["s"].astype(np.int64) // 10**9
a["e"] = a.d.apply(lambda x: datetime.utcfromtimestamp(x))
a


# In[5]:


print(round(9.14784, 4))
print(round(48.80589, 4))
print()
print(round(9.14674, 4), round(48.80549, 4))


# In[4]:


#d = {'a': 1, 'b': 2}
d.update((k, v + 1) for k, v in d.items())
d


# In[15]:


e = {k: v for k, v in d.items() if v <= 5}
e


# In[11]:


x = set(["S-GO2371", "S-GO2371", "S-GO2371", "S-GO2371", "S-GO2371", "S-GO2371", "S-GO2326", "S-GO2326", "S-GO2609", "S-GO2609", "S-GO2591", "S-GO2343", "S-GO2343", "S-GO2255", "S-GO2365", "S-GO2570", "S-GO2570", "S-GO2577", "S-GO2577", "S-GO2577", "S-GO2577", "S-GO2586", "S-GO2241", "S-GO2241", "S-GO2241", "S-GO2241", "S-GO2241", "S-GO2189", "S-GO2189", "S-GO2189", "S-GO2189", "S-GO2189", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2628", "S-GO2262", "S-GO2517", "S-GO2577", "S-GO2517", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "B-GO8937", "B-GO8937", "B-GO8937", "S-GO2375", "S-GO2375", "B-GO8937", "S-GO2653", "B-GO8937", "S-GO2653", "S-GO2653", "S-GO2653", "S-GO2653", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "B-GO8937", "S-GO2646", "B-GO8937", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2375", "S-GO2653", "S-GO2617", "S-GO2262", "S-GO2617", "S-GO2284", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2410", "S-GO2221", "S-GO2489", "S-GO2327"])
len(x)


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


# In[42]:


from evsim.data import load_car2go_trips, load_car2go_capacity

def transform_cols(df):
    df["timestamp"] = df["timestamp"].apply(
        lambda x: datetime.fromtimestamp(x)
    )
    df[["coordinates_lat", "coordinates_lon"]] = df[
        ["coordinates_lat", "coordinates_lon"]
    ].round(4)
    return df


def determine_charging_stations(df):
    """Find charging stations where EV has been charged once (charging==1)."""
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["day"] = df["timestamp"].dt.day
    
    df_stations = df.groupby(["name","coordinates_lat", "coordinates_lon", "year", "month", "day"]).max()
    #df_stations = df_stations[df_stations == 1]
    #df_stations = df_stations.reset_index()
    #logger.info("Determined %d charging stations in the dataset" % len(df_stations))
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


# In[37]:


df = pd.read_csv("../data/raw/car2go/stuttgart.2016.12.01-2017.02.22.csv")
df = transform_cols(df)


# In[43]:


get_ipython().run_cell_magic('time', '', 'stations = determine_charging_stations(df)\nstations')


# In[49]:


len(stations[stations.charging == 1])


# In[15]:


trips = load_car2go_trips()
trips["start_time"] = trips["start_time"].apply(
    lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
)
trips["end_time"] = trips["end_time"].apply(
    lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
)


# In[25]:


trips[trips["EV"] == 'S-GO2586'].loc[180000:]


# In[13]:


trips_error = trips[trips["EV"] == 'S-GO2371']
trips_error["n_EV"] = trips_error["EV"].shift(-1)
trips_error["n_soc"] = trips_error["start_soc"].shift(-1)

trips_error
errors = trips_error[
#    (trips_error["EV"] == trips_error["n_EV"]) # Same EV
    (trips_error["n_soc"] - trips_error["end_soc"] > 5) # Difference in SoC larger than 5
    & (trips_error["end_charging"] == 0) # Was not determined as charging last trip
]
errors

