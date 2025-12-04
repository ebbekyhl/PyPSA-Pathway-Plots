import matplotlib.pyplot as plt
import json
import plotly.express as px
import plotly.graph_objects as go
import pypsa
import geopandas as gpd
import pandas as pd
import numpy as np
import cartopy.crs as ccrs
import re
import warnings
warnings.filterwarnings("ignore")

fs = 13
plt.rcParams['axes.labelsize'] = fs
plt.rcParams['xtick.labelsize'] = fs
plt.rcParams['ytick.labelsize'] = fs
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['ytick.direction'] = 'out'
plt.rcParams['axes.axisbelow'] = True
plt.rcParams['legend.title_fontsize'] = fs
plt.rcParams['legend.fontsize'] = fs

country = "GB"

simple_names_dict= {'GBM': 'GB scotland',
                    'GBD': 'GB north west',
                    'GBC': 'GB north east yorkshire humber',
                    'GBE': 'GB north east yorkshire humber',
                    'GBF': 'GB east midland',
                    'GBG': 'GB west midland',
                    'GBH': 'GB east',
                    'GBJ1': 'GB central england',
                    'GBJ': 'GB south east',
                    'GBK': 'GB south west',
                    'GBL': 'GB wales cymru',
                    'GBI': 'GB greater london',
                    'GBN': 'GB north ireland'}

data_crs = ccrs.epsg(3035)

zmaxs = {
    "onshore wind": 50,
    "offshore wind": 30,
    "PV utility": 20,
    "PV rooftop": 20,
    "H2 Fuel Cells": 1,
    "co2 sequestered": 2500,
    "biomass CHP": 5,
    "nuclear": 5,
    "gas CHP": 5,
    "OCGT": 5,
    "CCGT": 5,
    "H2 underground store": 6000,
    "H2 overground store": 6000,
    "EV battery": 100,
    "H2 Electrolysis": 30,
    "H2 pipeline": 70,
    "air heat pump": 5,
    "ground heat pump": 5,
    "gas boiler": 15, 
    "biomass boiler": 5,
    "resistive heater": 5,
    "resistive heater": 5, 
    "solid biomass CHP": 5,
    "methanol CHP": 5,
    "rural resistive heater": 5,
    "methanol": 2500,
    "methanol steam reforming": 5,
    "methanolisation": 5,
    "Fischer-Tropsch": 5,
    "TES central": 100,
    "TES decentral": 100,
    }

units = {
    "solar rooftop": "GW",
    "onshore wind": "GW",
    "offshore wind": "GW",
    "PV utility": "GW",
    "co2 sequestered": "ktCO2"
    # etc...
}

def make_hovertemplate(v, unit):
    # 1 decimal + enhed i hover
    return (
        "<b>%{customdata}</b><br>"
        f"{v}: %{{z:.1f}} {unit}"
        "<extra></extra>"
    )

import yaml

with open('plotting.yaml') as file:
    config_i = yaml.safe_load(file)
config_plotting = config_i["plotting"]
tech_colors = config_plotting["tech_colors"]

tech_colors["methanol"] = "mediumspringgreen"
tech_colors["renewables"] = "#DDEC354F"
tech_colors["gas CHP"] = tech_colors["urban central gas CHP"]
tech_colors["gas CHP CC"] = tech_colors["urban central gas CHP CC"]
tech_colors["solid biomass CHP"] = tech_colors["urban central solid biomass CHP"]
tech_colors["solid biomass CHP CC"] = tech_colors["urban central solid biomass CHP CC"]
tech_colors["methanol CHP"] = tech_colors["urban central methanol CHP"]
tech_colors["methanol CHP CC"] = tech_colors["urban central methanol CHP CC"]
tech_colors["imports"] = "#94073d"
tech_colors["exports"] = "#e06796"
tech_colors["biomass to liquid CC"] = tech_colors["biomass to liquid"]
tech_colors["CCUS"] = tech_colors["CO2 sequestration"]
tech_colors["urban central biogas CHP"] = "olive"
tech_colors['TES central discharger'] = "#FFA500"  # orange
tech_colors['TES decentral discharger'] = "#FF8C00"  # dark orange
tech_colors["electrolytic H2"] = tech_colors["H2"]
tech_colors['heating'] = tech_colors["ground heat pump"]
tech_colors['residential heating'] = tech_colors["air heat pump"]
tech_colors["land transport"] = tech_colors["EV battery"]
tech_colors['residential electricity'] = "#a2a2a2"
tech_colors['industry electricity'] = "#3f4b38"
tech_colors['agriculture electricity'] = "#521010"
tech_colors['CCUS'] = "#ff002b"
tech_colors["urban decentral heat"] = "#ca9c92"
tech_colors["rural heat"] = "#C30202"
tech_colors['electrified heating (urban central)'] = tech_colors["urban central heat"]
tech_colors['electrified heating (urban decentral)'] = tech_colors["urban decentral heat"]
tech_colors['electrified heating (rural)'] = tech_colors["rural heat"] 
tech_colors["agriculture heat"] = "#B4B4B4"  # saddle brown
tech_colors["low-temperature heat for industry"] = "#656565"  # peru
tech_colors["medium heat for industry"] = "#291F1A"  # sienna
tech_colors["high heat for industry"] = "#000000"  # chocolate

