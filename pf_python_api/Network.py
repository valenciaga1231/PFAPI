from powerfactory import DataObject
import numpy as np

from .Elements import SynchronousGenerator, Line, Switch, TwoWindingTransformer, ThreeWindingTransformer, Load, ElectricalElement, Busbar, CommonImpedance, ExternalGrid, VoltageSourceAC, ShuntElement
from .LoadFlowResults import BusLoadFlowResult
from .Converter import Converter

from typing import Dict, List
from collections import defaultdict

class Network:
    def __init__(self):
        # Busbars
        self.busbarsPF: List[DataObject] = []
        self.busbar_name_to_index = {}

        # Classified network PF elements
        self.classified_elements: Dict[str, List[DataObject]] = {
            'ElmLne': [],       # Lines
            'ElmTr2': [],       # Transformers 2-Winding
            'ElmTr3': [],       # Transformers 3-Winding
            'ElmLod': [],       # Loads
            'ElmSym': [],       # Synchronous Machines
            'ElmCoup': [],      # Switches
            'ElmZpu': [],       # Common impedance pač neka impedanca, ki predsavlja neko skupno impedanco več elementov
            'ElmSind': [],      # Series reactors
            'ElmScap': [],      # Series capacitors
            'ElmBranch': [],    # Branch element is a composite two-port element which can contain a number of lines, terminals etc.
            'ElmVac': [],       # AC Voltage Source
            'ElmSssc': [],      # Static Synchronous Series Compensator
            'ElmShnt': [],      # Switchable Shunt
            'ElmSubmodcon': [], # ????
            'ElmVacbin': [],    # ????
            'ElmVscmono': [],   # PWM Converter (voltage source with series reactor or Norton Equivalent)
            'ElmGenstat': [],   # Static generator
            'ElmSvs': [],       # Static Var System
            'ElmXnet': [],      # External grid
            'ElmIac': [],       # AC Current Source
        }

        # Classified network elements
        self.busbars: List[Busbar] = []
        self.synchronous_machines: List[SynchronousGenerator] = []
        self.lines: List[Line] = []
        self.switchs: List[Switch] = []
        self.two_winding_transformers: List[TwoWindingTransformer] = []
        self.three_winding_transformers: List[ThreeWindingTransformer] = []
        self.loads: List[Load] = []
        self.common_impedances: List[CommonImpedance] = []
        self.external_grids: List[ExternalGrid] = []
        self.voltage_sources: List[VoltageSourceAC] = []
        self.shunts: List[ShuntElement] = []

        self.all_elements: List[ElectricalElement] = []

        # Load flow results
        self.load_flow_results: Dict[str, BusLoadFlowResult] = {}

    def store_busbar_name_to_index(self,idx, busbar_name: str, substation_name: str):
        unique_key = f"{substation_name}_{busbar_name}"
        if unique_key not in self.busbar_name_to_index:
            self.busbar_name_to_index[unique_key] = idx
        # return self.busbar_name_to_index[unique_key]

    def read_busbars(self, busbarsPF: List[DataObject]):
        self.busbar_name_to_index = {}
        self.busbarsPF = []
        self.busbars = []
        filtered_busbars = []

        for busbar in busbarsPF:
            # Remove out of service busbars
            if busbar.GetAttribute("outserv") == 1:
                continue

            # Check busbar type (accept only Busbar - 0 and Junction Node - 1)
            busbar_type = busbar.GetAttribute("iUsage")
            if busbar_type != 0 and busbar_type != 1:
                continue
            
            # Check if busbar is energized
            if busbar.IsEnergized() != 1:
                continue

            # If goes through all checks, add busbar to the list
            filtered_busbars.append(busbar)
        
        # Store filtered PF busbars
        self.busbarsPF = filtered_busbars

        # Store busbar name to index mapping
        for idx, busbar in enumerate(self.busbarsPF):
            busbar_name = busbar.GetAttribute("loc_name")
            if busbar_name in self.busbar_name_to_index:
                print(f"Duplicate busbar name found: {busbar_name}")
            else:
                self.busbar_name_to_index[busbar_name] = idx

        # Store busbars as objects
        self.busbars = Converter.convert_busbars(self.busbarsPF)

    def read_load_flow_results(self, load_flow_results: Dict[str, BusLoadFlowResult]):
        self.load_flow_results = load_flow_results

    def get_connected_elements(self):
        '''
        Gets all connected elements to the busbars from PF and classifies them storing in self.classified_elements
        '''
        connected_elements = {}
        self.classified_elements = defaultdict(list)
        print(f"[INFO] Obtaining connected elements... in {len(self.busbarsPF)} busbars...")

        for bus in self.busbarsPF:
            # Get connected elements to the busbar
            # elements = bus.GetConnectedElements(0, 0, 0)
            elements = bus.GetConnectedElements(1, 1, 1)
            
            # Iterate over connected elements
            for element in elements:
                element_id = element.GetAttribute('loc_name')
                element_class = element.GetClassName()
                # Check if element is in service
                if element.GetAttribute("outserv") == 1:
                    continue

                # Check if element is energized
                if element.IsEnergized() != 1:
                    continue
                
                # Get unique name for connecting circuits breakers between double busbars
                if element_class == "ElmCoup":
                    substation = element.GetAttribute('cpSubstat')
                    substation_name = substation.GetAttribute('loc_name') if substation is not None else "None"
                    element_id = Converter.generate_unique_busbar_name(element_id, substation_name)

                # Add element to connected elements
                if element_id in connected_elements:
                    # print(f"Element with name {element_id} already exists")
                    pass
                else:
                    connected_elements[element_id] = element

        for element in connected_elements.values():
            class_name = element.GetClassName()
            self.classified_elements.setdefault(class_name, []).append(element)
                

    def generate_unique_index(self, element_name: str, substation_name: str) -> int:
        """
        Generates a unique index for an element based on its name and substation name.
        The index is a hash of the concatenated names, ensuring uniqueness.
        """
        unique_string = f"{substation_name}_{element_name}"
        unique_index = hash(unique_string) % (10 ** 8)  # Modulo to limit the size of the index
        return unique_index

    def obtain_elements_data(self):
        '''
        Converts classified elements from PF Objects to internal objects and stores them in self.<element_type>
        '''
        self.lines = Converter.convert_lines(self.classified_elements['ElmLne'], self.busbar_name_to_index)
        self.loads = Converter.convert_loads(self.classified_elements['ElmLod'], self.load_flow_results)
        self.switchs = Converter.convert_switches(self.classified_elements['ElmCoup'])
        self.two_winding_transformers = Converter.convert_two_winding_transformers(self.classified_elements['ElmTr2'])
        self.three_winding_transformers = Converter.convert_three_winding_transformers(self.classified_elements['ElmTr3'])
        self.synchronous_machines = Converter.convert_synchronous_machines(self.classified_elements['ElmSym'])
        self.common_impedances = Converter.convert_common_impedances(self.classified_elements['ElmZpu'])
        self.external_grids = Converter.convert_external_grids(self.classified_elements['ElmXnet'])
        self.voltage_sources = Converter.convert_voltage_source_AC(self.classified_elements['ElmVac'])
        self.shunts = Converter.convert_shunt_elements(self.classified_elements['ElmShnt'])

    def calculate_admittance_matrix(self):
        Y_bus = np.zeros((len(self.busbars), len(self.busbars)), dtype=complex)
        print(f"Number of busbars: {len(self.busbars)}")
        print(f"Admittance matrix shape: {Y_bus.shape}")
        print(self.busbar_name_to_index.__len__())

        # Add lines to the admittance matrix
        for line in self.lines:
            idx_from = self.busbar_name_to_index[line.busbar_from]
            idx_to = self.busbar_name_to_index[line.busbar_to]

            Y = line.Y_line
            Y_shunt = line.Y_shunt

            # If line is parallel, calculate new Y & Y_shunt
            if (line.parallel > 1):
                # print(f"Parallel line: {line.parallel} Calculating new Y and Y_shunt")
                Y        = Y        * line.parallel
                Y_shunt  = Y_shunt  * line.parallel

            Y_bus[idx_from, idx_to] -= Y
            Y_bus[idx_to, idx_from] -= Y
            Y_bus[idx_from, idx_from] += Y + Y_shunt / 2
            Y_bus[idx_to, idx_to] += Y + Y_shunt / 2
        
        # Add generators to the admittance matrix
        for generator in self.synchronous_machines:
            idx = self.busbar_name_to_index[generator.busbar_to]
            try:
                Y_bus[idx, idx] += generator.Y
            except IndexError as e:
                print(f"IndexError at generator {generator.name}: idx={idx}, error={e}")
                raise

        # Add switches to the admittance matrix
        for switch in self.switchs:
            idx_from = self.busbar_name_to_index[switch.busbar_from]
            idx_to = self.busbar_name_to_index[switch.busbar_to]
            Y = switch.Y
            Y_bus[idx_from, idx_to] -= Y
            Y_bus[idx_to, idx_from] -= Y
            Y_bus[idx_from, idx_from] += Y
            Y_bus[idx_to, idx_to] += Y
        
        # Add two winding transformers to the admittance matrix
        for transformer in self.two_winding_transformers:
            idx_from = self.busbar_name_to_index[transformer.busbar_from]   # HV
            idx_to = self.busbar_name_to_index[transformer.busbar_to]       # LV
            Y = transformer.Y
            a = transformer.ratio

            # Diagonal elements
            if (transformer.parallel > 1):
                Y_bus[idx_from, idx_from] += (Y / abs(a) ** 2)*transformer.parallel
                Y_bus[idx_to, idx_to] += Y*transformer.parallel
            else:
                Y_bus[idx_from, idx_from] += Y / abs(a) ** 2 
                Y_bus[idx_to, idx_to] += Y

            # Off-diagonal elements
            if (transformer.parallel > 1):
                Y_bus[idx_from, idx_to] -= (Y / np.conj(a))*transformer.parallel
                Y_bus[idx_to, idx_from] -= (Y / a)*transformer.parallel
            else:
                Y_bus[idx_from, idx_to] -= Y / np.conj(a)
                Y_bus[idx_to, idx_from] -= Y / a

            # Y_elements = transformer.get_admittance_matrix_elements()
            # Y_bus[idx_from, idx_from] += Y_elements['Y_aa']    
            # Y_bus[idx_to, idx_to] += Y_elements['Y_bb']     

            # # Off-diagonal elements
            # Y_bus[idx_from, idx_to] -= Y_elements['Y_ab']
            # Y_bus[idx_to, idx_from] -= Y_elements['Y_ba']

        # Add three winding transformers to the admittance matrix
        for transformer in self.three_winding_transformers:
            idx_HV = self.busbar_name_to_index[transformer.bus_HV]
            idx_MV = self.busbar_name_to_index[transformer.bus_MV]
            idx_LV = self.busbar_name_to_index[transformer.bus_LV]

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
        for load in self.loads:
            idx = self.busbar_name_to_index[load.busbar_to]
            Y_bus[idx, idx] += load.Y
        
        # Add Common Impedances to the admittance matrix
        for common_impedance in self.common_impedances:
            idx_from = self.busbar_name_to_index[common_impedance.bus_from]   # HV
            idx_to = self.busbar_name_to_index[common_impedance.bus_to]       # LV
            Y = common_impedance.Y

            # Diagonal elements
            Y_bus[idx_from, idx_from] += Y
            Y_bus[idx_to, idx_to] += Y

            # Off-diagonal elements
            Y_bus[idx_from, idx_to] -= Y
            Y_bus[idx_to, idx_from] -= Y

        # Add External Grids to the admittance matrix
        for external_grid in self.external_grids:
            idx = self.busbar_name_to_index[external_grid.bus_to]
            Y = external_grid.Y
            Y_bus[idx, idx] += Y

        # Add Voltage Sources to the admittance matrix
        for voltage_source in self.voltage_sources:
            idx = self.busbar_name_to_index[voltage_source.bus_to]
            Y = voltage_source.Y
            Y_bus[idx, idx] += Y

        # Add Shunts to the admittance matrix
        for shunt in self.shunts:
            idx = self.busbar_name_to_index[shunt.bus_to]
            Y = shunt.Y
            Y_bus[idx, idx] += Y

        return Y_bus