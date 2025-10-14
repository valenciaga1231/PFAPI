import numpy as np
import powerfactory as pf
from .Network import Network
import logging
from typing import Dict
from ..utils.LoadFlowResults import BusLoadFlowResult

logger = logging.getLogger(__name__)

def calculate_power_distribution_ratios(Y_reduced, generator_bus_names_order: list[str], network: Network, gen_out_name):
    B_K = np.imag(Y_reduced)
    G_K = np.real(Y_reduced)

    # Get load-flow results from Network
    load_flow_results = network.load_flow_results

    V_gens, Z_gens = obtain_generator_voltage_and_impedance(network, generator_bus_names_order, load_flow_results)
    P_gens, Q_gens = obtain_generator_power(network, generator_bus_names_order)
    E_gens, E_abs, E_angle = calculate_generators_internal_voltage_and_angle(V_gens, Z_gens, P_gens, Q_gens)

    E_abs = E_abs.reshape(-1, 1)
    E_angle = E_angle.reshape(-1, 1)

    # ------ Calculate synchronizing power coefficients ------
    # Find the index of the disturbance bus based on the generator name
    dist_bus_name = next((gen.busbar_to for gen in network.synchronous_machines if gen.name == gen_out_name), None)
    if dist_bus_name is None:
        raise ValueError(f"Generator with name '{gen_out_name}' not found in synchronous_machines")
    dist_bus = generator_bus_names_order.index(dist_bus_name) # Disturbance bus index
    logging.info(f"Calculating synchronizing power coefficients for disturbance bus: {dist_bus_name} at index {dist_bus}")

    K = (np.ones(Y_reduced.shape) * E_abs[dist_bus] * E_abs *
        (B_K * np.cos(E_angle - np.ones(Y_reduced.shape) * E_angle[dist_bus]) -
         G_K * np.sin(E_angle - np.ones(Y_reduced.shape) * E_angle[dist_bus])))
    
    K[np.isnan(K)] = 0 # Replace NaN values with zero

    # Reference is SG bus
    K = K[:, dist_bus] # Select the column at dist_bus from matrix
    K[dist_bus] = 0 # Set the element at dist_bus to zero

    # Calculate the ratios of power distrubution
    ratios = K / np.sum(K)

    return ratios

def obtain_generator_voltage_and_impedance(network: Network, generator_bus_names_order: list[str], lf_results: Dict[str, BusLoadFlowResult]):
    V_gens = np.zeros(len(generator_bus_names_order), dtype=complex)
    Z_gens = np.zeros(len(generator_bus_names_order), dtype=complex)

    # Loop through each generator bus name and find the corresponding generator
    for i, bus_name in enumerate(generator_bus_names_order):
        for gen in network.synchronous_machines:
            if gen.busbar_to == bus_name:
                # Get voltage and angle
                V = lf_results[bus_name].voltage
                phi = lf_results[bus_name].angle

                V_complex = V * (np.cos(np.radians(phi)) + 1j * np.sin(np.radians(phi)))
                V_gens[i] = V_complex

                Z = 1 / gen.Y
                Z_gens[i] = Z
                break

    return V_gens, Z_gens

def obtain_generator_power(network: Network, generator_bus_names_order: list[str]):
    P_gens = np.zeros(len(generator_bus_names_order))
    Q_gens = np.zeros(len(generator_bus_names_order))

    for i, bus_name in enumerate(generator_bus_names_order):
        for gen in network.classified_elements['ElmSym']:
            # busbar_to = gen.GetAttribute()
            connected_terminal: pf.DataObject = gen.GetAttribute("bus1")
            gen_bus_name = connected_terminal.GetParent().GetAttribute("loc_name")

            if gen_bus_name == bus_name:
                typ = gen.typ_id
                rat_power = typ.GetAttribute('sgn')

                P = gen.GetAttribute("m:P:bus1")
                Q = gen.GetAttribute("m:Q:bus1")
                P_gens[i] = P/rat_power # [p.u.]
                Q_gens[i] = Q/rat_power # [p.u.]
                break

    return P_gens, Q_gens

def calculate_generators_internal_voltage_and_angle(V_gens, Z_gens, P_gens, Q_gens):
    E = V_gens + Z_gens * (np.conj(P_gens + 1j * Q_gens) / np.conj(V_gens))
    E_abs = np.abs(E)
    E_angle = np.angle(E)

    return E, E_abs, E_angle