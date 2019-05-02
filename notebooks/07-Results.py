#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents &lt;br&gt;&lt;/br&gt;<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><ul class="toc-item"><li><span><a href="#Imports-and-Data-loading" data-toc-modified-id="Imports-and-Data-loading-0.1"><span class="toc-item-num">0.1&nbsp;&nbsp;</span>Imports and Data loading</a></span></li><li><span><a href="#Regular-Profit" data-toc-modified-id="Regular-Profit-0.2"><span class="toc-item-num">0.2&nbsp;&nbsp;</span>Regular Profit</a></span></li><li><span><a href="#Charging-Stations" data-toc-modified-id="Charging-Stations-0.3"><span class="toc-item-num">0.3&nbsp;&nbsp;</span>Charging Stations</a></span></li></ul></li><li><span><a href="#Baseline-Charging" data-toc-modified-id="Baseline-Charging-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Baseline Charging</a></span></li><li><span><a href="#Intraday" data-toc-modified-id="Intraday-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Intraday</a></span><ul class="toc-item"><li><span><a href="#Benchmark" data-toc-modified-id="Benchmark-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Benchmark</a></span></li><li><span><a href="#Risk-Averse-(r=0.3,-acc=90)" data-toc-modified-id="Risk-Averse-(r=0.3,-acc=90)-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Risk Averse (r=0.3, acc=90)</a></span></li></ul></li><li><span><a href="#Balancing" data-toc-modified-id="Balancing-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Balancing</a></span><ul class="toc-item"><li><span><a href="#Benchmark" data-toc-modified-id="Benchmark-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>Benchmark</a></span></li><li><span><a href="#Risk-Averse-(r=0.5,-acc=70)" data-toc-modified-id="Risk-Averse-(r=0.5,-acc=70)-3.2"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>Risk Averse (r=0.5, acc=70)</a></span></li></ul></li><li><span><a href="#Integrated" data-toc-modified-id="Integrated-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Integrated</a></span><ul class="toc-item"><li><span><a href="#100%-Benchmark" data-toc-modified-id="100%-Benchmark-4.1"><span class="toc-item-num">4.1&nbsp;&nbsp;</span>100% Benchmark</a></span></li><li><span><a href="#70,90-Benchmark" data-toc-modified-id="70,90-Benchmark-4.2"><span class="toc-item-num">4.2&nbsp;&nbsp;</span>70,90 Benchmark</a></span></li><li><span><a href="#Risk-Averse-(r=0.5,0.3,-acc=70,90)" data-toc-modified-id="Risk-Averse-(r=0.5,0.3,-acc=70,90)-4.3"><span class="toc-item-num">4.3&nbsp;&nbsp;</span>Risk Averse (r=0.5,0.3, acc=70,90)</a></span></li><li><span><a href="#Risk-Seeking-(r=0.2,0.00,-acc=70,90)" data-toc-modified-id="Risk-Seeking-(r=0.2,0.00,-acc=70,90)-4.4"><span class="toc-item-num">4.4&nbsp;&nbsp;</span>Risk Seeking (r=0.2,0.00, acc=70,90)</a></span></li><li><span><a href="#RL-(acc=50,60)" data-toc-modified-id="RL-(acc=50,60)-4.5"><span class="toc-item-num">4.5&nbsp;&nbsp;</span>RL (acc=50,60)</a></span></li><li><span><a href="#RL-(acc=70,90)" data-toc-modified-id="RL-(acc=70,90)-4.6"><span class="toc-item-num">4.6&nbsp;&nbsp;</span>RL (acc=70,90)</a></span></li><li><span><a href="#RL-(acc=80,95)" data-toc-modified-id="RL-(acc=80,95)-4.7"><span class="toc-item-num">4.7&nbsp;&nbsp;</span>RL (acc=80,95)</a></span></li><li><span><a href="#RL-(acc=90,99)" data-toc-modified-id="RL-(acc=90,99)-4.8"><span class="toc-item-num">4.8&nbsp;&nbsp;</span>RL (acc=90,99)</a></span></li><li><span><a href="#RL-(acc=100,100)" data-toc-modified-id="RL-(acc=100,100)-4.9"><span class="toc-item-num">4.9&nbsp;&nbsp;</span>RL (acc=100,100)</a></span></li></ul></li><li><span><a href="#Plots" data-toc-modified-id="Plots-5"><span class="toc-item-num">5&nbsp;&nbsp;</span>Plots</a></span><ul class="toc-item"><li><span><a href="#Style" data-toc-modified-id="Style-5.1"><span class="toc-item-num">5.1&nbsp;&nbsp;</span>Style</a></span></li><li><span><a href="#Fleet-Utilization" data-toc-modified-id="Fleet-Utilization-5.2"><span class="toc-item-num">5.2&nbsp;&nbsp;</span>Fleet Utilization</a></span></li></ul></li></ul></div>

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

from evsim.data import load


# In[3]:


pd.set_option('display.float_format', '{:.4f}'.format)

start = "2016-06-01"
end = "2018-01-01"


def market_price(df):
    p_ind = 0.15
    charged_regular = df["charged_regular_kwh"]
    
    charged_vpp = df["charged_vpp_kwh"]
    profit = df["profit_eur"]
    
    regular_costs = p_ind * charged_vpp
    market_costs = regular_costs - profit
    market_price = market_costs / charged_vpp
    average_price = ((market_price * charged_vpp) + (p_ind * charged_regular)) / (charged_vpp + charged_regular)
    return(average_price)


