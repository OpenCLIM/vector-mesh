import geopandas as gpd
import pandas as pd
import os
import shutil
from zipfile import ZipFile
from glob import glob
import subprocess

# Define Data Paths
data_path = os.getenv('DATA_PATH', '/data')
inputs_path = os.path.join(data_path,'inputs')
grids_path = os.path.join(inputs_path,'grids')
boundary_path = os.path.join(inputs_path,'boundary')
outputs_path = os.path.join(data_path, 'outputs')
outputs_path_ = data_path + '/' + 'outputs'
if not os.path.exists(outputs_path):
    os.mkdir(outputs_path_)
buildings_path = os.path.join(outputs_path, 'buildings')
buildings_path_ = outputs_path + '/' + 'buildings'
if not os.path.exists(buildings_path):
    os.mkdir(buildings_path_)
vector_path = os.path.join(inputs_path, 'vectors')


# Identify input polygons and shapes (boundary of city, and OS grid cell references)
boundary_1 = glob(boundary_path + "/*.*", recursive = True)
print('Boundary File:',boundary_1)

# Identify the name of the boundary file for the city name
file_path = os.path.splitext(boundary_1[0])
print('File_path:',file_path)
filename=file_path[0].split("/")
print('filename:',filename)
location = filename[-1]
print('Location:',location)

vector_output = os.path.join(outputs_path, location + '.gpkg')
print('Vector Output File Name:', vector_output)

boundary = gpd.read_file(boundary_1[0])
grid = glob(grids_path + "/*_5km.gpkg", recursive = True)
print('Grid File:',grid)
grid = gpd.read_file(grid[0])

# Ensure all of the polygons are defined by the same crs
boundary.set_crs(epsg=27700, inplace=True)
grid.set_crs(epsg=27700, inplace=True)

# Identify which of the 5km OS grid cells fall within the chosen city boundary
cells_needed = gpd.overlay(boundary,grid, how='intersection')
list = cells_needed['tile_name']

# Identify which of the 100km OS grid cells fall within the chosen city boundary 
# This will determine which folders are needed to retrieve the DTM for the area

check=[]
check=pd.DataFrame(check)
check['cell_code']=['AAAAAA' for n in range(len(list))]
a_length = len(list[0])
cell='A'

# Look at each 5km cell that falls in the area and examine the first two digits
for i in range(0,len(list)):
    cell=list[i]
    check.cell_code[i] = cell[a_length - 6:a_length - 4]

# Remove any duplicates, reset the index - dataframe for the 100km cells
grid_100 = check.drop_duplicates()
grid_100.reset_index(inplace=True, drop=True)

# Create a dataframe for the 5km cells
grid_5=cells_needed['tile_name']
grid_5=pd.DataFrame(grid_5)

# Establish which zip files need to be unzipped
files_to_unzip=[]
files_to_unzip=pd.DataFrame(files_to_unzip)
files_to_unzip=['XX' for n in range(len(grid_100))]
for i in range(0,len(grid_100)):
    name=grid_100.cell_code[i]
    name_path = os.path.join(vector_path, name + '.zip')
    files_to_unzip[i] = name_path

# Unzip the required files
for i in range (0,len(files_to_unzip)):
    if os.path.exists(files_to_unzip[i]) :
        with ZipFile(files_to_unzip[i],'r') as zip:
            # extract the files into the inputs directory
            zip.extractall(vector_path)

# Create a list of each grid cell that lies within the boundary (which gpkg are we looking for)
grid_5['file_name'] = grid_5['tile_name']+'.gpkg'
archive=[]
archive=pd.DataFrame(archive)
archive=['XX' for n in range(len(grid_5))]

# Check if the gpkgs for each cell exist
for i in range(0,len(grid_5)):
    name = grid_5.file_name[i]
    path = glob(vector_path + '/**/' + name, recursive=True)
    archive[i] = path

# Remove the empty grid cells from the list
while([] in archive):
    archive.remove([])

# Create a list of all of the gpkgs to be merged
to_merge=[]
to_merge=['XX' for n in range(len(archive))]
for i in range (0,len(archive)):
    file_path = os.path.splitext(archive[i][0])
    filename=file_path[0].split("/")
    to_merge[i]=filename[4]+'.gpkg'

# Create a geodatabase and merge the data from each gpkg together
original = []
original=gpd.GeoDataFrame(original)
for cell in to_merge:
    gdf = gpd.read_file('/data/inputs/vectors/%s' %cell)
    original = pd.concat([gdf, original],ignore_index=True)

# Print to a gpkg file
original.to_file(os.path.join(vector_output),driver='GPKG',index=False)

print('Running vector clip')

vector = gpd.read_file(vector_output)
clipped = gpd.clip(vector,boundary)

# Print to a gpkg file
clipped.to_file(os.path.join(outputs_path, location + '_clip.gpkg'),driver='GPKG',index=False)

# Remove unclipped file
os.remove(vector_output)

# Move the clipped file into a new folder and remove the _clip
src=os.path.join(outputs_path, location + '_clip.gpkg')
dst=os.path.join(buildings_path, location + '.gpkg')
shutil.copy(src,dst)

# Remove duplicate file
os.remove(os.path.join(outputs_path, location + '_clip.gpkg'))
