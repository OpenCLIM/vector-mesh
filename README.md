# vector-mesh
This model takes national scale datasets and clips them to a geographical area.

## Description
National scale datasets are too large to upload onto DAFNI, and processing these large datasets is time extensive. Models such as City Catchment Analysis Tool,
require vector data from the national datasets for a city of interest. The national data sets have been uploaded onto DAFNI in zip format for each 100km OS grid cell. 
Geopackage files within the zip folders contain the vector data per 5km OS grid cell. This model identifies which 5km grid cells are contained within the boundary 
file for the city of interest, and merges the geopackage to generate a single gpkg file for the city.

## Input Parameters
*Location
  * Description: The name of the place of interest outlinned by the boundary file.


## Input Files (data slots)
* Vectors
  * Description: Any required vector files (buildings, greenspaces etc.) These should be saved in files of 5km OS grid cells, and zipped at the 100m grid cell level.
  * Location: /data/vectors
* Boundary
  * Description: A .gpkg of the geographical area of interest. 
  * Location: /data/boundary
* Grids
  * Description: A .gpkg of the OS British National Grid cells.
  * Location: /data/grids

## Outputs
The model should output only one file - a .gpkg file of the chosen area containing the vectors of interest.