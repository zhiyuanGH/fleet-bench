import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Function to convert RTT to integer
def convert_to_int(rtt_str):
    return int(rtt_str.strip('ms'))

# Function to convert string time to seconds
def convert_to_seconds(time_str):
    m, s = time_str.split('m')
    s = s.strip('s')
    return int(m) * 60 + float(s)

# Read all CSV files
df_metrics_stargz = pd.read_csv("metrics_sum_stargz_200bw_fleetbench.csv")
df_metrics_fleet = pd.read_csv("metrics_sum_fleet_200bw_fleetbench.csv")

df_prov_stargz = pd.read_csv("provisioning_times_stargz_200bw_fleetbench.csv")
df_prov_fleet = pd.read_csv("provisioning_times_fleet_200bw_fleetbench.csv")
df_prov_legacy = pd.read_csv("provisioning_times_overlayfs_200bw_fleetbench.csv")

selected_containers = ['mariadb', 'ghost', 'wordpress','pytorch','tensorflow']
plt.rcParams['axes.labelsize'] = 16  # Font size for x and y labels
plt.rcParams['axes.titlesize'] = 16  # Font size for title
plt.rcParams['xtick.labelsize'] = 16 # Font size for x-tick labels
plt.rcParams['ytick.labelsize'] = 15 # Font size for y-tick labels

# Filter the data
df_metrics_stargz = df_metrics_stargz[df_metrics_stargz['Container'].isin(selected_containers)]
df_metrics_fleet = df_metrics_fleet[df_metrics_fleet['Container'].isin(selected_containers)]
df_prov_stargz = df_prov_stargz[df_prov_stargz['Container'].isin(selected_containers)]
df_prov_fleet = df_prov_fleet[df_prov_fleet['Container'].isin(selected_containers)]
df_prov_legacy = df_prov_legacy[df_prov_legacy['Container'].isin(selected_containers)]


# Convert RTT column to integer
df_metrics_stargz['RTT'] = df_metrics_stargz['RTT'].apply(convert_to_int)
df_metrics_fleet['RTT'] = df_metrics_fleet['RTT'].apply(convert_to_int)

df_prov_stargz['RTT'] = df_prov_stargz['RTT'].apply(convert_to_int)
df_prov_fleet['RTT'] = df_prov_fleet['RTT'].apply(convert_to_int)
df_prov_legacy['RTT'] = df_prov_legacy['RTT'].apply(convert_to_int)

# Convert Time column to seconds for both datasets
df_prov_stargz['Time'] = df_prov_stargz['Time'].apply(convert_to_seconds)
df_prov_fleet['Time'] = df_prov_fleet['Time'].apply(convert_to_seconds)
df_prov_legacy['Time'] = df_prov_legacy['Time'].apply(convert_to_seconds)

# Group by Container and RTT, then calculate mean Metrics Sum
grouped_metrics_stargz = df_metrics_stargz.groupby(['Container', 'RTT'])['Metrics Sum'].mean().reset_index()
grouped_metrics_fleet = df_metrics_fleet.groupby(['Container', 'RTT'])['Metrics Sum'].mean().reset_index()

# Group by Container and RTT, then calculate mean Time for both datasets
grouped_prov_stargz = df_prov_stargz.groupby(['Container', 'RTT'])['Time'].mean().reset_index()
grouped_prov_fleet = df_prov_fleet.groupby(['Container', 'RTT'])['Time'].mean().reset_index()
grouped_prov_legacy = df_prov_legacy.groupby(['Container', 'RTT'])['Time'].mean().reset_index()

# Calculate Acceleration Rate
grouped_prov_stargz['Acceleration Rate'] = grouped_prov_legacy['Time'] / grouped_prov_stargz['Time']
grouped_prov_fleet['Acceleration Rate'] = grouped_prov_legacy['Time'] / grouped_prov_fleet['Time']
grouped_prov_legacy['Acceleration Rate'] = grouped_prov_legacy['Time'] / grouped_prov_legacy['Time']


# Get the unique container names 
containers = grouped_metrics_stargz['Container'].unique()

# Create subplots in a 3xN grid (3 rows, N columns) and adjust subplot height
fig, axs = plt.subplots(3, len(containers), figsize=(len(containers)*4, 10))

