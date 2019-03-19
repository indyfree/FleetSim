#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-0.1"><span class="toc-item-num">0.1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li></ul></li><li><span><a href="#Intraday" data-toc-modified-id="Intraday-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Intraday</a></span></li><li><span><a href="#Balancing" data-toc-modified-id="Balancing-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Balancing</a></span></li><li><span><a href="#Comparison" data-toc-modified-id="Comparison-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Comparison</a></span><ul class="toc-item"><li><span><a href="#Plot-differences" data-toc-modified-id="Plot-differences-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>Plot differences</a></span></li></ul></li><li><span><a href="#Demand-Patterns" data-toc-modified-id="Demand-Patterns-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Demand Patterns</a></span><ul class="toc-item"><li><span><a href="#Yearly-rental-patterns" data-toc-modified-id="Yearly-rental-patterns-4.1"><span class="toc-item-num">4.1&nbsp;&nbsp;</span>Yearly rental patterns</a></span></li><li><span><a href="#Weekly-Pattern-of-connected-EVS" data-toc-modified-id="Weekly-Pattern-of-connected-EVS-4.2"><span class="toc-item-num">4.2&nbsp;&nbsp;</span>Weekly Pattern of connected EVS</a></span></li><li><span><a href="#Daily-Pattern-of-connected-EVS" data-toc-modified-id="Daily-Pattern-of-connected-EVS-4.3"><span class="toc-item-num">4.3&nbsp;&nbsp;</span>Daily Pattern of connected EVS</a></span></li><li><span><a href="#2.4.-Average-Daily-Pattern" data-toc-modified-id="2.4.-Average-Daily-Pattern-4.4"><span class="toc-item-num">4.4&nbsp;&nbsp;</span>2.4. Average Daily Pattern</a></span></li></ul></li></ul></div>

# ## Imports and Data loading

# In[1]:


# Display plots inline
get_ipython().run_line_magic('matplotlib', 'inline')

# Autoreload all package before excecuting a call
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[1]:


from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import gym

from evsim.data import load_car2go_trips, load_car2go_capacity


# In[6]:


env = gym.make('evsim-v0')


# In[10]:


type(env.action_space)

