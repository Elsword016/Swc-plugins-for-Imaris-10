#
#
#  Export SWC XTension  
#
#  @Biswanath Saha 
#
#    <CustomTools>
#      <Menu>
#       <Item name="SWC Exporter 1.0" icon="Python3" tooltip="Calls the Imaris To export SWC">
#         <Command>Python3XT::XTExportSWC(%i)</Command>
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
logging.basicConfig(filename='G://swc_converter_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
def XTExportSWC(aImarisId):
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

	if vFilaments is None:
		print('Pick a filament first')
		time.sleep(10)
		return
	V = vImaris.GetDataSet()
	pixel_scale = np.array([V.GetSizeX() / (V.GetExtendMaxX() - V.GetExtendMinX()),
							V.GetSizeY() / (V.GetExtendMaxY() - V.GetExtendMinY()),
							V.GetSizeZ() / (V.GetExtendMaxZ() - V.GetExtendMinZ())])
	pixel_offset = np.array([V.GetExtendMinX(), V.GetExtendMinY(), V.GetExtendMinZ()])
	# ad-hoc fix Z-flip when |maxZ| < |minZ|
	if abs(V.GetExtendMinZ()) > abs(V.GetExtendMaxZ()):
		pixel_offset = np.array([V.GetExtendMinX(), V.GetExtendMinY(), V.GetExtendMaxZ()])
		pixel_scale[2] = -pixel_scale[2]

	# get filename
	root = Tk()
	root.withdraw()
	savename = filedialog.asksaveasfilename(defaultextension=".swc")
	root.destroy()
	if not savename: # asksaveasfilename return '' if dialog closed with "cancel".
		print('No files selected')
		time.sleep(10)
		return
	
	#main conversion
	swcs = np.zeros((0,7))
	swc_list = []
	vCount = vFilaments.GetNumberOfFilaments()
	for i in range(vCount):
		vFilamentsXYZ = vFilaments.GetPositionsXYZ(i)
		vFilamentsRadius = vFilaments.GetRadii(i)
		vFilamentsEdges = vFilaments.GetEdges(i)
		vFilamentsTypes = vFilaments.GetTypes(i)

		N = len(vFilamentsXYZ)
		G = np.zeros((N,N),dtype=bool)
		visited = np.zeros(N,dtype=bool)
		for p1,p2 in vFilamentsEdges:
			G[p1,p2] = True
			G[p2,p1] = True
			
		head = 0
		swc = np.zeros((N,7))
		visited[0] = True


		queue = [0]
		prevs = [-1]
		while queue:
			cur = queue.pop()
			prev = prevs.pop()

			swc[head] = [head+1, vFilamentsTypes[cur],0,0,0,vFilamentsRadius[cur],prev]
			pos = vFilamentsXYZ[cur]-pixel_offset
			swc[head,2:5] = pos*pixel_scale
			for idx in np.where(G[cur])[0]:
				if not visited[idx]:
					visited[idx] = True
					queue.append(idx)
					prevs.append(head+1)
			head += 1
		filename_filament = f"{savename}_filament_{i}.swc"
		print('Exported '+str(i+1)+'/'+str(vCount)+' filaments',end='\r') ## Export individual filaments as separate swcs
		swcs = np.vstack((swcs,swc))
		np.savetxt(filename_filament,swc,fmt='%d %d %f %f %f %f %d')
	np.savetxt(savename,swcs,fmt='%d %d %f %f %f %f %d') # Combined swcs
	print('All filaments exported!')
	time.sleep(5)
		
