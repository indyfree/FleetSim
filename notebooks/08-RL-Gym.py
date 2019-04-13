#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li></ul></div>

# ## Imports and Data loading

# In[1]:


# Display plots inline
get_ipython().run_line_magic('matplotlib', 'inline')

# Autoreload all package before excecuting a call
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[2]:


from datetime import datetime
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns

import gym

from evsim.rl import DDQN
from evsim.simulation import Simulation, SimulationConfig
from evsim.controller import Controller, strategy

logger = logging.getLogger(__name__)


# In[3]:


def visualize_log(filename, figsize=None, output=None):
    with open(filename, 'r') as f:
        data = json.load(f)
    if 'episode' not in data:
        raise ValueError('Log file "{}" does not contain the "episode" key.'.format(filename))
    episodes = data['episode']

    # Get value keys. The x axis is shared and is the number of episodes.
    keys = sorted(list(set(data.keys()).difference(set(['episode']))))

    if figsize is None:
        figsize = (15., 5. * len(keys))
    f, axarr = plt.subplots(len(keys), sharex=True, figsize=figsize)
    for idx, key in enumerate(keys):
        axarr[idx].plot(episodes, data[key])
        axarr[idx].set_ylabel(key)
    plt.xlabel('episodes')
    plt.tight_layout()
    if output is None:
        plt.show()
    else:
        plt.savefig(output)

        
def setup_logger(name, write=True):
    f = logging.Formatter("%(levelname)-7s %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(f)
    sh.setLevel(logging.ERROR)
    handlers = [sh]

    if write:
        os.makedirs("./logs", exist_ok=True)
        fh = logging.FileHandler("./logs/%s.log" % name, mode="w")
        fh.setFormatter(f)
        fh.setLevel(logging.DEBUG)
        handlers = [sh, fh]

    logging.basicConfig(
        level=logging.DEBUG, datefmt="%d.%m. %H:%M:%S", handlers=handlers
    )


# In[4]:


episode_steps = 6429

setup_logger("FleetSim-RL", write=False)
env = gym.make("evsim-v0") 

env.imbalance_costs(8000)

dqqn = DDQN(env, memory_limit=50000, nb_eps=50000, nb_warmup=1000)
dqqn.run(10 * episode_steps)


# In[5]:


visualize_log(dqqn.log_filename)


# In[6]:


result_filename = "./results/sim_result_ep_{}.csv"

def results(filename):
    start = "2016-06-01"
    end = "2018-01-01"

    df = pd.read_csv(filename)
    df = df.groupby(df.index // 3).agg({'timestamp': np.min,
                                        'risk_bal': np.min,
                                        'risk_intr': np.min,
                                        'profit_eur': np.sum,
                                        'imbalance_kwh': np.sum,
                                        'lost_rentals_eur': np.sum,
                                        'charged_vpp_kwh': np.sum,
                                        })

    df["timestamp"] = df["timestamp"].apply(lambda x : datetime.fromtimestamp(x))
    df = df.set_index("timestamp")
    df = df[start:end]

    grouper = "week"
    df[grouper] = df.index.week
    
    # sns.lineplot(x="week", y="profit_eur", data=df);
    sns.lineplot(x=grouper, y="risk_bal", data=df, label="Balancing");
    sns.lineplot(x=grouper, y="risk_intr", data=df, label="Intraday");

    print("Profit {:d} EUR".format(int(df["profit_eur"].sum())))
    print("Imbalance {} kWh".format(df["imbalance_kwh"].sum()))
    print("Lost rentals {} EUR".format(df["lost_rentals_eur"].sum()))
    print("Mean Risk Balancing={:.3}, Intraday={:.3}".format(df["risk_bal"].mean(), df["risk_intr"].mean()))
    


# In[7]:


results(result_filename.format(env.episode-1))


# In[8]:


dqqn.test()


# In[9]:


results(result_filename.format("test"))