preferred_order_demand = pd.Index(['residential electricity',
                                    'industry electricity',
                                    'agriculture electricity',
                                    'electrified heating (urban central)',
                                    'electrified heating (urban decentral)',
                                    'electrified heating (rural)',
                                    'land transport',
                                    'ammonia', 
                                    'CCUS', 
                                    'electrolytic H2',
                                    ])

preferred_order_heating = pd.Index([
                                     'air heat pump',
                                     'ground heat pump',
                                     'resistive heater',
                                     'gas boiler', 
                                     'gas for industry heat',    
                                     'gas for industry heat CC',                                  
                                     'solid biomass CHP',
                                     'solid biomass for industry heat', 
                                     'solid biomass for industry heat CC', 
                                     "biomass boiler",
                                     'oil boiler',
                                     "H2 Electrolysis",
                                     "H2 Fuel Cell",
                                     'TES central discharger', 
                                     'TES decentral discharger', 
                                    ])

preferred_order = pd.Index(
    [
        "renewables",
        "wind",
        "onwind",
        "offwind",
        "offwind-ac",
        "offwind-dc",
        "onshore wind",
        "offshore wind",
        "offshore wind (AC)",
        "offshore wind (DC)",
        "solar PV",
        "solar thermal",
        "solar rooftop",
        "solar",
        "hydro",
        "ror",
        "solid biomass",
        "biogas",
        "transmission lines",
        "hydroelectricity",
        "hydro reservoir",
        "run of river",
        "pumped hydro storage",
        "nuclear",
        "OCGT",
        "CCGT",
        "battery storage",
        "BEV charger",
        "building retrofitting",
        "H2",
        "H2 Electrolysis",
        "H2 Store",
        "H2 pipeline", 
        "SMR",
        "SMR-CC",
        "import H2",
        "H2 turbine",
        "methanation",
        "ammonia",
        "ground heat pump",
        "air heat pump",
        "heat pump",
        "resistive heater",
        "hot water storage",
        "power-to-heat",
        "gas-to-power/heat",
        "gas boiler",
        "gas",
        "natural gas",
        "CHP",
        "power-to-gas",
        "power-to-liquid",
        "battery storage",
        "hot water storage",
        "CO2 sequestration",
    ]
)

def calculate_endogenous_demand(n):
    
    links_wo_transmission = n.links.drop(n.links.query("carrier == 'DC'").index)
    
    electricity_buses = list(n.buses.query('carrier == "AC"').index) + list(
        n.buses.query('carrier == "low voltage"').index
    )

    boolean_elec_demand_via_links = [
        links_wo_transmission.bus0[i] in electricity_buses
        for i in range(len(links_wo_transmission.bus0))
    ]
    
    boolean_elec_demand_via_links_series = pd.Series(boolean_elec_demand_via_links)
    
    elec_demand_via_links = links_wo_transmission.iloc[
        boolean_elec_demand_via_links_series[boolean_elec_demand_via_links_series].index
    ]
    
    # Drop batteries
    elec_demand_via_links = elec_demand_via_links.drop(
        elec_demand_via_links.index[elec_demand_via_links.index.str.contains("battery")]
    )

    # Drop distribution links
    elec_demand_via_links = elec_demand_via_links.drop(
        elec_demand_via_links.index[
            elec_demand_via_links.index.str.contains("distribution")
        ]
    )

    endogenous_demand = n.links_t.p0[elec_demand_via_links.index]

    return endogenous_demand

