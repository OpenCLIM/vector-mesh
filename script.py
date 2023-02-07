import geopandas as gpd
import pandas as pd
import os
import shutil
import subprocess
from zipfile import ZipFile
from glob import glob
from os.path import isfile, join, isdir
from os import listdir, getenv, mkdir, remove, walk
import json
import math

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
# buildings_path = os.path.join(outputs_path,'buildings')
# buildings_path_ = outputs_path + '/' + 'buildings'
# if not os.path.exists(buildings_path):
#     os.mkdir(buildings_path_)

location = os.getenv('LOCATION')

vector_output = os.path.join(outputs_path, location + '.gpkg')

# Identify input polygons and shapes (boundary of city, and OS grid cell references)
boundary = glob(boundary_path + "/*.*", recursive = True)
boundary = gpd.read_file(boundary[0])
grid = glob(grids_path + "/*_5km.gpkg", recursive = True)
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


# The next set of code takes the output gpkg and clips it to the original boundary.

def check_output_dir(path):
    """
    Check output directory exists and create if not
    """
    if isdir(path) is False:
        mkdir(path)
    else:
        files = [f for f in listdir(path) if isfile(join(path, f))]
        for file in files:
            remove(join(path,file))
    return


def output_file_name(input_path, output_name, number_of_input_files):
    """
    Set the name for the output file from each clip process
    If more than 1 input file to be clipped, default behaviour should be used
    If only one input file passed, and output file name not set, use default behavior
    If only one input file passed, and the output file name is passed, use output file name
    """
    input_path, input_extension = input_path.split('.')
    input_name = input_path.split('/')[-1]
    if number_of_input_files > 1 or output_name is None:
        output_file = input_name + '_clip.' + input_extension
    else:
        output_file = output_name

    return output_file


def fetch_clip_file():
    """
    Check the clip extents directory for a file to clip the input data with.
    Return None is no file found.
    """
    clip_file = []  # set in case no file is passed
    extensions = ['gpkg', 'shp', 'txt']
    for extension in extensions:

        for file in glob(join(boundary_path, "*.%s" % extension)):
            clip_file.append(file)

    return clip_file


def get_data_type(file, vector_types, raster_types):
    """
    Get the data type, raster or vector, of the clip file
    """

    # get the file extension to identify data type
    extension_text = file.split('.')[-1]

    # set the data type
    if extension_text in raster_types:
        return 'raster'
    elif extension_text in vector_types:
        return 'vector'
    else:
        return None


def filter_input_files(input_file_list, file_extensions):
    """
    Get those files from the list of input files where the file extensions is recognised as a raster or vector data type
    """
    verified_file_list = []

    # loop through the files
    for file in input_file_list:
        # fetch file extension
        file_extension = file.split('.')[-1].lower()

        # check if file extension in defined set of usable file types
        if file_extension in file_extensions:
            verified_file_list.append(file)

    return verified_file_list


def find_extents_file(name, path):
    for root, dirs, files in walk(path):
        if name in files:
            return join(root, name)
            

def get_crs_of_data(file, vector=False):
    """
    Find the crs of the file. Checks that it exists and return it for any further required checks.
    """
    print('vector:',vector)
    if vector is False:
        info = subprocess.run(["gdalinfo", "-json", file], stdout=subprocess.PIPE)#.stdout.splitlines()
        print('**********')
        #print(info.stdout.decode("utf-8"))
        info = info.stdout.decode("utf-8")
        #info = info.replace('\n','')
        info_ = json.loads(info)
        #print(info_.keys())
        if 'coordinateSystem' in info_.keys():
            proj = info_['coordinateSystem']['wkt'].split(',')[0].replace('PROJCRS[', '').replace('"', '')
        else:
            # no projection information available
            proj = None

    elif vector is True:
        info = subprocess.run(["ogrinfo", "-ro", "-so", "-al", file], stdout=subprocess.PIPE)#, "glasgow_city_centre_lad"])
        proj = 27000
        info = info.stdout
        info = info.decode("utf-8").split('\n')
        for line in info:
            if 'PROJCRS' in line:
                proj = line.replace('PROJCRS[', '').replace('"', '').replace(',', '')

    return proj

