# NetCmp
Cadence netlist comparison tool

###Usage
```netcmp.py [path to netlist A] [path to netlist_B] [path to report]```

###Output
Produces a csv format output of all differences (component or pin missing, or different net attached).

###Library

You can also use it as a library by importing the ```NetCmp``` class.

```python
 from netcmp import NetCmp
 
 # Init and parse netlist
 netlist1  = NetCmp("path//to//netlist1.dat")
 netlist2  = NetCmp("path//to//netlist2.dat")
 
 # Direct pythonic netlist comparison using __eq__()
 if netlist1 != netlist2:
    print("They ain't the same bud")
    
 # Perform full comparison and create report
 netlist1.compare(netlist2, "path//to//report.csv")
 
 # Grab the net name of a component's pin
 r150_pin1_net = netlist1.components["R150"]["1"].net
 
 # Get a list of all nets 
 list_all_nets = netlist2.nets
```