def calculate_demand_by_sector(n):
    ###############
    end_demand = calculate_endogenous_demand(n)
    end_demand = end_demand.T.groupby([n.links.loc[end_demand.columns].bus1.str.replace(" low voltage", ""),
                                        n.links.loc[end_demand.columns].carrier]).sum().sum(axis=1)
    end_demand_UK = end_demand.loc[end_demand.index.get_level_values(0).str.contains(country)]
    end_demand_UK = pd.DataFrame(end_demand_UK)
    end_demand_UK["bus1"] = end_demand_UK.index.get_level_values(0).str.replace("GB central england ", "").str.replace("GB north west ", "").str.replace("GB south east ", "").str.replace("GB south west ", "").str.replace("GB wales cymru ", "").str.replace("GB scotland ", "").str.replace("GB north east yorkshire humber ", "").str.replace("GB west midland ", "").str.replace("GB east midland ", "").str.replace("GB greater london ", "").str.replace("GB north ireland 0 ", "").str.replace("GB east ", "")

    end_demand_UK.set_index([end_demand_UK.index.get_level_values(1), 
                                                end_demand_UK["bus1"]], inplace=True)
    end_demand_UK = end_demand_UK.drop(columns=["bus1"]).groupby(level=[0,1]).sum().reset_index()
    end_demand_UK_heating = end_demand_UK.loc[end_demand_UK.bus1.str.contains("heat")]
    end_demand_UK_heating = end_demand_UK_heating.drop(index = end_demand_UK_heating.query("carrier == 'DAC'").index)
    end_demand_UK_heating["carrier"] = end_demand_UK_heating["bus1"]

    end_demand_UK.loc[end_demand_UK_heating.index, :] = end_demand_UK_heating.values
    end_demand_UK = end_demand_UK.set_index("bus1").drop(columns="carrier")
    #############
    exo_demand = n.loads_t.p[n.loads.carrier[n.loads.carrier.str.contains("electricity")].index]
    exo_demand = exo_demand.T.groupby([n.loads.loc[exo_demand.columns].bus.str.replace(" low voltage", ""),
                                    n.loads.loc[exo_demand.columns].carrier]).sum().sum(axis=1).unstack()
    exo_demand_UK = exo_demand.loc[exo_demand.index.str.contains(country)].sum()

    demand_by_sector = pd.concat([end_demand_UK, exo_demand_UK])

    demand_by_sector.rename(index = {"EV battery": "land transport",
                                    "DAC": "CCUS",
                                    "agriculture electricity": "industry electricity",
                                    "H2": "electrolytic H2",
                                    "Haber-Bosch": "ammonia",
                                    "electricity": "residential electricity",
                                    "rural heat": 'electrified heating (rural)', 
                                    "urban central heat": 'electrified heating (urban central)',
                                    "urban decentral heat": 'electrified heating (urban decentral)',
                                    }, inplace=True)

    demand_by_sector = demand_by_sector.groupby(demand_by_sector.index).sum()

    return demand_by_sector[0]

def calculate_heating_demand_by_sector(n):
    heat_loads = n.loads.loc[n.loads.index.str.contains("heat")]
    heat_loads_UK = heat_loads.loc[heat_loads.index.str.contains(country)]
    heat_loads_UK_by_sector = n.loads_t.p[heat_loads_UK.index].T.groupby(heat_loads_UK.carrier).sum().sum(axis=1)

    return heat_loads_UK_by_sector

def add_year_label(regions_dict, years, scen):
    regions = regions_dict[f"{scen}-2025"][["country", "parent", "contains", "substations", "geometry"]]

    for year in years:
        regions_y = regions_dict[f"{scen}-{year}"]
        regions_to_plot = regions_y.drop(columns = ["country", "parent", "contains", "substations", "geometry"])
        regions_to_plot.columns = regions_to_plot.columns + f" ({year})"

        regions.loc[regions_to_plot.index, regions_to_plot.columns] = regions_to_plot

    regions = regions.reset_index()
    regions = regions.to_crs(epsg=4326)
    regions_geojson = json.loads(regions.to_json())

    return regions, regions_geojson