# Round minima down and maxima up to nearest km
def round_down(val, round_val):
    """Round a value down to the nearst value as set by the round val parameter"""
    return math.floor(val / round_val) * round_val


def round_up(val, round_val):
    """Round a value up to the nearst value as set by the round val parameter"""
    return math.ceil(val / round_val) * round_val


def round_bbox_extents(extents, round_to):
    """Round extents
    extents: a list of 4 values which are the 2 corners/extents of a layer
    rount_to: an integer value in base 0 in meters to round the extents too
    """
    print('^^^^^')
    print('In round bbox extents method.')
    print('Extents to round are: %s' %extents)
    print('Rounding to extents to: %s' %round_to)
    print('^^^^^')

    xmin = round_down(extents[0], round_to)
    ymin = round_down(extents[2], round_to)
    xmax = round_up(extents[1], round_to)
    ymax = round_up(extents[3], round_to)

    return [xmin, xmax, ymin, ymax]

# list of default options
defaults = {
    'output_crs': '27700',
    'crs_bng' : 'OSGB 1936 / British National Grid',
    'cut_to_bounding_box': True
}

# list of accepted file types for data being clipped
raster_accepted = ['asc', 'tiff', 'geotiff', 'jpeg']
vector_accepted = ['shp', 'gpkg', 'geojson']

## START SETTING UP THE PARAMETERISATION
# Search for input files whicha re to be clipped
input_files = []
# loop through the input/clip director for files and files in sub folders
for root, dirs, files in walk(outputs_path):
    for file in files:
        # record any files found
        input_files.append(join(root,file))

# if no input files found, terminate
if len(input_files) == 0:
    print('Error! No input files found! Terminating')
    exit(2)

# filter the input files to check that are valid
input_files = filter_input_files(input_files, vector_accepted+raster_accepted)
if len(input_files) == 0:
    print('Error! No input files given specified data format! Terminating!')
    exit(2)

print('Verified input files: %s' %input_files)

# get extents for clip - file or defined extents
# check the data slot (inputs/clip_extent) for a spatial file
clip_file = fetch_clip_file()
if len(clip_file) > 0:
    pass
else:
    clip_file = None
print('Clip files is:', clip_file)

# check if file passed from previous step and in a different folder than expected
outcome = [find_extents_file('extents.txt', data_path)]
print('Outcome:',outcome)
if outcome[0] is not None:
    clip_file = outcome
    print(clip_file)

# defined extents
# a user may pass some defined extents as text. these are only used
# if no other method identified from the files found
extent = None
if clip_file is None or len(clip_file) == 0: #if not files passed expect an env to be passed defining the extents
    extent = getenv('extent')
    if extent == '' or extent == 'None': # if no extent passed
        extent = None
    
    print('Extent: %s' % extent)


# if no extent string set, presume file is passed and read in. if no file, return an error and exit
if extent is None and len(clip_file) == 1 and clip_file != None:
    # if a text bounds file passed, convert to extent text so can use that existing method
    # xmin,ymin,xmax,ymax
    print('Reading extents file')
    cf_ext = clip_file[0].split('.')[1]
    print('cf_ext:',cf_ext)
    if cf_ext == 'txt':
        with open(clip_file[0]) as ef:
            extent = ef.readline()
        clip_file = None

print('Extent set as:', extent)
print('Clip file is:', clip_file)

# no data to allow a file to be clipped has been found. exit.
if extent is None and clip_file is None:
    # if neither a clip file set or an extent passed
    print('Error! No clip_file var or extent var passed. Terminating!')
    exit(2)

# check if the clip file is still in a list format - it no longer needs to be
if clip_file is not None and len(clip_file) > 0:
    clip_file = clip_file[0]

# GET USER SENT PARAMETERS
# CLIP_TO_EXTENT_BOX
# get if cutting to shapefile or bounding box of shapefile (if extent shapefile passed)
#clip_to_extent_bbox = getenv('clip_to_extent_bbox')
clip_to_extent_bbox = 'clip-to-bounding-box'
if clip_to_extent_bbox is None:
    cut_to_bounding_box = defaults['cut_to_bounding_box']
elif clip_to_extent_bbox == 'clip-to-bounding-box':
    cut_to_bounding_box = True
elif clip_to_extent_bbox == 'clip-to-vector-outline':
    cut_to_bounding_box = False
else:
    print(clip_to_extent_bbox)

# OUTPUT_FILE
# this is only used if a single input file is passed
#output_file = getenv('output_file')
output_file = None
print('Output file: %s' % output_file)
if len(input_files) > 1:
    output_file = None
elif output_file is None or output_file == 'None':
    output_file = None
elif output_file[0] == '' or output_file == '[]': # needed on DAFNI
    print('Warning! Empty output file var passed.')
    output_file = None

## START SETTING UP THE PARAMETERISATION
# Search for input files whicha re to be clipped
input_files = []
# loop through the input/clip director for files and files in sub folders
for root, dirs, files in walk(outputs_path):
    for file in files:
        # record any files found
        input_files.append(join(root,file))

# if no input files found, terminate
if len(input_files) == 0:
    print('Error! No input files found! Terminating')
    exit(2)

# filter the input files to check that are valid
input_files = filter_input_files(input_files, vector_accepted+raster_accepted)
if len(input_files) == 0:
    print('Error! No input files given specified data format! Terminating!')
    exit(2)

print('Verified input files: %s' %input_files)

# get extents for clip - file or defined extents
# check the data slot (inputs/clip_extent) for a spatial file
clip_file = fetch_clip_file()
if len(clip_file) > 0:
    pass
else:
    clip_file = None
print('Clip files is:', clip_file)

# check if file passed from previous step and in a different folder than expected
outcome = [find_extents_file('extents.txt', data_path)]
print('Outcome:',outcome)
if outcome[0] is not None:
    clip_file = outcome
    print(clip_file)

# defined extents
# a user may pass some defined extents as text. these are only used
# if no other method identified from the files found
extent = None
if clip_file is None or len(clip_file) == 0: #if not files passed expect an env to be passed defining the extents
    extent = getenv('extent')
    if extent == '' or extent == 'None': # if no extent passed
        extent = None
    
    print('Extent: %s' % extent)


# if no extent string set, presume file is passed and read in. if no file, return an error and exit
if extent is None and len(clip_file) == 1 and clip_file != None:
    # if a text bounds file passed, convert to extent text so can use that existing method
    # xmin,ymin,xmax,ymax
    print('Reading extents file')
    cf_ext = clip_file[0].split('.')[1]
    print('cf_ext:',cf_ext)
    if cf_ext == 'txt':
        with open(clip_file[0]) as ef:
            extent = ef.readline()
        clip_file = None

print('Extent set as:', extent)
print('Clip file is:', clip_file)

# no data to allow a file to be clipped has been found. exit.
if extent is None and clip_file is None:
    # if neither a clip file set or an extent passed
    print('Error! No clip_file var or extent var passed. Terminating!')
    exit(2)

# check if the clip file is still in a list format - it no longer needs to be
if clip_file is not None and len(clip_file) > 0:
    clip_file = clip_file[0]

# GET USER SENT PARAMETERS
# CLIP_TO_EXTENT_BOX
# get if cutting to shapefile or bounding box of shapefile (if extent shapefile passed)
#clip_to_extent_bbox = getenv('clip_to_extent_bbox')
clip_to_extent_bbox = 'clip-to-bounding-box'
if clip_to_extent_bbox is None:
    cut_to_bounding_box = defaults['cut_to_bounding_box']
elif clip_to_extent_bbox == 'clip-to-bounding-box':
    cut_to_bounding_box = True
elif clip_to_extent_bbox == 'clip-to-vector-outline':
    cut_to_bounding_box = False
else:
    print(clip_to_extent_bbox)

# OUTPUT_FILE
# this is only used if a single input file is passed
#output_file = getenv('output_file')
output_file = None
print('Output file: %s' % output_file)
if len(input_files) > 1:
    output_file = None
elif output_file is None or output_file == 'None':
    output_file = None
