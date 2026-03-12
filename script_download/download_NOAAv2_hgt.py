
import os

import numpy as np

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

cartella_download = f'{cartella_lavoro}/NOAAv2c_hgt_annuali'
os.makedirs(cartella_download, exist_ok=True)

# %%
lista_anni = np.arange(1851, 2015)

### Da: https://www.psl.noaa.gov/data/gridded/data.20thC_ReanV2c.html
### 164 - Geopotential height - Ensemble Mean -	Pressure Levels - 4x Daily

os.chdir(cartella_download)

for anno in lista_anni:
    print(f'Anno = {anno}')
    stringa_download = f'https://downloads.psl.noaa.gov//Datasets/20thC_ReanV2c/pressure/hgt.{anno}.nc'
    
    if not os.path.exists(f'hgt.{anno}.nc'):
        comando = f'wget --quiet {stringa_download}'
        print(comando)
        os.system(comando)
    else:
        print(f'hgt.{anno}.nc esiste già. Continuo.')

print('\n\nDone')
