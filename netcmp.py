#!/usr/bin/python3

# Imports
import hashlib


class Node:
    def __init__(self, component: str, pin: str, net: str):
        """ Simple class to represent a Node"""
        self.component = component
        self.pin = pin
        self.net = net


class Net:
    def __init__(self, name: str, full_signal_name: str):
        """ Simple class to represent a Net """
        self.name = name
        self.full_signal_name = full_signal_name


class NetCmp:
    def __init__(self, netlistpath):
        """ Main class for netlist comparison """
        # Init class vars
        self.nets = {}
        self.components = {}
        self.netlistpath = netlistpath
        self._hash = None

        # Parse the netlist file
        self.parse(netlistpath)

    def parse(self, filepath: str) -> None:
        """ Parse the netlist file """
        # Open netlist file
        with open(filepath) as fp:

            # Split netlist file contents on every semicolon, and iterate through each item
            for item in fp.read().split(";"):

                # Convert tabs to new lines, then split one every new line and store as i
                i = item.replace("\t", "\n").strip().split("\n")

                # If the first part starts with open curly bracket, its part of the header - remove it
                if i[0].startswith("{"):
                    del i[0]

                # Check if the first part is NODE_NAME
                if "NODE_NAME" in i[0]:

                    # Split the second part by spaces to get component and pin (R52 1)
                    component, pin = i[1].split(" ")

                    # Extract net name from 4th part. Remove quotes and colons, and strip out spaces
                    net = i[3].replace("'", "").replace(":", "").strip()

                    # Create node instance
                    node = Node(component=component, pin=pin, net=net)

                    # If there isn't already a dict for this component, create an empty one
                    if component not in self.components:
                        self.components[component] = {}

                    # Store node in dict, indexed by component then by pin
                    self.components[component][pin] = node

                # Check if the first part is NET_NAME
                elif "NET_NAME" in i[0]:

                    # Extract the net name from the second part, and strip out quotes
                    name = i[1].strip("'")

                    # Extract the full name, remove 'C_SIGNAL' and strip out spaces and quotes
                    full_name = i[3].replace("C_SIGNAL=", "").strip().strip("'")

                    # Create a new net instance, and store in the nets dict (indexed by net name)
                    net = Net(name=name, full_signal_name=full_name)
                    self.nets[name] = net

                # If it its NET_NAME or NODE_NAME, its crap. Skip and continue to the next item
                else:
                    continue

            # Regenerate hash
            self._hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """ Create an md5 hash of the design based on nodes and nets, irrespective of netlist ordering """
        # Initialise empty dict for flatten nodes
        node_flat = {}

        # Iterate through all components
        for comp_name, comp_dict in self.components.items():

            # Iterate through all pins of the component
            for pin_name, node in comp_dict.items():

                # Store the node for each pin in the flat dict
                node_flat[comp_name+"."+pin_name] = node

        # Initialise hasher instance
        hasher = hashlib.md5()

        # Create a list of all node names from the node_flat dict
        node_list = list(node_flat.keys())

        # !IMPORTANT! Sort the node_list alphabetically, so that we always have the same order
        # (regardless of netlist order)
        node_list.sort()

        # Iterate through every node name in the list
        for node_name in node_list:

            # Update the hasher with the node name and the node net
            hasher.update(node_name.encode())
            hasher.update(node_flat[node_name].net.encode())

        # Return a hex digest string of the hasher
        return hasher.hexdigest()

    def compare(self, b: NetCmp, report_path:str) -> int:
        """ Compare this design with b. Writes report to self.reportpath, and returns number of differences found """
        # Open/create the report file
        with open(reportpath, "w+") as fp:

            # Intialise the report index to zero
            self.report_index = 0

            # Write the intial report header
            fp.write("A: {}, ({})\n".format(self.hash(), self.netlistpath))
            fp.write("B: {}, ({})\n".format(self.hash(), b.netlistpath))
            fp.write("--------------------------------\n")
            fp.write("INDEX, REF, DIFF, A, B\n")

            # Define on the fly report write function, using the file pointer we opened
            # Each write is terminated with a newline character, and increments the report index
            def report(string):
                fp.write("{:03}, {}\n".format(self.report_index, string))
                self.report_index += 1

            # Iterate through each component
            for comp_name, comp_dict in self.components.items():

                # Check this component is in design b
                if comp_name in b.components:

                    # Iterate through every pin of this component
                    for pin, node in comp_dict.items():

                        # Check this pin is in design B's component
                        if pin in b.components[comp_name]:

                            # If the net attached to this pin is different from the one on design B, report the diff
                            if node.net != b.components[comp_name][pin].net:
                                report("{}.{}, NET DIFF, {}, {}".format(comp_name, pin, node.net, b.components[comp_name][pin].net))

                        # The pin is missing from design B's component, report it
                        else:
                            report("{}, COMP PIN MISSING, {}, NONE".format(comp_name, pin))

                # The component is missing from design B, report it
                else:
                    report("{0}, COMP MISSING, {0}, NONE".format(comp_name))

            # Iterate through all components in design B
            for comp_name in b.components.keys():

                # If the component is not in our design, report it
                if comp_name not in self.components:
                    report("{0}, EXTRA COMP, NONE, {0}".format(comp_name))

            # Write the report footer
            fp.write("--------------------------------\n")
            fp.write("{} differences found".format(self.report_index))

            # Return the number of diffs found (report index)
            return self.report_index

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, NetCmp):
            return False
        else:
            return hash(self) == hash(other)


# Execute if run directly (and not imported)
if __name__ == "__main__":

    import argparse

    # Initialise argument parser, with netlist a & b and report file arguments
    # Usage: netcmp.py [netlist_a] [netlist_b] [report_path]
    parser = argparse.ArgumentParser()
    parser.add_argument("netlist_a", help="Path to netlist A")
    parser.add_argument("netlist_b", help="Path to netlist B")
    parser.add_argument("report_file", help="Path to store report")
    args = parser.parse_args()

    # Create NetCmp instances for each netlist
    a = NetCmp(args.netlist_a)
    b = NetCmp(args.netlist_b)

    # Compare designs
    diff = a.compare(b, args.report_file)

    # Print comparison done, with number of diffs
    print("Comparison complete, {} differences found".format(diff))
    
    
