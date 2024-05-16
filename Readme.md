## Imaris plugins

Based on the original implementation by Sarun Gulyanon (2018). 

Re-implemented from scratch for **Imaris 10.0.1** and **Python 3.7**

## Implementation details

Based on the **Breadth-first search (BFS)** - algorithm for searching a tree data structure for a node that satisfies a given property. It starts at the tree root and explores all nodes at the present depth before moving on to the nodes at the next depth level.
## Required
 - `ImarisXT` license 
 - `Imarisbridge`
 -  `ImarisLib`
 -  `Python 3.7`

## Depedencies

Please check the `environment.yml` for the necessary packages. Recommended to the use a conda environment.
## Files

1. `ExportSWC_new.py`- Export any Imaris filaments as swc morphology- separate and in a single combined file.
2. `ImportSWC_new.py` - Import any swc morphology as Imaris filaments.

## Installation

Placed in the folder with the `ImarisLib` library folders and then run it from the Imaris window and follows the prompts on the GUI.
