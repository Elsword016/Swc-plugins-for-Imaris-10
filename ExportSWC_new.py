#
#
#  Export SWC XTension
#
#  @Biswanath Saha
#
#    <CustomTools>
#      <Menu>
#       <Item name="SWC Exporter 1.1 (Debug)" icon="Python3" tooltip="Calls the Imaris To export SWC (with debug pause)">
#         <Command>Python3XT::XTExportSWC(%i)</Command>
#       </Item>
#      </Menu>
#    </CustomTools>


import ImarisLib
import time
import random
import numpy as np
import logging
import traceback # Import traceback module for detailed error info
import os # Import os module for path manipulation

# GUI imports
from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog, filedialog

# --- Configuration ---
# *** IMPORTANT: SET A VALID PATH FOR YOUR LOG FILE ***
# Example for Windows: 'C:/Users/YourUsername/Documents/imaris_swc_export.log'
# Example for macOS: '/Users/YourUsername/Documents/imaris_swc_export.log'
# Example for Linux: '/home/YourUsername/imaris_swc_export.log'
# Using os.path.expanduser('~') gets your home directory automatically:
log_file_path = os.path.join(os.path.expanduser('~'), 'imaris_swc_export.log')

# Configure logging to write to the specified file
logging.basicConfig(filename=log_file_path,
                    level=logging.DEBUG, # Log everything from DEBUG level up
                    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s', # Include function name
                    filemode='a') # 'a' to append, 'w' to overwrite each time

