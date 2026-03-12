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

cartella_download = f'{cartella_lavoro}/ERA5_annuali'
os.makedirs(cartella_download, exist_ok=True)

lista_anni = np.arange(1940, 2024)

for anno in lista_anni: # non riesce a scaricare 2022 e 2023
    print(f'Anno = {anno}')
    
    if os.path.exists(f'{cartella_download}/ERA5_{anno}.nc'):
        print(f'\n{cartella_download}/ERA5_{anno}.nc esiste già. Continuo\n')
        continue

    else:

        dataset = "reanalysis-era5-single-levels"
        request = {
            "product_type": ["reanalysis"],
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "mean_sea_level_pressure",
                "significant_height_of_combined_wind_waves_and_swell"
            ],
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
            "time": [
                "00:00", "03:00", "06:00",
                "09:00", "12:00", "15:00",
                "18:00", "21:00"
            ],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": [55, -10, 34, 20]
        }
    
        target = f'{cartella_download}/ERA5_{anno}.nc'
    
        client = cdsapi.Client()
    
        client.retrieve(dataset, request, target)

print('\n\nDone')
