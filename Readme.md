## Swc importer and exporter for Imaris 10.0.1

Based on the original implementation by Sarun Gulyanon (2018). Re-implemented from scratch for **Imaris 10.0.1** and **Python 3.7** and updated some things like generation and saving individual filaments separately and exports more consistent with the .swc specifications.

Used for additional analysis of the paper:

**Automated neuronal reconstruction with super-multicolour fluorescence imaging**

Marcus N. Leiwe, Satoshi Fujimoto, Toshikazu Baba, Daichi Moriyasu, Biswanath Saha, Richi Sakaguchi, Shigenori Inagaki, Takeshi Imai 
[[bioRxiv 2022]](https://www.biorxiv.org/content/10.1101/2022.10.20.512984v1) [[github]](https://github.com/mleiwe/QDyeFinder)



## Implementation details

Based on the **Breadth-first search (BFS)** - algorithm for searching a tree data structure for a node that satisfies a given property. It starts at the tree root and explores all nodes at the present depth before moving on to the nodes at the next depth level.
## Required
 - `ImarisXT` license 
 - `Imarisbridge`
 -  `ImarisLib`
 -  `Python 3.7`

## Files

1. `ExportSWC_new.py`- Export any Imaris filaments as swc morphology- separate and in a single combined file.
2. `ImportSWC_new.py` - Import any swc morphology as Imaris filaments.


## Morphology file specifications

**Standard .swc** morphologies only (no swc+). 

Data imported/exported follows the [Neuromorpho specifications](http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html) should look like this:

- Encoding:  ASCII text
- Limitations: no markers, no spines.
- Comment lines begin with character '#'.
- Subsequent non-empty lines each represent a single neuron sample point with seven data items.

![image](https://github.com/Elsword016/Swc-plugins-for-Imaris-10/assets/29883365/d2437612-806a-4a88-b544-bea8054a8590)

## Depedencies

Please check the `environment.yml` for the necessary packages. Recommended to the use a conda environment.

## Installation

Place in the folder with the `ImarisLib` library folders and then run it from the Imaris window and follow the prompts on the GUI.


