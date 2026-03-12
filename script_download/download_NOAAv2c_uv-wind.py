
import os

import numpy as np

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

# %%
lista_anni = np.arange(1851, 2015)

cartella_download = f'{cartella_lavoro}/NOAAv2c_u-wind_annuali'
os.makedirs(cartella_download, exist_ok=True)

### Da: https://www.psl.noaa.gov/data/gridded/data.20thC_ReanV2c.html
### 164 - U-wind - Ensemble Mean - 10 m - 8x Daily

os.chdir(cartella_download)

for anno in lista_anni:
    print('Anno = {anno}')
    stringa_download = f'https://downloads.psl.noaa.gov/Datasets/20thC_ReanV2c/gaussian/monolevel/uwnd.10m.{anno}.nc'

    if not os.path.exists(f'u-wind.10m.{anno}.nc'):
        comando = f'wget --quiet {stringa_download}'
        print(comando)
        os.system(comando)
    else:
        print(f'u-wind.{anno}.nc esiste già. Continuo.')

##############
##############

### Da: https://www.psl.noaa.gov/data/gridded/data.20thC_ReanV2c.html
### 164 - V-wind - Ensemble Mean - 10 m - 8x Daily

cartella_download = f'{cartella_lavoro}/NOAAv2c_v-wind_annuali'
os.makedirs(cartella_download, exist_ok=True)

os.chdir(cartella_download)

for anno in lista_anni:
    print('Anno = {anno}')
    stringa_download = f'https://downloads.psl.noaa.gov/Datasets/20thC_ReanV2c/gaussian/monolevel/vwnd.10m.{anno}.nc'
    
    if not os.path.exists(f'v-wind.10m.{anno}.nc'):
        comando = f'wget --quiet {stringa_download}'
        print(comando)
        os.system(comando)
    else:
        print(f'v-wind.{anno}.nc esiste già. Continuo.')

print('\n\nDone')