def calculate_capacities_at_regions(n, techs, mapping = False, admin_shapes_path = "data/admin_shapes.geojson"):
    carriers_dict = {"onshore wind": "onwind",
                 "offshore wind": "offwind-ac",
                 "PV utility": "solar",
                 "PV rooftop": "solar rooftop",}

    renewables = ["onshore wind", 
                "PV rooftop",
                "offshore wind",
                "PV utility"]

    # update specs for stores and links
    stores = n.stores.copy()
    links = n.links.copy()

    # split H2 stores into underground and overground
    h2_stores = stores.query("carrier == 'H2 Store'")
    h2_stores_underground = h2_stores.loc[h2_stores.capital_cost <= 200]
    h2_stores_overground = h2_stores.loc[h2_stores.capital_cost > 200]
    stores.loc[h2_stores_underground.index, "carrier"] = "H2 underground store"
    stores.loc[h2_stores_overground.index, "carrier"] = "H2 overground store"

    # group water tanks and water pits 
    urban_central_water = stores.loc[stores.carrier.isin(['urban central water tanks', 'urban central water pits'])]
    decentral_water = stores.loc[stores.carrier.isin(['rural water tanks', 'urban decentral water tanks'])]
    stores.loc[urban_central_water.index, "carrier"] = "TES central"
    stores.loc[decentral_water.index, "carrier"] = "TES decentral"

    urban_central_water_links = links.loc[links.carrier.str.contains("urban central water tanks discharger|water pits discharger")]
    decentral_water_links = links.loc[links.carrier.str.contains("rural water tanks discharger|urban decentral water tanks discharger")]
    links.loc[urban_central_water_links.index, "carrier"] = "TES central discharger"
    links.loc[decentral_water_links.index, "carrier"] = "TES decentral discharger"

    urban_central_water_links_charge = links.loc[links.carrier.str.contains("urban central water tanks charger")]
    decentral_water_links_charge = links.loc[links.carrier.str.contains("rural water tanks charger|urban decentral water tanks charger")]
    links.loc[urban_central_water_links_charge.index, "carrier"] = "TES central charger"
    links.loc[decentral_water_links_charge.index, "carrier"] = "TES decentral charger"

    # remove prefix from CHP unit names
    heat_links_bus1 = links.loc[links.bus1.str.contains("heat")]
    heat_links_bus2 = links.loc[links.bus2.str.contains("heat")]

    links.loc[heat_links_bus1.index, "carrier"] = heat_links_bus1.carrier.str.replace(r'^(urban|rural) (central|decentral) ', '', regex=True)
    links.loc[heat_links_bus2.index, "carrier"] = heat_links_bus2.carrier.str.replace(r'^(urban|rural) (central|decentral) ', '', regex=True)

    n.stores = stores
    n.links = links

    regions =  gpd.read_file(admin_shapes_path)
    if mapping:
        regions.set_index("name", inplace=True)
        regions = regions.rename(index = {"GB north ireland": "GB north ireland 0"})
    else:
        regions = regions.rename(columns = {"admin": "name"})
        regions.set_index("name", inplace=True)
        regions = regions.rename(index = {"GBN0B+1": "GBN 0"})
        regions = regions.loc[regions.index.str.contains(country)]

    regions = regions.to_crs(data_crs)

    uk_buses = n.buses.query("carrier == 'AC'").query(f"country == '{country}'").index
    unit = "GW"

    links = n.links
    links_uk = links.loc[links.index.str.contains(country)]
    links_capacity = links_uk.p_nom_opt*links_uk.efficiency

    stores = n.stores
    stores_uk = stores.loc[stores.index.str.contains(country)]
    stores_capacity = stores_uk.e_nom_opt

    conversion = 1/(1e3) if unit == "GW" else 1

    for tech in techs:

        if tech in ["battery", "H2", "methanol", 
                    'co2 sequestered', 'ammonia', 
                    "TES central", "TES decentral"]:

            stores_capacity_tech = stores_capacity.groupby([stores_uk.bus, 
                                                            stores_uk.carrier
                                                            ]).sum().unstack()

            stores_capacity_tech = stores_capacity_tech.T.loc[stores_capacity_tech.columns.str.contains(tech)].T.unstack().dropna()

            index_bus = stores_capacity_tech.loc[stores_capacity_tech.index.get_level_values(1).str.contains(country)].reset_index()

            for i in range(len(index_bus)):
                match_bus = next((name for name in regions.index if name in index_bus["bus"].iloc[i]), None)
                index_bus.loc[i, "bus"] = match_bus

            capacities_by_bus = index_bus.groupby(index_bus.index).sum()
            capacities_by_bus.set_index("bus", inplace=True)
            capacities_by_bus.set_index([capacities_by_bus.index,"carrier"], drop=True, inplace = True)
            capacities_by_bus = pd.DataFrame(capacities_by_bus[0].groupby(level=[0,1]).sum())
            capacities_by_bus = capacities_by_bus[0].unstack()

            if len(capacities_by_bus.columns) == 0:
                continue
            elif len(capacities_by_bus.columns) > 1:
                for col in capacities_by_bus.columns:
                    regions.loc[capacities_by_bus.index, col] = capacities_by_bus * conversion
            else:
                try:
                    regions.loc[capacities_by_bus.index, tech] = capacities_by_bus[capacities_by_bus.columns[0]] * conversion
                except:
                    print("error assigning store capacities to regions ", tech, capacities_by_bus)
        
        elif tech not in renewables:

            links_capacity_tech = links_capacity.groupby([links_uk.bus0, 
                                                            links_uk.bus1, 
                                                            links_uk.carrier]).sum().unstack()

            links_capacity_tech = links_capacity_tech.T.loc[links_capacity_tech.columns.str.contains(tech)].T.reset_index().fillna(0)

            index_bus0 = links_capacity_tech.loc[links_capacity_tech["bus0"].str.contains(country)].reset_index()
            index_bus1 = links_capacity_tech.loc[links_capacity_tech["bus1"].str.contains(country)].reset_index()

            # ensure no overlapping indices
            index_bus1 = index_bus1.loc[~index_bus1["index"].isin(index_bus0["index"])]
            
            for i in range(len(index_bus0)):
                match_bus0 = next((name for name in regions.index if name in index_bus0["bus0"].iloc[i]), None)
                index_bus0.loc[i, "bus"] = match_bus0

            if len(index_bus0) == 0 and len(index_bus1) == 0:
                continue

            if len(index_bus1) > 0:
                for i in range(len(index_bus1)):
                    match_bus1 = next((name for name in regions.index if name in index_bus1["bus1"].iloc[i]), None)
                    index_bus1.loc[i, "bus"] = match_bus1

                index_bus = pd.concat([index_bus0, index_bus1], ignore_index=True).drop(columns=["bus0", "bus1", "index"]).set_index("bus")
            
            else:
                index_bus = index_bus0.drop(columns=["bus0", "bus1", "index"]).set_index("bus")

            capacities_by_bus = index_bus.groupby(index_bus.index).sum()

            if len(capacities_by_bus.columns) == 0:
                continue
            elif len(capacities_by_bus.columns) > 1:
                for col in capacities_by_bus.columns:
                    regions.loc[capacities_by_bus.index, col] = capacities_by_bus * conversion
            else:
                try:
                    regions.loc[capacities_by_bus.index, tech] = capacities_by_bus[capacities_by_bus.columns[0]] * conversion
                except:
                    print("error assigning link capacities to regions ", tech, capacities_by_bus)             
        else:
            carrier = carriers_dict[tech]
            if tech in ["onshore wind", "PV rooftop"]:
                n_tech = n.generators.query("carrier == @carrier")
            elif tech == "PV utility":
                n_tech = n.generators.query("carrier == 'solar'")
            elif tech == "offshore wind":
                n_tech = n.generators.query("carrier == 'offwind-ac' or carrier == 'offwind-dc'")
            else:
                print("technology not recognized: ", tech)
                continue

            if tech == "PV rooftop":
                uk_tech = n_tech[n_tech.bus.isin(uk_buses + " low voltage")].set_index("bus")
            else:
                uk_tech = n_tech[n_tech.bus.isin(uk_buses)].set_index("bus")

            uk_tech_by_region = uk_tech.groupby(uk_tech.index).sum()
            if tech == "PV rooftop":
                uk_tech_by_region.index = uk_tech_by_region.index.str.split(" low voltage", expand = True).get_level_values(0)
            
            regions.loc[uk_tech_by_region.index, tech] = uk_tech_by_region["p_nom_opt"] * conversion

    regions = regions.rename(index = {"GB north ireland 0": "GB north ireland"})

    return regions