elif output_file[0] == '' or output_file == '[]': # needed on DAFNI
    print('Warning! Empty output file var passed.')
    output_file = None

# END OF PARAMETER FETCHING
# START RUNNING THE PROCESSING

round_extents = 1000

# loop through each file to clip
for input_file in input_files:

    print('Input file is: %s' % input_file)
    # set the data type
    data_type = get_data_type(input_file, vector_types=vector_accepted, raster_types=raster_accepted)

    # get the crs of the input file
    input_crs = get_crs_of_data(input_file,True)
    if input_crs is None:
        print('Warning! No projection information could be found for the input file.')
        input_crs = defaults['crs_bng']
        print('Warning! Using default projection (british national grid) for input file.')
		
    print('Input CRS is: %s' % input_crs)

    # run clip process
    if data_type is None:
        print('Error. Data type is None')

    elif data_type == 'vector':
        print('Running vector clip')

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))
	print('Output_file_name_set:',output_file_name_set)

        if clip_file is not None:
            subprocess.run(["ogr2ogr", "-clipsrc", clip_file, "-f", "GPKG",
                            output_file_name_set, input_file])

        elif extent is not None:
            print('Running extent method')

            if round_extents is not False:
                print('Rounding extents')
                extent = round_bbox_extents(extent, round_extents)

            subprocess.run(["ogr2ogr", "-spat", *extent, "-f", "GPKG", output_file_name_set,
                            input_file])

    elif data_type == 'raster':
        print('Running raster clip')
        print('Running for input:', input_file)

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))
        print('output_file_name_set:',output_file_name_set)

        if extent is not None:
            print('Using extent method')
            print('Extents are: %s' %extent)

            if round_extents is not False:
                print('Rounding extents')
                extent = round_bbox_extents(extent, round_extents)

            print('Running subprocess')
            extents = extent.split(",")
            subprocess.run(["gdalwarp", "-te", extents[0], extents[1], extents[2], extents[3], input_file, output_file_name_set])

        elif clip_file is not None and len(clip_file) > 0:
            print("Using clip file method")

            # get crs of clip file
            print('clip_file:',clip_file)
            clip_crs = get_crs_of_data(clip_file, vector=True)

            # if crs could not be found, return error
            if clip_crs is None:
                print('Error! No projection information could be found for the clip file.')
                exit()

            # need to check crs of clip file is same as that for the data being clipped
            if clip_crs != input_crs:
                print("Error! CRS of datasets do not match!!! (input: %s ; clip: %s)" %(input_crs, clip_crs))
                exit()

            if cut_to_bounding_box is False:
                # crop to the shapefile, not just the bounding box of the shapefile
                print('Clipping with cutline flag')
                command_output = subprocess.run(["gdalwarp", "-cutline", clip_file, "-crop_to_cutline", input_file,
                     output_file_name_set])

            else:
                print('clipping with bounding box of vector data')
          
                print(input_file)
                print(output_file_name_set)

                # read in shapefile
                t = gpd.read_file(clip_file)
                # get bounding box for shapefile
                bounds = t.geometry.total_bounds

                if round_extents is not False:
                    print('Rounding extents')
                    print(bounds, round_extents)
                    bounds = round_bbox_extents(bounds, round_extents)

                print('Using bounds:', bounds)
                # run clip
                subprocess.run(["gdalwarp", "-te", str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]), input_file, output_file_name_set])

            # add check to see if file written to directory as expected
            if isfile(output_file_name_set):
                print('Clip completed and file written (%s)' % output_file_name_set)
            else:
                print("Failed. Expected output not found (%s)" % output_file_name_set)


# check output file is written...... and if not return an error?
files = [f for f in listdir(outputs_path) if
         isfile(join(outputs_path, f))]
print('Files in output dir: %s' % files)

print('Completed running clip')

# Remove unclipped file
os.remove(input_file)

# # Move the clipped file into a new folder and remove the _clip
# src=os.path.join(outputs_path, location + '_clip.gpkg')
# dst=os.path.join(buildings_path, location + '.gpkg')
# shutil.copy(src,dst)

# # Remove duplicate file
# os.remove(join(outputs_path, location + '_clip.gpkg'))
