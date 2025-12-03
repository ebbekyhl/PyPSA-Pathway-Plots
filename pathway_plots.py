from scripts.pathway_functions import *
# token
token = "pk.eyJ1IjoiZWJiZWt5aGwiLCJhIjoiY21pZnU5dHdzMDAxODNmcXgzcnoyamM0MyJ9.K4YNSDBAcgnXN_hfrr7FrQ" # add your mapbox token here (get one from https://account.mapbox.com/access-tokens/)

# Specficiations
mapping = True # if network is mapped to admin regions then it needs a different regions .geojson file
timeres = "3h"
subfolder = "pypsa-uk"

# investigated scenarios
scenarios = ["all",
             'minimal_methanol_economy',
             ]

# define number of clusters used in scenarios
clusters_dic = {
    "all": 60,
    "minimal_methanol_economy": 60,
    }

# planning years considered
years = [
        2025, 
        2030, 
        2035, 
        2040, 
        2045, 
        2050
         ]

###############################################################################################################
############################ Choose variables to appear in the figures ########################################
###############################################################################################################

# Each of these lists define the variables included in each of the plots.

# renewable generators
ren_gen_techs = ["onshore wind", 
                "PV rooftop",
                "offshore wind",
                "PV utility",]

# conventional generators
gentechs = ["nuclear",
            "OCGT",
            "CCGT",
            "allam methanol",
            "CHP"
            ]

# storage technologies
storage_techs = ["battery", # utility and residential batteries
                 "H2", # underground and overground H2 stores
                 "methanol", 
                 'ammonia', 
                 "TES central", # thermal store in the heating supply (central)
                 "TES decentral", # thermal store in the heating supply (decentral)
                 'co2 sequestered', # onshore and offshore CO2 storage 
                 ]

# energy transmission 
transmission = ["H2 pipeline"]

# heating technologies
heating_techs = [
                "heat pump",
                "gas boiler",
                "biomass boiler",
                "resistive heater",
                "TES central",
                "TES decentral",
                # "CHP", # already included in gentechs
                ]

# Conversion links
links = [
        "Fischer-Tropsch",
        "SMR",
        "SMR CC",
        "Sabatier",
        "ammonia cracker",
        "methanolisation",
        "Methanol steam reforming",
        "H2 Electrolysis",
        ]

