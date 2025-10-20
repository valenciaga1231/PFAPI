from typing import TYPE_CHECKING
import numpy as np
import pandas as pd
import logging

# Import Network for type checking to avoid circular imports
if TYPE_CHECKING:
    from ..core.Network import Network

logger = logging.getLogger(__name__)

def build_admittance_matrix(network: Network, as_dataframe: bool = False):
    # Initialize the admittance matrix shape
    Y_bus = np.zeros((len(network.busbars), len(network.busbars)), dtype=complex)

    # Add lines to the admittance matrix
    for line in network.lines:
        if line.busbar_from is None or line.busbar_to is None:
            continue
        idx_from = network.busbar_name_to_index[line.busbar_from]
        idx_to = network.busbar_name_to_index[line.busbar_to]

        Y = line.Y_line
        Y_shunt = line.Y_shunt

        # If line is parallel, calculate new Y & Y_shunt
        if (line.parallel > 1):
            Y        = Y        * line.parallel
            Y_shunt  = Y_shunt  * line.parallel

        Y_bus[idx_from, idx_to] -= Y
        Y_bus[idx_to, idx_from] -= Y
        Y_bus[idx_from, idx_from] += Y + Y_shunt / 2
        Y_bus[idx_to, idx_to] += Y + Y_shunt / 2
    
    # Add generators to the admittance matrix
    for generator in network.synchronous_machines:
        idx = network.busbar_name_to_index[generator.busbar_to]
        try:
            Y_bus[idx, idx] += generator.Y
        except IndexError as e:
            print(f"IndexError at generator {generator.name}: idx={idx}, error={e}")
            raise

    # Add switches to the admittance matrix
    for switch in network.switchs:
        if switch.busbar_from is None or switch.busbar_to is None:
            continue
        idx_from = network.busbar_name_to_index[switch.busbar_from]
        idx_to = network.busbar_name_to_index[switch.busbar_to]
        Y = switch.Y
        Y_bus[idx_from, idx_to] -= Y
        Y_bus[idx_to, idx_from] -= Y
        Y_bus[idx_from, idx_from] += Y
        Y_bus[idx_to, idx_to] += Y
    
    # Add two winding transformers to the admittance matrix
    for transformer in network.two_winding_transformers:
        if transformer.busbar_from is None or transformer.busbar_to is None:
            continue
        idx_from = network.busbar_name_to_index[transformer.busbar_from]   # HV
        idx_to = network.busbar_name_to_index[transformer.busbar_to]       # LV

        Y_elements = transformer.get_admittance_matrix_elements(network.base_mva)
        # Diagonal elements
        Y_bus[idx_from, idx_from] += Y_elements['Y_aa'] * transformer.parallel   
        Y_bus[idx_to, idx_to] += Y_elements['Y_bb'] * transformer.parallel    

        # Off-diagonal elements
        Y_bus[idx_from, idx_to] += Y_elements['Y_ab'] * transformer.parallel
        Y_bus[idx_to, idx_from] += Y_elements['Y_ba'] * transformer.parallel

    # Add three winding transformers to the admittance matrix
    for transformer in network.three_winding_transformers:
        idx_HV = network.busbar_name_to_index[transformer.bus_HV]
        idx_MV = network.busbar_name_to_index[transformer.bus_MV]
        idx_LV = network.busbar_name_to_index[transformer.bus_LV]

        # For simplified version
        Y_delta = transformer.delta_admittance_matrix()
        # Insert into global Y_bus (already sized NxN)
        Y_bus[idx_HV, idx_HV] += Y_delta[0, 0]
        Y_bus[idx_HV, idx_MV] += Y_delta[0, 1]
        Y_bus[idx_HV, idx_LV] += Y_delta[0, 2]
        Y_bus[idx_MV, idx_HV] += Y_delta[1, 0]
        Y_bus[idx_MV, idx_MV] += Y_delta[1, 1]
        Y_bus[idx_MV, idx_LV] += Y_delta[1, 2]
        Y_bus[idx_LV, idx_HV] += Y_delta[2, 0]
        Y_bus[idx_LV, idx_MV] += Y_delta[2, 1]
        Y_bus[idx_LV, idx_LV] += Y_delta[2, 2]
        

    # Add loads to the admittance matrix
    for load in network.loads:
        idx = network.busbar_name_to_index[load.busbar_to]
        Y_bus[idx, idx] += load.Y
    
    # Add Common Impedances to the admittance matrix
    for common_impedance in network.common_impedances:
        idx_from = network.busbar_name_to_index[common_impedance.bus_from]   # HV
        idx_to = network.busbar_name_to_index[common_impedance.bus_to]       # LV
        Y = common_impedance.Y

        # Diagonal elements
        Y_bus[idx_from, idx_from] += Y
        Y_bus[idx_to, idx_to] += Y

        # Off-diagonal elements
        Y_bus[idx_from, idx_to] -= Y
        Y_bus[idx_to, idx_from] -= Y

    # Add External Grids to the admittance matrix
    for external_grid in network.external_grids:
        idx = network.busbar_name_to_index[external_grid.busbar_to]
        Y = external_grid.Y
        Y_bus[idx, idx] += Y

    # Add Voltage Sources to the admittance matrix
    for voltage_source in network.voltage_sources:
        idx = network.busbar_name_to_index[voltage_source.busbar_to]
        Y = voltage_source.Y
        Y_bus[idx, idx] += Y

    # Add Shunts to the admittance matrix
    for shunt in network.shunts:
        idx = network.busbar_name_to_index[shunt.bus_to]
        Y = shunt.Y
        Y_bus[idx, idx] += Y

    if as_dataframe:
        busbar_names = [busbar.name for busbar in network.busbars]
        return pd.DataFrame(Y_bus, index=busbar_names, columns=busbar_names)
    
    return Y_bus

