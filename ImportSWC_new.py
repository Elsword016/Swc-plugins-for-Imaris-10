#
#
#  Import SWC XTension  
#
#  @Biswanath Saha
#
#    <CustomTools>
#      <Menu>
#       <Item name="SWC Importer 1.0" icon="Python3" tooltip="Calls the Imaris to import SWC">
#         <Command>Python3XT::XTImportSWC(%i)</Command>
#       </Item>
#      </Menu>
#    </CustomTools>


import ImarisLib
import time
import random
import numpy as np
import logging
# GUI imports
from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog,filedialog
import os 
logging.basicConfig(filename='', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s') #add your filepath
def XTImportSWC(aImarisId):
	# Create an ImarisLib object
	vImarisLib = ImarisLib.ImarisLib()

	# Get an imaris object with id aImarisId
	vImaris = vImarisLib.GetApplication(aImarisId)

	if vImaris is None:
		print('Could not connect to Imaris!')
		time.sleep(10)
		return
	
	vFactory = vImaris.GetFactory()
	vFilaments = vFactory.ToFilaments(vImaris.GetSurpassSelection())
	root = Tk()
	root.withdraw()
	swc_dir = filedialog.askdirectory(title='Select SWC Directory')
	root.destroy()
	if not swc_dir: # asksaveasfilename return '' if dialog closed with "cancel".
		print('No files selected')
		time.sleep(10)
		return
	print(swc_dir)
	V = vImaris.GetDataSet()
	pixel_scale = np.array([V.GetSizeX() / (V.GetExtendMaxX() - V.GetExtendMinX()),
							V.GetSizeY() / (V.GetExtendMaxY() - V.GetExtendMinY()),
							V.GetSizeZ() / (V.GetExtendMaxZ() - V.GetExtendMinZ())])
	pixel_offset = np.array([V.GetExtendMinX(), V.GetExtendMinY(), V.GetExtendMinZ()])
	# ad-hoc fix Z-flip when |maxZ| < |minZ|
	if abs(V.GetExtendMinZ()) > abs(V.GetExtendMaxZ()):
		pixel_offset = np.array([V.GetExtendMinX(), V.GetExtendMinY(), V.GetExtendMaxZ()])
		pixel_scale[2] = -pixel_scale[2]
	
	for swc_file in os.listdir(swc_dir):
				if swc_file.endswith(".swc"):
					full_path = os.path.join(swc_dir, swc_file)
					print('Importing: ' + full_path)
					swc = np.loadtxt(full_path)

					try:
						N = swc.shape[0]
						vFilaments = vImaris.GetFactory().CreateFilaments()
						vPositions = swc[:, 2:5].astype(np.float) / pixel_scale
						vPositions = vPositions + pixel_offset
						vRadii = swc[:, 5].astype(np.float)
						vTypes = np.zeros((N))  # (0: Dendrite; 1: Spine)
						vEdges = swc[:, [6, 0]]
						idx = np.all(vEdges > 0, axis=1)
						vEdges = vEdges[idx, :] - 1
						vTimeIndex = 0
						vFilaments.AddFilament(vPositions.tolist(), vRadii.tolist(), vTypes.tolist(), vEdges.tolist(), vTimeIndex)
						vFilamentIndex = 0
						vVertexIndex = 1
						vFilaments.SetBeginningVertexIndex(vFilamentIndex, vVertexIndex)
						vScene = vImaris.GetSurpassScene()
						vScene.AddChild(vFilaments, -1)
						logging.info(f'Imported {swc_file}')
					except Exception as e:
						logging.error(f'Failed to import {swc_file}')
	print('All swc files imported')