def read_results(path):
    df = pd.read_csv(path)
    df["timestamp"] = df["timestamp"].apply(lambda x : datetime.fromtimestamp(x))
    df = df.set_index("timestamp") 
    if "profit_eur" in df.columns:
        df["profit_eur"] = df["profit_eur"] - df["lost_rentals_eur"]
    df = df[start:end]
    return df
    
    
def summarize_results(path):
    df = read_results(path)
    df_result = df.sum() / 1000
    df_result["market_price"] = market_price(df).replace([np.inf, -np.inf], np.nan).mean()
    
    if "risk_bal" in df.columns:
        df_result["risk_bal"] = df["risk_bal"].mean()
        df_result["risk_intr"] = df["risk_intr"].mean()
    return df_result


# ## Regular Profit

# In[4]:


df_car2go = pd.read_pickle("../data/processed/trips_big.pkl")
df_car2go["end_time"] = df_car2go["end_time"].apply(lambda x : datetime.fromtimestamp(x))
df_car2go = df_car2go.set_index("end_time")
df_car2go = df_car2go[start:end]
df_car2go["trip_price"].sum()/1000


# ## Charging Stations

# In[5]:


df_c = df_car2go.loc[df_car2go["end_charging"] == 1, ["end_lat", "end_lon"]].round(3)
df_c["stations"] = df_c["end_lat"].astype(str) + ";" + df_c["end_lon"].astype(str)
len(df_c["stations"].unique())


# # Baseline Charging

# In[6]:


df = summarize_results("../results/baseline.csv")
df


# # Intraday

# ## Benchmark

# In[7]:


df_b = summarize_results("../results/intraday-benchmark.csv")
df_b


# ## Risk Averse (r=0.3, acc=90)

# In[8]:


df_i = summarize_results("../results/intraday-risk-averse.csv")
profit_intr = df_i["profit_eur"]
df_i


# # Balancing

# ## Benchmark

# In[9]:


df_b = summarize_results("../results/balancing-benchmark.csv")
df_b


# ## Risk Averse (r=0.5, acc=70)

# In[10]:


df_b = summarize_results("../results/balancing-risk-averse.csv")
profit_bal = df_b["profit_eur"]
df_b


# # Integrated

# ## 100% Benchmark

# In[11]:


df_in = summarize_results("../results/integrated-benchmark.csv")
df_in


# ## 70,90 Benchmark

# In[12]:


df_in = summarize_results("../results/integrated-benchmark-acc-1.csv")
profit_bench = df_in["profit_eur"]
df_in


# ## Risk Averse (r=0.5,0.3, acc=70,90)

# In[13]:


df_in = summarize_results("../results/integrated-risk-averse.csv")
profit_in = df_in["profit_eur"]
df_in


# ## Risk Seeking (r=0.2,0.00, acc=70,90)

# In[14]:


summarize_results("../results/integrated-risk-seeking.csv")


# ## RL (acc=50,60)

# In[15]:


df_rl = summarize_results("../results/accuracy/DDDQN-50-60_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# In[16]:


df_rl = summarize_results("../results/accuracy/DDDQN-60-75_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# ## RL (acc=70,90)

# In[17]:


df_rl = summarize_results("../results/accuracy/DDDQN-70-90_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# ## RL (acc=80,95)

# In[18]:


df_rl = summarize_results("../results/accuracy/DDDQN-80-95_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# ## RL (acc=90,99)

# In[19]:


df_rl = summarize_results("../results/accuracy/DDDQN-90-99_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# ## RL (acc=100,100)

# In[20]:


df_rl = summarize_results("../results/accuracy/DDDQN-100-100_result.csv")
print(df_rl)
profit_rl = df_rl["profit_eur"]
print("Risk factors - Balancing: {:.2f}. Intraday:{:.2f}".format(df_rl["risk_bal"], df_rl["risk_intr"]))
print("Profit comparison - Balancing: {:+.0%}, Intraday: {:+.0%}, Integrated: {:+.0%}, , Benchmark: {:+.0%}".format(
            profit_rl / profit_bal,
            profit_rl / profit_intr,
            profit_rl / profit_in,
            profit_rl / profit_bench
            ))


# # Plots

# ## Style

# In[21]:


sns.set(rc={'figure.figsize':(10,6)})
sns.set_context("paper", font_scale=1.3, rc={"lines.linewidth": 1.5, "lines.markersize": 7})

sns.set_style("white")
sns.set_style("ticks")

palette = sns.cubehelix_palette(5, start=.5, rot=-.75, reverse=True)
sns.set_palette(palette)

sns.palplot(palette)


# ## Fleet Utilization

# In[22]:


df_stats = read_results("../results/stats-baseline.csv")

print(df_stats.describe())

df_stats = df_stats[["available_evs", "charging_evs", "vpp_evs"]]
df_stats.columns = ["Available", "Connected", "VPP"]

x = "Hour"
value_name = "Number EVs"
var_name = "Status"

df_stats[x] = df_stats.index.hour
df_stats = pd.melt(df_stats, id_vars=x, var_name=var_name, value_name=value_name) 

sns.set_palette(sns.cubehelix_palette(4, start=.5, rot=-.75, reverse=True))
sns.lineplot(x=x, y=value_name, hue=var_name, style=var_name, ci="sd", markers=False, data=df_stats)

sns.despine(offset=10)
plt.xticks(np.arange(0, 24, 2));
plt.yticks(np.arange(0, 500, 50));


# In[ ]:




