import geopandas as gpd
import pandas as pd
import os
from zipfile import ZipFile
from glob import glob

# Define Data Paths
data_path = os.getenv('DATA_PATH', '/data')
inputs_path = os.path.join(data_path,'inputs')
grids_path = os.path.join(inputs_path,'grids')
boundary_path = os.path.join(inputs_path,'boundary')
outputs_path = os.path.join(data_path, 'outputs')
outputs_path_ = data_path + '/' + 'outputs'
if not os.path.exists(outputs_path):
    os.mkdir(outputs_path_)
vector_path = os.path.join(inputs_path, 'vectors')

location = os.getenv('LOCATION')

vector_output = os.path.join(outputs_path, location + '.gpkg')
print(vector_output)

# Identify input polygons and shapes (boundary of city, and OS grid cell references)
boundary = glob(boundary_path + "/*.*", recursive = True)
boundary = gpd.read_file(boundary[0])
print(boundary)
grid = glob(grids_path + "/*_5km.gpkg", recursive = True)
grid = gpd.read_file(grid[0])
print(grid)

# Ensure all of the polygons are defined by the same crs
boundary.set_crs(epsg=27700, inplace=True)
grid.set_crs(epsg=27700, inplace=True)

# Identify which of the 5km OS grid cells fall within the chosen city boundary
cells_needed = gpd.overlay(boundary,grid, how='intersection')
list = cells_needed['tile_name']
print(list)

# Identify which of the 100km OS grid cells fall within the chosen city boundary 
# This will determine which folders are needed to retrieve the DTM for the area

check=[]
check=pd.DataFrame(check)
check['cell_code']=['AAAAAA' for n in range(len(list)-1)]
a_length = len(list[2])
cell='A'

# Look at each 5km cell that falls in the area and examine the first two digits
for i in range(0,len(list)-1):
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

print(files_to_unzip)

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
    
print(archive)

# Create a list of all of the gpkgs to be merged
to_merge=[]
to_merge=['XX' for n in range(len(archive))]
for i in range (0,len(archive)):
    file_path = os.path.splitext(archive[i][0])
    filename=file_path[0].split("\\")
    to_merge[i]=filename[8]+'.gpkg'

# Create a geodatabase and merge the data from each gpkg together
original = []
original=gpd.GeoDataFrame(original)
for cell in to_merge:
    gdf = gpd.read_file('\data\inputs\vectors\%s' %cell)
    original = pd.concat([gdf, original],ignore_index=True)

# Print to a gpkg file
original.to_file(os.path.join(vector_output),driver='GPKG',index=False)