# Set common y-axis limits
ymin = 0
max_metrics_sum = max(grouped_metrics_stargz['Metrics Sum'].max(), grouped_metrics_fleet['Metrics Sum'].max())
ymax_time = grouped_prov_legacy['Time'].max()
ymax_time = np.ceil(df_prov_legacy['Time'].max())  # round up to the nearest integer
ymax_time*= 1.1
min_provisioning_time = min(df_prov_stargz['Time'].min(), df_prov_fleet['Time'].min(), df_prov_legacy['Time'].min())
max_provisioning_time = max(df_prov_stargz['Time'].max(), df_prov_fleet['Time'].max(), df_prov_legacy['Time'].max())
max_provisioning_time*=1.1
ymax_rate = max(grouped_prov_stargz['Acceleration Rate'].max(), grouped_prov_fleet['Acceleration Rate'].max())
ymax_rate*=1.1

colors = ['#0080ff', '#FFA500', 'g']
markers = ['s', 'o', 'd']
labels = ['OverlayFS', 'eStargz', 'Fleet']

for i, container in enumerate(containers):
    # Filter data for the specific container
    data_metrics_stargz = grouped_metrics_stargz[grouped_metrics_stargz['Container'] == container]
    data_metrics_fleet = grouped_metrics_fleet[grouped_metrics_fleet['Container'] == container]
    data_prov_stargz = grouped_prov_stargz[grouped_prov_stargz['Container'] == container]
    data_prov_fleet = grouped_prov_fleet[grouped_prov_fleet['Container'] == container]
    data_prov_legacy = grouped_prov_legacy[grouped_prov_legacy['Container'] == container]

    # Plot data with line markers
    
 # Plot data with line markers
    axs[0,i].plot(data_prov_legacy['RTT'], data_prov_legacy['Time'], color=colors[0], marker=markers[0], label=labels[0], markeredgecolor='white', markeredgewidth=1)
    axs[0,i].plot(data_prov_stargz['RTT'], data_prov_stargz['Time'], color=colors[1], marker=markers[1], label=labels[1], markeredgecolor='white', markeredgewidth=1)
    axs[0,i].plot(data_prov_fleet['RTT'], data_prov_fleet['Time'], color=colors[2], marker=markers[2], label=labels[2], markeredgecolor='white', markeredgewidth=1)

    axs[0,i].set_yscale('log')  # Set y-axis to logarithmic scale
    

    axs[1,i].set_yscale('log')
    axs[1,i].plot(data_metrics_stargz['RTT'], data_metrics_stargz['Metrics Sum'], color=colors[1], marker=markers[1], label=labels[1], markeredgecolor='white', markeredgewidth=1)
    axs[1,i].plot(data_metrics_fleet['RTT'], data_metrics_fleet['Metrics Sum'], color=colors[2], marker=markers[2], label=labels[2], markeredgecolor='white', markeredgewidth=1)

    # Plot acceleration rate with bar chart
    # adjust as needed for your data
    width = 17  
    axs[2,i].bar(data_prov_stargz['RTT'] -width/2, data_prov_stargz['Acceleration Rate'], color=colors[1],width=width, align='edge')
    axs[2,i].bar(data_prov_fleet['RTT']+ width/2, data_prov_fleet['Acceleration Rate'], color=colors[2], width=width, align='edge')

    axs[0,i].set_title(container)
    axs[0,i].set_xlabel('RTT (ms)')
    axs[0,i].set_ylabel('Provisioning Time (s)')

    axs[1,i].set_xlabel('RTT (ms)')
    axs[1,i].set_ylabel('On-demand Fetch')

    axs[2,i].set_xlabel('RTT (ms)')
    axs[2,i].set_ylabel('Acceleration Rate')

    # Set y-axis limit
    # axs[0,i].set_ylim([ymin, ymax_time])
    axs[0,i].set_ylim([1, max_provisioning_time])
    axs[1,i].set_ylim([1, max_metrics_sum*1.1])

    axs[2,i].set_ylim([ymin, ymax_rate])

# Create a legend for the whole figure
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#0080ff', edgecolor='r', label='OverlayFS'),
                   Patch(facecolor='#FFA500', edgecolor='r', label='eStargz'),
                   Patch(facecolor='g', edgecolor='r', label='Fleet')]


max_width = max(ax.yaxis.get_ticklabel_extents(fig.canvas.get_renderer())[1].width for ax in axs.ravel())

for ax in axs.ravel():
    ax.yaxis.set_label_coords(-max_width / fig.dpi / fig.get_figwidth() -0.2, 0.5, transform=ax.transAxes)
# Place the legend higher position
fig.legend(handles=legend_elements, loc='lower center', ncol=len(legend_elements), bbox_to_anchor=(0.5, 0.06),fontsize=16)

# Adjust the layout to fit the legend and add space between subplots
plt.subplots_adjust(bottom=0.2, hspace=0.5, wspace=0.4)

# Save the figure in EPS format for publication
plt.savefig('Fleet5.png', format='png', bbox_inches='tight')

# Show the plot
plt.show()
