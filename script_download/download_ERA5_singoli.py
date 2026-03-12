
import os
import cdsapi

import pandas as pd

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

# %%

cartella_download = f'{cartella_lavoro}/ERA5_singoli'
os.makedirs(cartella_download, exist_ok=True)

lista_range_tempi = [
    ['1948-01-26', '1948-01-29'],
    ['1952-12-16', '1952-12-18'],
    ['1953-02-09', '1953-02-12'],
    ['1955-02-17', '1955-02-21'],
    ['1957-02-17', '1957-02-19'],
    ['1962-12-14', '1962-12-17'],
    ['1968-01-06', '1968-01-08'],
    ['1974-02-05', '1974-02-08'],
    ['1976-11-30', '1976-12-06'],
    ['1978-12-30', '1979-01-02'],
    ['1979-03-15', '1979-03-18'],
    ['1981-12-06', '1981-12-11'],
    ['1981-12-13', '1981-12-19'],
    ['1986-01-22', '1986-01-25'],
    ['1989-02-24', '1989-03-02'],
    ['1990-02-12', '1990-02-17'],
    ['1990-02-25', '1990-03-01'],
    ['1992-03-22', '1992-03-25'],
    ['1996-11-18', '1996-11-22'],
    ['1999-02-07', '1999-02-11'],
    ['1999-12-24', '1999-12-28'],
    ['1999-12-26', '1999-12-30'],
    ['2000-11-05', '2000-11-10'],
    ['2001-11-07', '2001-11-10'],
    ['2002-02-19', '2002-02-22'],
    ['2003-02-02', '2003-02-05'],
    ['2006-03-02', '2006-03-06'],
    ['2007-02-28', '2007-03-03'],
    ['2008-03-20', '2008-03-23'],
    ['2008-10-28', '2008-11-01'],
    ['2008-11-28', '2008-12-03'],
    ['2011-12-14', '2011-12-18'],
    ['2015-11-19', '2015-11-22'],
    ['2019-12-20', '2019-12-24'],
    ['2021-01-21', '2021-01-26'],
    ['2023-11-01', '2023-11-07'],
    ['2024-11-18', '2024-11-24'],
    ['2025-01-26', '2025-01-30']
]

for int_tempi in lista_range_tempi:

    sub_cartella_download = f"{cartella_download}/ciclone_{int_tempi[0].replace('-', '_')}"
    os.makedirs(sub_cartella_download, exist_ok=True)

    range_tempo = pd.date_range(pd.to_datetime(int_tempi[0]), pd.to_datetime(int_tempi[1]) + pd.DateOffset(days=1), freq='1D')

    for t in range_tempo:
        print(f'{int_tempi} · t = {t}')

        dataset = "reanalysis-era5-single-levels"
        request = {
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "mean_sea_level_pressure",
                "surface_pressure"
            ],
            "product_type": ["reanalysis"],
            "year": [f'{t.year}'],
            "month": [f'{t.month:02d}'],
            "day": [f'{t.day:02d}'],
            "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "area": [55, -10, 34, 20],
            "download_format": "unarchived",
            "data_format": "netcdf"
        }

        target = f'{sub_cartella_download}/ERA5_{t.year}_{t.month:02d}_{t.day:02d}.nc'

        client = cdsapi.Client()

        if os.path.exists(f'{sub_cartella_download}/ERA5_{t.year}_{t.month:02d}_{t.day:02d}.nc'):
            print(f'{sub_cartella_download}/ERA5_{t.year}_{t.month:02d}_{t.day:02d}.nc esiste. Continuo.')

        else:
            try:
                client.retrieve(dataset, request, target)
            except ValueError:
                print(f'\n\nERRORE in {t} del ciclone del {int_tempi[0]}\n\n')

    print()

print('\n\nDone')