def add_to_regions(df, mapping = False, admin_shapes_path = "data/admin_shapes.geojson"):

    regions =  gpd.read_file(admin_shapes_path)
    if mapping:
        regions.set_index("name", inplace=True)
        regions = regions.rename(index = {"GB north ireland": "GB north ireland 0"})
    else:
        regions = regions.rename(columns = {"admin": "name"})
        regions.set_index("name", inplace=True)
        regions = regions.rename(index = {"GBN0B+1": "GBN 0"})
        regions = regions.loc[regions.index.str.contains(country)]

    regions = regions.to_crs(data_crs)

    regions.loc[:, df.columns] = df
    return regions

def calculate_generation_mix(n):

    # HV buses
    buses = n.buses.query("carrier == 'AC'").index # high voltage buses
    AC_generators = [x for x in n.generators.index if n.generators.loc[x].bus in buses] # high voltage generators
    links = n.links.copy() # every link in the network
    links = links.drop(links.query("carrier == 'DC'").index) # without DC transmission lines

    electricity_generation_links = [x for x in links.index if links.loc[x].bus1 in buses] # electricity generation links

    # LV buses
    buses_lv = n.buses.query("carrier == 'low voltage'").index # low voltage buses
    lv_generators = [x for x in n.generators.index if n.generators.loc[x].bus in buses_lv] # low voltage generators

    # initialize dataframe
    df_1 = n.generators_t.p[AC_generators].sum().groupby([n.generators.loc[AC_generators].bus, n.generators.loc[AC_generators].carrier]).sum()

    df_2 = n.generators_t.p[lv_generators].sum().groupby([n.generators.loc[lv_generators].bus.str.replace(" low voltage", ""), n.generators.loc[lv_generators].carrier]).sum()

    df_3 = -n.links_t.p1[electricity_generation_links].sum().groupby([n.links.loc[electricity_generation_links].bus1, n.links.loc[electricity_generation_links].carrier]).sum()
    df_3.drop(index = df_3.loc[df_3.index.get_level_values(1).str.contains("discharge")].index, inplace=True)
    df_3.drop(index = df_3.loc[df_3.index.get_level_values(1).str.contains("Fuel Cell")].index, inplace=True)
    df_3.drop(index = df_3.loc[df_3.index.get_level_values(1).str.contains("electricity distribution grid")].index, inplace=True)
    
    df_4 = n.storage_units_t.p[n.storage_units.query("carrier == 'hydro'").index].sum().groupby([n.storage_units.loc[n.storage_units.query("carrier == 'hydro'").index].bus, n.storage_units.loc[n.storage_units.query("carrier == 'hydro'").index].carrier]).sum()

    # # aggregated by technology (for every hour)
    df = pd.concat([df_1, df_2, df_3, df_4], axis=0).sort_index()

    # only use GB nodes
    df = df.loc[df.index.get_level_values(0).str.contains(country)]

    return df

