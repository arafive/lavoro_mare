"""Download dei dati CERRA da Copernicus"""

import os
import cdsapi

import numpy as np

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

# %%

cartella_download = f'{cartella_lavoro}/CERRA_annuali'
os.makedirs(cartella_download, exist_ok=True)

lista_anni = np.arange(1985, 2021)[::-1]

for anno in lista_anni:
    print('Anno = {anno}')
    
    if os.path.exists(f'{cartella_download}/CERRA_{anno}.nc'):
        print(f'{cartella_download}/CERRA_{anno}.nc esiste. Continuo.')
        continue
    
    dataset = "reanalysis-cerra-single-levels"
    request = {
        "variable": [
            "mean_sea_level_pressure",
        ],
        "level_type": "surface_or_atmosphere",
        "data_type": ["reanalysis"],
        "product_type": "analysis",
        "year": [f"{anno}"],
        "month": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12"
        ],
        "day": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12",
            "13", "14", "15",
            "16", "17", "18",
            "19", "20", "21",
            "22", "23", "24",
            "25", "26", "27",
            "28", "29", "30",
            "31"
        ],
        "time": ["00:00", "03:00", "06:00",
                 "09:00", "12:00", "15:00",
                 "18:00", "21:00"
         ],
        "data_format": "netcdf"
    }

    target = f'{cartella_download}/CERRA_{anno}.nc'

    client = cdsapi.Client()
    
    client.retrieve(dataset, request, target)

print('\n\nDone')
    