def reduce_matrix(Y_bus: np.ndarray, network: "Network"):
    '''
    Reduces the admittance matrix Y_bus by eliminating non-generator buses. This is done by:
    1. Extending the admittance matrix to add apparent generator buses
    2. Applying Kron reduction to eliminate non-generator buses

    Args:
        Y_bus (np.ndarray): The admittance matrix to be reduced.
        network (Network): The network object containing busbar and generator information.
    '''
    # Get generator bus names
    gen_bus_names = [gen.busbar_to for gen in network.synchronous_machines if gen.busbar_to is not None] # ['Bus 36G', 'Bus 33G',..]
    is_gen_bus = np.array([1 if bus in gen_bus_names else 0 for bus in network.busbar_name_to_index]) # [0, 0, 1, 0, 1,..] 1 for generator bus

    # Get indices of generator buses and store their name order
    generator_bus_indices = np.where(is_gen_bus == 1)[0] # Get indices of generator buses
    generator_bus_names_order = [network.busbars[i].name for i in generator_bus_indices] # Get names of generator buses

    # ----------- Sort the admittance matrix to have non-generator buses first and generator buses at the end -----------
    # Get all bus names
    all_bus_names =  [bus for bus in network.busbar_name_to_index]

    sorted_idx = sorted(range(len(all_bus_names)), key=lambda i: all_bus_names[i] in gen_bus_names)
    logger.debug(f"Sorted indices to non-generator first and generator second: {sorted_idx}")

    # Reindex Y_red to have non-generator buses first and generator buses second
    Y_bus_sorted = Y_bus[np.ix_(sorted_idx, sorted_idx)]

    # ----------- Build extended version of the admitance matrix -----------
    # Create new apparent generator buses matrix (maintaining the same order as generator_bus_names_order)
    y_gen = np.eye(np.sum(is_gen_bus), dtype=complex)
    for id, gen in enumerate(network.synchronous_machines):
        for i, bus_name in enumerate(generator_bus_names_order):
            if bus_name == gen.busbar_to:
                y_gen[i, i] = gen.Y

    # Connections to the apparent generator buses
    y_gen2 = -y_gen

    # Non-generator buses that are not connected to generator buses
    y_dist = np.zeros((np.sum(is_gen_bus == 1), np.sum(is_gen_bus == 0)))

    # Build the extended admittance matrix
    top_right = np.hstack((y_dist, y_gen2))
    bottom_left = np.vstack((y_dist.T, y_gen2))
    Y_extended = np.block([
        [y_gen,         top_right],
        [bottom_left,   Y_bus_sorted]
    ])
    logger.debug(f"Y_extended shape: {Y_extended.shape}")

    # ----------- Apply Kron reduction to the extended admittance matrix -----------
    num_gen_buses = np.sum(is_gen_bus) # Get number of generator buses
    Y_reduced = KronReduction(Y_extended, num_gen_buses)

    return Y_reduced, generator_bus_names_order

def KronReduction(Y: np.ndarray, p: int):
    '''
    Applies Kron reduction to the given admittance matrix Y.
    Args:
        Y (np.ndarray): The admittance matrix to be reduced.
        p (int): The number of generator buses (the size of the reduced matrix).
    Returns:
        np.ndarray: The reduced admittance matrix.
    '''
    # Extracting sub-blocks
    Y_RR = Y[:p, :p]
    Y_RL = Y[:p, p:]
    Y_LR = Y[p:, :p]
    Y_LL = Y[p:, p:]
    
    # Compute the inverse of Y_LL
    Y_LL_inv = np.linalg.inv(Y_LL)
    
    # Compute Y_reduced using the Schur complement
    Y_reduced = Y_RR - Y_RL @ Y_LL_inv @ Y_LR

    return Y_reduced