def calculate_heating_generation_mix(n):
    heating_buses = n.buses.loc[n.buses.carrier.str.contains("heat")].index

    heating_links_p1 = n.links.loc[n.links.bus1.isin(heating_buses)]
    heating_links_p2 = n.links.loc[n.links.bus2.isin(heating_buses)]

    heating_links_p1["bus"] = heating_links_p1["bus1"].str.replace("urban central heat", "").str.replace("medium heat for industry", "").str.replace("high heat for industry", "").str.replace("agriculture heat", "").str.replace("rural heat", "").str.replace("urban decentral heat", "").str.strip()
    heating_links_p2["bus"] = heating_links_p2["bus2"].str.replace("urban central heat", "").str.replace("medium heat for industry", "").str.replace("high heat for industry", "").str.replace("agriculture heat", "").str.replace("rural heat", "").str.replace("urban decentral heat", "").str.strip()

    heating_generation_p1 = -n.links_t.p1[heating_links_p1.index].T.groupby([heating_links_p1.carrier, 
                                                                            heating_links_p1.bus]).sum().T

    heating_generation_p1 = heating_generation_p1.T.swaplevel(0,1).sum(axis=1).unstack()

    heating_generation_p2 = -n.links_t.p2[heating_links_p2.index].T.groupby([heating_links_p2.carrier,
                                                                            heating_links_p2.bus]).sum().T

    heating_generation_p2 = heating_generation_p2.T.swaplevel(0,1).sum(axis=1).unstack()

    heating_generation = heating_generation_p1.copy()
    heating_generation.loc[:, heating_generation_p2.columns] = heating_generation_p2

    # get UK elements
    heating_generation_uk = heating_generation.loc[heating_generation.index.str.contains(country)]

    return heating_generation_uk

def calculate_electricity_demand(n):
    end_demand = calculate_endogenous_demand(n)
    end_demand = end_demand.T.groupby(n.links.loc[end_demand.columns].bus0.str.replace(" low voltage", "")).sum()
    end_demand = end_demand.groupby(end_demand.index).sum().T

    exo_demand = n.loads_t.p[n.loads.carrier[n.loads.carrier.str.contains("electricity")].index]
    exo_demand = exo_demand.T.groupby(n.loads.loc[n.loads.carrier.str.contains("electricity")].bus.str.replace(" low voltage", "")).sum()
    exo_demand = exo_demand.groupby(exo_demand.index).sum().T

    nodal_demand = end_demand + exo_demand

    # only use GB nodes
    nodal_demand = nodal_demand.loc[:, nodal_demand.columns.str.contains(country)].T
    
    return nodal_demand

def calculate_heating_demand(n):
    exo_demand = n.loads_t.p[n.loads.carrier[n.loads.carrier.str.contains("heat")].index]
    exo_demand_bus = n.loads.loc[n.loads.carrier.str.contains("heat")].bus.str.replace("urban central heat", "").str.replace("medium heat for industry", "").str.replace("high heat for industry", "").str.replace("agriculture heat", "").str.replace("rural heat", "").str.replace("urban decentral heat", "").str.strip()
    exo_demand = exo_demand.T.groupby(exo_demand_bus).sum()
    exo_demand = exo_demand.groupby(exo_demand.index).sum().T

    # only use GB nodes
    nodal_demand = exo_demand.loc[:, exo_demand.columns.str.contains(country)].T
    
    return nodal_demand