# Also log to console (useful if the window *doesn't* close instantly)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # Log INFO level and above to console
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def XTExportSWC(aImarisId):
    logging.info(f"--- Script Started for Imaris ID: {aImarisId} ---")
    try:
        # Create an ImarisLib object
        vImarisLib = ImarisLib.ImarisLib()
        logging.debug("ImarisLib object created.")

        # Get an imaris object with id aImarisId
        vImaris = vImarisLib.GetApplication(aImarisId)

        if vImaris is None:
            logging.error("Could not connect to Imaris!")
            messagebox.showerror("Error", "Could not connect to Imaris instance.")
            return # Exit early

        logging.info(f"Connected to Imaris version: {vImaris.GetVersion()}")

        vFactory = vImaris.GetFactory()
        vFilaments = vFactory.ToFilaments(vImaris.GetSurpassSelection())

        if vFilaments is None:
            logging.warning("No filament object selected in Imaris.")
            messagebox.showwarning("Selection Required",
                                   "Please select a Filaments object in the Surpass tree before running the script.")
            return # Exit early

        logging.info(f"Processing Filaments object: {vFilaments.GetName()}")

        V = vImaris.GetDataSet()
        if V is None:
             logging.error("Could not get DataSet from Imaris.")
             messagebox.showerror("Error", "Could not get image dataset details from Imaris.")
             return # Exit early

        # Calculate pixel scaling and offset
        min_x, min_y, min_z = V.GetExtendMinX(), V.GetExtendMinY(), V.GetExtendMinZ()
        max_x, max_y, max_z = V.GetExtendMaxX(), V.GetExtendMaxY(), V.GetExtendMaxZ()
        size_x, size_y, size_z = V.GetSizeX(), V.GetSizeY(), V.GetSizeZ()

        # Avoid division by zero if extent is zero in any dimension (though unlikely)
        scale_x = size_x / (max_x - min_x) if (max_x - min_x) != 0 else 1.0
        scale_y = size_y / (max_y - min_y) if (max_y - min_y) != 0 else 1.0
        scale_z = size_z / (max_z - min_z) if (max_z - min_z) != 0 else 1.0

        pixel_scale = np.array([scale_x, scale_y, scale_z])
        pixel_offset = np.array([min_x, min_y, min_z])

        # ad-hoc fix Z-flip when |maxZ| < |minZ| (common in some microscope setups)
        if abs(min_z) > abs(max_z) and (max_z - min_z) != 0:
            logging.warning("Detected potential Z-flip (|minZ| > |maxZ|). Adjusting offset and scale.")
            pixel_offset = np.array([min_x, min_y, max_z]) # Use max_z as the origin offset
            pixel_scale[2] = -pixel_scale[2] # Invert Z scaling

        logging.debug(f"Pixel Scale: {pixel_scale}")
        logging.debug(f"Pixel Offset: {pixel_offset}")

        # get filename
        root = Tk()
        root.withdraw() # Hide the main Tk window
        savename = filedialog.asksaveasfilename(
            title="Save SWC file(s)",
            defaultextension=".swc",
            filetypes=[("SWC files", "*.swc"), ("All files", "*.*")]
        )
        root.destroy() # Clean up the Tk root window

        if not savename: # asksaveasfilename return '' if dialog closed with "cancel".
            logging.info("File save operation cancelled by user.")
            print("Operation cancelled: No file selected.") # Also print to console
            return # Exit early

        logging.info(f"Selected base save name: {savename}")
        # Optional: Split base name and extension for cleaner individual file naming
        base_name, _ = os.path.splitext(savename)


        #main conversion
        all_filaments_swc_data = [] # Use a list to collect numpy arrays first
        vCount = vFilaments.GetNumberOfFilaments()
        logging.info(f"Found {vCount} individual filament(s) to process.")

        if vCount == 0:
            logging.warning("Filaments object contains 0 filaments.")
            messagebox.showwarning("Empty Object", "The selected Filaments object contains no actual filaments.")
            return

        for i in range(vCount):
            logging.debug(f"Processing filament index {i}")
            vFilamentsXYZ = vFilaments.GetPositionsXYZ(i)
            vFilamentsRadius = vFilaments.GetRadii(i)
            vFilamentsEdges = vFilaments.GetEdges(i) # List of (p1, p2) index tuples
            vFilamentsTypes = vFilaments.GetTypes(i) # Optional: Get segment types if set

            N = len(vFilamentsXYZ)
            if N == 0:
                logging.warning(f"Filament index {i} has no points. Skipping.")
                continue # Skip this filament

            # Adjacency list is often more efficient for sparse graphs like neurons
            adj = [[] for _ in range(N)]
            for p1, p2 in vFilamentsEdges:
                 # Ensure indices are within bounds (paranoia check)
                if 0 <= p1 < N and 0 <= p2 < N:
                    adj[p1].append(p2)
                    adj[p2].append(p1)
                else:
                    logging.warning(f"Invalid edge found in filament {i}: ({p1}, {p2}) - Max index is {N-1}")


            # SWC conversion using Breadth-First Search (BFS) or Depth-First Search (DFS)
            # We need to handle potential disconnections and find a root.
            # Let's assume the first point (index 0) is a potential root,
            # but handle cases where the filament might be disconnected.
            # We'll use BFS here.

            swc_lines = np.zeros((N, 7))
            visited = np.zeros(N, dtype=bool)
            node_map = {} # Map original Imaris index to new SWC index (1-based)
            parent_map = {} # Map original Imaris index to SWC parent index (-1 for root)
            swc_idx_counter = 1
            nodes_processed = 0

            # Handle potentially disconnected components
            for start_node_idx in range(N):
                if not visited[start_node_idx]:
                    logging.debug(f"Starting traversal from node {start_node_idx} (potential new root)")
                    queue = [(start_node_idx, -1)] # (imaris_idx, swc_parent_idx)
                    visited[start_node_idx] = True

                    while queue:
                        cur_imaris_idx, current_swc_parent_idx = queue.pop(0) # BFS

                        # Assign current node its SWC index
                        current_swc_idx = swc_idx_counter
                        node_map[cur_imaris_idx] = current_swc_idx
                        parent_map[cur_imaris_idx] = current_swc_parent_idx
                        swc_idx_counter += 1

                        # Get position, radius, type
                        pos = np.array(vFilamentsXYZ[cur_imaris_idx]) - pixel_offset
                        scaled_pos = pos * pixel_scale
                        radius = vFilamentsRadius[cur_imaris_idx]
                        # Use default type 3 (axon) if types array is empty or invalid
                        node_type = vFilamentsTypes[cur_imaris_idx] if vFilamentsTypes and cur_imaris_idx < len(vFilamentsTypes) else 3

                        # Create SWC line (indices filled later)
                        swc_lines[nodes_processed] = [
                            current_swc_idx, node_type,
                            scaled_pos[0], scaled_pos[1], scaled_pos[2],
                            radius, current_swc_parent_idx
                        ]
                        nodes_processed += 1

                        # Add neighbors to queue
                        for neighbor_imaris_idx in adj[cur_imaris_idx]:
                            if not visited[neighbor_imaris_idx]:
                                visited[neighbor_imaris_idx] = True
                                queue.append((neighbor_imaris_idx, current_swc_idx)) # Parent is the current node's SWC index

            if nodes_processed != N:
                 logging.warning(f"Filament {i}: Processed {nodes_processed} nodes, but expected {N}. Possible isolated nodes?")
                 # Truncate swc_lines if needed, though usually N should match
                 swc_lines = swc_lines[:nodes_processed]


            # --- Save individual filament ---
            # Use the modified base name
            filename_filament = f"{base_name}_filament_{i}.swc"
            print(f'Exporting filament {i+1}/{vCount} to {filename_filament}') # Use standard print for user feedback
            logging.info(f"Saving individual filament {i} to {filename_filament}")
            # Define the format string explicitly for clarity
            swc_format = '%d %d %.6f %.6f %.6f %.6f %d'
            np.savetxt(filename_filament, swc_lines, fmt=swc_format, delimiter=' ')
            all_filaments_swc_data.append(swc_lines) # Add to the list for combined saving

        # --- Combine and save all filaments ---
        if all_filaments_swc_data:
            # Correctly merge SWC files: re-index node IDs and parent IDs
            logging.info("Combining SWC data for final output file...")
            final_swc_data = []
            node_offset = 0
            for swc_data in all_filaments_swc_data:
                if swc_data.shape[0] > 0: # If the filament wasn't empty
                    temp_data = swc_data.copy()
                    # Update node index (column 0)
                    temp_data[:, 0] += node_offset
                    # Update parent index (column 6), ignoring roots (-1)
                    parent_mask = temp_data[:, 6] != -1
                    temp_data[parent_mask, 6] += node_offset
                    final_swc_data.append(temp_data)
                    node_offset += swc_data.shape[0] # Increment offset by number of nodes in this filament

            if final_swc_data:
                combined_swcs = np.vstack(final_swc_data)
                logging.info(f"Saving combined SWC data ({combined_swcs.shape[0]} nodes) to {savename}")
                print(f"\nSaving combined file with all filaments to: {savename}")
                swc_format = '%d %d %.6f %.6f %.6f %.6f %d'
                np.savetxt(savename, combined_swcs, fmt=swc_format, delimiter=' ')
                logging.info("Combined SWC file saved successfully.")
            else:
                 logging.warning("No valid filament data found to combine.")
                 print("\nWarning: No filament data was generated to save in the combined file.")
        else:
             logging.warning("No individual filaments were successfully processed.")
             print("\nWarning: No individual filaments processed, combined file will not be saved.")


        print("\nScript finished successfully!")
        logging.info("--- Script Finished Successfully ---")
        messagebox.showinfo("Success", f"SWC export finished successfully!\nLog file: {log_file_path}")


    except Exception as e:
        # Log the full error traceback to the log file
        logging.error("An unexpected error occurred:")
        logging.error(traceback.format_exc()) # This logs the full traceback

        # Show a user-friendly error message
        print(f"\n--- ERROR ---")
        print(f"An error occurred: {e}")
        print(f"Please check the log file for details: {log_file_path}")
        print(f"Error type: {type(e).__name__}")
        messagebox.showerror("Script Error",
                             f"An error occurred:\n{e}\n\n"
                             f"See log file for details:\n{log_file_path}")
        logging.error("--- Script Terminated Due to Error ---")


    finally:
        # This block will always execute, whether an error occurred or not.
        print("\nExecution complete (or an error occurred).")
        input("Press Enter in this window to close...") # Keep the window open
        logging.info("--- Terminal Window Closing ---")