###############################################################################################################
######################################## Postprocess network files ############################################
###############################################################################################################
networks = {} # dictionary for storing network files
renewable_generation_capacity = {} # renewable generation capacity
generation_capacity = {} # conventional generation capacity 
storage_capacity = {} # Energy storage 
transmission_capacity = {} # Transmission capacity 
heating_capacity = {} # Heating technology capacity 
links_capacity = {} # Conversion links capacity 
electricity_demand = {} # Electricity demand  (including exogenous and endogenous)
heating_demand = {} # Heating demand 
electricity_generation = {} # Electricity generation mix
electricity_generation_normalized = {} # Normalized electricity generation mix
heating_generation = {} # Heating generation mix
heating_generation_normalized = {} # Normalized heating generation mix
for s in scenarios:
    for year in years:

        if mapping:
            path = f"networks/mapped/{s}_"
            network_name = path + f"base_s_{clusters_dic[s]}__{timeres}_{year}{'_mapped' if mapping else ''}.nc"

        else:
            subsubfolder = f"n{clusters_dic[s]}-{timeres}"
            # subsubfolder = f"n_varied-{timeres}"
            path = f"networks/raw/{subfolder}/{subsubfolder}/{s}/"

            network_name = path + f"networks/base_s_{clusters_dic[s]}__{timeres}_{year}{'_mapped' if mapping else ''}.nc"

        if f"{s}-{year}" in networks.keys():
            n = networks[f"{s}-{year}"]
        else:
            n = pypsa.Network(network_name)
            networks[f"{s}-{year}"] = n

        n_years = n.snapshot_weightings.sum().loc["objective"] / 8760
        snapshots_weighting = n_years * 8760 / len(n.snapshots)

        # Regional capacities
        renewable_generation_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, ren_gen_techs, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")
        generation_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, gentechs, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")
        storage_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, storage_techs, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")
        transmission_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, transmission, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")
        heating_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, heating_techs, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")
        links_capacity[f"{s}-{year}"] = calculate_capacities_at_regions(n, links, mapping = mapping, admin_shapes_path = path + "admin_shapes.geojson")

        # Electricity demand
        elec_demand_i = calculate_electricity_demand(n)
        annual_nodal_demand = pd.DataFrame(elec_demand_i.sum(axis=1)) / 1e6 * snapshots_weighting # in TWh
        annual_nodal_demand.columns = ["annual_elec_demand_TWh"]
        elec_demand_i_w_region = add_to_regions(annual_nodal_demand, mapping = mapping)
        electricity_demand[f"{s}-{year}"] = elec_demand_i_w_region

        # Heating demand
        heat_demand_i = calculate_heating_demand(n)
        annual_nodal_heat_demand = pd.DataFrame(heat_demand_i.sum(axis=1)) / 1e6 * snapshots_weighting # in TWh
        annual_nodal_heat_demand.columns = ["annual_heat_demand_TWh"]
        heat_demand_i_w_region = add_to_regions(annual_nodal_heat_demand, mapping = mapping)
        heating_demand[f"{s}-{year}"] = heat_demand_i_w_region

        # Generation mix
        gen_mix_i = calculate_generation_mix(n)
        gen_mix_i = gen_mix_i * snapshots_weighting / 1e6 # in TWh
        gen_mix_i_norm = gen_mix_i.unstack() / (gen_mix_i.sum().sum()) * 100
        gen_mix_i_w_region = add_to_regions(gen_mix_i.unstack(), mapping = mapping)
        gen_mix_i_norm_w_region = add_to_regions(gen_mix_i_norm, mapping = mapping)
        electricity_generation[f"{s}-{year}"] = gen_mix_i_w_region
        electricity_generation_normalized[f"{s}-{year}"] = gen_mix_i_norm_w_region

        heating_generation_uk_i = calculate_heating_generation_mix(n)
        annual_heating_generation = heating_generation_uk_i / 1e6 * snapshots_weighting # in TWh
        annual_heating_generation_norm = annual_heating_generation.unstack() / (annual_heating_generation.sum().sum()) * 100
        annual_heating_generation_w_region = add_to_regions(annual_heating_generation, mapping = mapping)
        annual_heating_generation_norm_w_region = add_to_regions(annual_heating_generation_norm.unstack().T, mapping = mapping)
        heating_generation[f"{s}-{year}"] = annual_heating_generation_w_region
        heating_generation_normalized[f"{s}-{year}"] = annual_heating_generation_norm_w_region

###############################################################################################################
################################# Plot electricity generation balance #########################################
###############################################################################################################
variables = [electricity_demand, 
             electricity_generation
            ]

for scen in scenarios:
    fig = plot_energy_mix(variables, scen, years, var_label = "annual_elec_demand_TWh", preferred_order = preferred_order)
    fig.savefig(f"figures/pathway_electricity_generation_mix_{scen}.png", bbox_inches='tight')

###############################################################################################################
################################# Plot heating generation balance #############################################
###############################################################################################################
variables = [heating_demand, 
             heating_generation
            ]

for scen in scenarios:
    fig = plot_energy_mix(variables, scen, years, var_label = "annual_heat_demand_TWh", preferred_order = preferred_order_heating)
    fig.savefig(f"figures/pathway_heating_generation_mix_{scen}.png", bbox_inches='tight')

###############################################################################################################
########################################## Create interactive map #############################################
###############################################################################################################
variables = {"UK_regional_electricity_demand": electricity_demand,
             "UK_regional_elec_gen_shares": electricity_generation_normalized,
             "UK_regional_heating_demand": heating_demand,
             "UK_regional_heating_gen_share": heating_generation_normalized,
             "UK_regional_renewable_generation_capacity": renewable_generation_capacity,
             "UK_regional_generation_capacity": generation_capacity,
             "UK_regional_storage_capacity": storage_capacity,
             "UK_regional_transmission_capacity": transmission_capacity,
             "UK_regional_heating_capacity": heating_capacity,
             "UK_regional_links_capacity": links_capacity,
             }

for scen in scenarios:
    for var_name, var_data in variables.items():
        if not (scen == "minimal_methanol_economy" and var_name == "UK_regional_transmission_capacity"):
            make_interactive_map(token, var_data, var_name, years, scen, n_mapping = mapping)