def make_interactive_map(token, capacity, filename, years, scen, n_mapping = False):
    regions, regions_geojson = add_year_label(capacity, years, scen)

    # --- 1. Find all numeric columns we want to plot ---
    value_cols = regions.drop(
        columns=['name', 'country', 'parent', 'contains', 'substations', 'geometry'],
        errors='ignore'
    )
    value_cols = value_cols.loc[:, value_cols.sum() > 0.1]
    all_cols = value_cols.columns.sort_values()

    # Expect column names like "Solar rooftop (2030)"
    col_pattern = re.compile(r"^(.*) \((\d{4})\)$")

    # Parse tech + year from column names
    mapping = {}          # (tech, year) -> column name
    techs = set()
    years = set()

    for col in all_cols:
        m = col_pattern.match(col)
        if not m:
            continue
        tech = m.group(1)
        year = int(m.group(2))
        mapping[(tech, year)] = col
        techs.add(tech)
        years.add(year)

    # print(mapping)

    techs = sorted(techs)
    years = sorted(years)

    # Initial tech + year
    tech0 = techs[0]
    year0 = years[0]

    # Choose default unit from filename
    if "storage" in filename:
        default_unit = "GWh"
        variable = "Capacity"
        variable_long = "Deployed capacity"
        zmaxs_to_use = zmaxs
    elif "demand" in filename:
        default_unit = "TWh"
        variable = "Demand"
        variable_long = "Electricity demand"
        zmaxs_to_use = zmaxs
    elif "share" in filename:
        default_unit = "%"
        variable = "Share"
        variable_long = "Generation share"
        zmaxs_to_use = {}
    else:
        default_unit = "GW"
        variable = "Capacity"
        variable_long = "Deployed capacity"
        zmaxs_to_use = zmaxs

    # unit0 = units.get(tech0, default_unit)
    unit0 = default_unit

    # using plotly.graph_objects to make a Choroplethmapbox 
    fig = go.Figure()

    # --- initial totals for year0, all techs ---
    totals_year0 = []
    for tech in techs:
        col0 = mapping.get((tech, year0))
        if col0 is None or col0 not in regions:
            tot = 0.0
        else:
            tot = regions[col0].sum()
        totals_year0.append(tot)

    # Build a nice text like "EV batteries: 10.2 GW; Onshore wind: 25.3 GW; ..."
    if "share" not in filename:
        totals_text_year0 = "<br>".join(
            f"{tech}: {tot:,.1f} {units.get(tech, default_unit)}"
            for tech, tot in zip(techs, totals_year0)
        )
    else:
        totals_text_year0 = ""

    initial_annotation = [
                            dict(
                                x=0.97, y=0.975, xref="paper", yref="paper",
                                text=f"UK totals {year0}:<br>{totals_text_year0}",
                                showarrow=False,
                                font=dict(size=14, color="gray"),
                                align="right",
                                bgcolor=None, #"white",
                                bordercolor=None, #"gray",
                                borderwidth=1,
                                borderpad=4,
                            )
                        ]

    # --- 2. One trace per tech (dropdown toggles visibility) ---
    for i, tech in enumerate(techs):
        col_name = mapping.get((tech, year0))
        if col_name is None:
            z = [0.0] * len(regions)
        else:
            z = regions[col_name]

        
        if not "share" in filename:
            zmax = zmaxs_to_use.get(tech, None)
        else:
            zmax = 10

        # unit = units.get(tech, default_unit)
        unit = default_unit

        # cbar_title_input = f"{tech} ({unit})"
        cbar_title_input = f"{variable} ({unit})"

        if n_mapping:
            simple_names = regions["name"]
        else:
            simple_names = regions["name"].str[0:3].map(simple_names_dict)

        multiple_entries = simple_names.loc[simple_names.duplicated()].unique()

        for me in multiple_entries:
            series = simple_names[simple_names == me]
            no_entries = len(series)

            count = 0
            for j in series.index:
                simple_names.loc[j] = f"{me} ({count+1}/{no_entries})"
                count += 1

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=regions_geojson,
                locations=regions['name'],
                featureidkey="properties.name",
                z=z,
                colorscale="Blues",
                zmin=0,
                zmax=zmax,
                marker_opacity=0.5,
                marker_line_width=0,
                visible=(i == 0),  # only first tech visible initially
                # keep colorbar title constant over years for a given tech
                colorbar_title=cbar_title_input,
                customdata=simple_names,
                hovertemplate=make_hovertemplate(col_name or f"{tech} ({year0})", unit)
            )
        )

    # --- 3. Dropdown: choose technology (show/hide traces only) ---
    buttons = []
    for i, tech in enumerate(techs):
        # unit = units.get(tech, default_unit)
        unit = default_unit
        visibility = [False] * len(techs)
        visibility[i] = True

        col_name = mapping.get((tech, year0))
        if col_name not in regions:
            tot = 0.0
        else:
            tot = regions[col_name].sum()

        buttons.append(
            dict(
                label=tech,
                method="update",
                args=[
                    {"visible": visibility},
                    {#"annotations[0].text": f"Total {year0}: {tot:.1f} {unit}"
                    }
                ]
            )
        )

    # --- 4. Slider: choose year (restyle z + hovertemplate ONLY) ---
    slider_steps = []
    for year in years:
        z_list = []
        hover_list = []
        totals_this_year = []

        for tech in techs:
            col_name = mapping.get((tech, year))
            # unit = units.get(tech, default_unit)
            unit = default_unit

            if col_name is None:
                z = [0.0] * len(regions)
                tot = 0.0
            else:
                z = regions[col_name]
                tot = z.sum()

            z_list.append(z)
            hover_list.append(make_hovertemplate(col_name or f"{tech} ({year})", unit))
            totals_this_year.append(tot)

        # build totals string for this year
        if "share" not in filename:
            totals_text = "<br>".join(
                f"{tech}: {tot:,.1f} {units.get(tech, default_unit)}"
                for tech, tot in zip(techs, totals_this_year)
            )
        else:
            totals_text = ""

        slider_steps.append(
            dict(
                label=str(year),
                method="update",
                args=[
                    {   # trace updates – one z per tech trace
                        "z": z_list,
                        "hovertemplate": hover_list,
                    },
                    {   # layout update – only the annotation text
                        "annotations[0].text": f"UK totals {year}:<br>{totals_text}"
                    },
                ]
            )
        )

    sliders = [
        dict(
            active=0,
            currentvalue={"prefix": "Year: "},
            pad={"t": 5},
            steps=slider_steps,
        )
    ]

    # --- 5. Layout + Mapbox config ---
    px.set_mapbox_access_token(token)

    fig.update_layout(
        autosize=False,  # <- freeze size so it doesn't re-autosize
        mapbox_accesstoken=token,
        mapbox_style="mapbox://styles/mapbox/light-v11",
        mapbox_zoom=4.5,
        mapbox_center={"lat": 54.5, "lon": -3.4360},
        
        updatemenus=[dict(
            buttons=buttons,
            direction="down",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            bgcolor="white",
            showactive=True
            )],

        annotations=initial_annotation,
        
        sliders=sliders,
        uirevision="keep-zoom",
        width=700,
        height=750,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"{variable_long} by region in PyPSA-UK ({unit0})",
    )

    fig.update_traces(
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="black",
                            font_size=14,
                            font_color="black"
                        )
                    )
    
    fig.update_traces(
                        marker_line_width=0.1,
                        marker_line_color="gray"
                    )

    fig.show(config={"scrollZoom": True})

    add_str = "_mapped" if n_mapping else ""
    filename += add_str
    fig.write_html(f"figures/{scen}_{filename}.html", config={"scrollZoom": True})

