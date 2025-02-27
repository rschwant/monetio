"""GOES PM2.5 Surface Product File Reader"""

import warnings

import numpy as np
import xarray as xr
from numpy import meshgrid
import pandas as pd

def open_mfdataset(
    fname,
    direction,
    files_meta=None,
    var_list=["pm25sat_ge" , "pm25sat_gw"],
    **kwargs,
):
    """Method to open multiple (or single) GOES PM2.5 netcdf files.
       This method extends the xarray.open_mfdataset functionality
       It is the main method called by the driver. Other functions defined
       in this file are internally called by open_mfdataset and are proceeded
       by an underscore (e.g. _ensure_mfdataset_filenames).

    Parameters
    ----------
    fname : string or list
        fname is the path to the file or files.  It will accept wildcards in
        strings as well.
    files_meta : string or list
        fname is the path to the file containing the meta data for the 
        GOES PM2.5 product: https://www.star.nesdis.noaa.gov/atmospheric-composition-training/satellite_data_goes_imager_projection.php
    direction : string
        direction is the position of the GOES satellite product.
        It will accept "west" or "east". 
    var_list : string or list
        List of variables to load from the GOES PM2.5 netcdf file. 
        Default is to load PM2.5 west and east. 

    Returns
    -------
    xarray.Dataset
    """

    # check that the files are netcdf format
    names, netcdf = _ensure_mfdataset_filenames(fname)
    
    # open the dataset using xarray
    try:
        if netcdf:
            dset_list = []
            for file_n in fname:
                # open the dataset using xarray
                dset = xr.open_mfdataset(file_n, **kwargs)
                # add the times
                dset["time"] = [pd.Timestamp(file_n[-13:-9]+"-"+file_n[-9:-7]
                                        +"-"+file_n[-7:-5]+"T"+file_n[-5:-3])]
                dset_list.append(dset)
                dset = xr.concat(dset_list, "time")
        else:
            raise ValueError
    except ValueError:
        print(
            """File format not recognized. Note that files should be in netcdf
                format. Do not mix and match file types."""
        )
    
    #############################
    # Process the loaded data
    
    #optionally replace meta data
    if files_meta is not None:
        names_meta, netcdf_meta = _ensure_mfdataset_filenames(files_meta)
        
        # open the meta dataset using xarray
        try:
            if netcdf_meta:
                dset_meta = xr.open_mfdataset(files_meta, **kwargs)
            else:
                raise ValueError
        except ValueError:
            print("""File format not recognized. Note that files should be in netcdf
                format. Do not mix and match file types. This file should be the meta data for GOES PM2.5: 
                https://www.star.nesdis.noaa.gov/atmospheric-composition-training/satellite_data_goes_imager_projection.php""")
        #Replace the meta data, so there are no NaNs
        dset["lon_gw"] = dset_meta["lon_gw"]
        dset["lon_ge"] = dset_meta["lon_ge"]
        dset["lat_gw"] = dset_meta["lat_gw"]
        dset["lat_ge"] = dset_meta["lat_ge"]
    
    # extract variables of choice
    dset = dset.get(var_list)
        
    try:
        if direction == "west":
            dset = dset.rename_dims({"xdim_gw": "x", "ydim_gw": "y"})
            dset = dset.rename({"lon_gw": "longitude", "lat_gw": "latitude"})
        elif direction == "east":
            dset = dset.rename_dims({"xdim_ge": "x", "ydim_ge": "y"})
            dset = dset.rename({"lon_ge": "longitude", "lat_ge": "latitude"})
        else:
            raise ValueError
    except ValueError:
        print(
            """Only west and east are accepted inputs for direction. Please update, thank you."""
        )
    
    #Expand fake z dimension 
    dset = dset.expand_dims("z", axis=1)
    #############################

    return dset


# -----------------------------------------
# Below are internal functions to this file
# -----------------------------------------


def _ensure_mfdataset_filenames(fname):
    """Checks if dataset in netcdf format

    Parameters
    ----------
    fname : string or list of strings

    Returns
    -------
    type
    """
    from glob import glob

    from numpy import sort

    if isinstance(fname, str):
        names = sort(glob(fname))
    else:
        names = sort(fname)
    netcdfs = [True for i in names if "nc" in i]
    netcdf = False
    if len(netcdfs) >= 1:
        netcdf = True
    return names, netcdf