def plot_energy_mix(variables, scen, years, var_label = "annual_heat_demand_TWh", preferred_order = preferred_order_heating):
    
    df_1 = pd.DataFrame(index = years) # supply
    df_2 = pd.DataFrame(index = years) # demand by sector

    for year in years:
        var_1 = variables[0][f"{scen}-{year}"].drop(columns = ["country", "parent", "contains", "substations", "geometry"])
        var_2 = variables[1][f"{scen}-{year}"]
        
        if "heat" in var_label:
            var_1.columns = var_1.columns.str.replace("rural ","")
            var_1 = var_1.T.groupby(var_1.columns).sum().T.drop(columns = ["DAC"])

        df_1.loc[year, 
                var_1.columns] = var_1.sum()

        df_2.loc[year, var_2.index] = var_2.values

    new_columns = df_1.columns[df_1.sum() / (df_1.sum().sum()) > 0.001]
    df_1 = df_1[new_columns]

    new_index = preferred_order.intersection(df_1.columns).append(
                                                            df_1.columns.difference(preferred_order)
                                                            )
    fig, ax = plt.subplots(figsize=(12,6), dpi = 300)
    df_1[new_index].plot(kind='area', stacked=True, ax=ax, 
                        color = [tech_colors[i] for i in new_index], lw=0
                    )

    # give me len(preferred_order_demand) shades of gray 
    gray_shades = plt.cm.Greys(np.linspace(0.2, 0.8, len(preferred_order_demand)))
    for i, tech in enumerate(preferred_order_demand):
        if tech not in  tech_colors.keys():
            tech_colors[tech] = gray_shades[i]

    ylim = ax.get_ylim()[1]
    new_index_demand = preferred_order_demand.intersection(df_2.columns).append(
                                                            df_2.columns.difference(preferred_order_demand)
                                                            )
    # remove legend
    ax.legend().remove()

    ax.set_xlim(2025, 2050)
    ax.set_ylabel("TWh")

    # plot heat_demand_agg_series as a dashed line
    ax.plot(df_2.index, df_2.sum(axis=1), 
            color='black', lw=3, ls='--', label='"demand"', zorder = 100)

    ax.axhline(y=0, color='white', lw=1, ls="--")

    # add legend below plot
    handles, labels = ax.get_legend_handles_labels()
    leg_y_pos_1 = -0.25 if not "heat" in var_label else -0.33
    leg_x_pos_1 = 0.22 if not "heat" in var_label else 0.25
    fig.legend(handles, labels, loc='lower center', ncol=2, fontsize=12, bbox_to_anchor=(leg_x_pos_1, leg_y_pos_1), title="Supply by source")

    (-df_2.loc[:, new_index_demand]).plot(kind='area', stacked=True, ax=ax, 
                                        color = [tech_colors[i] for i in new_index_demand], alpha=0.7,
                                        lw=0
                                        )

    ax.legend().remove()
    handles, labels = ax.get_legend_handles_labels()

    nl = len(new_index_demand)
    leg_y_pos_2 = -0.21 if not "heat" in var_label else -0.21
    leg_x_pos_2 = 0.7 if not "heat" in var_label else 0.77
    fig.legend(handles[-nl:], labels[-nl:], loc='lower center', ncol=2, fontsize=12, bbox_to_anchor=(leg_x_pos_2, leg_y_pos_2), title="Demand by sector")

    ax.set_ylim(-ylim, ylim)

    ax.grid(lw = 0.5, ls = '--')

    # grid should be behind the plots
    ax.set_axisbelow(True)

    return fig
