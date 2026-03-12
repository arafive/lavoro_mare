
import os

import numpy as np

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

cartella_download = f'{cartella_lavoro}/NOAAv2c_prmsl_annuali'
os.makedirs(cartella_download, exist_ok=True)

# %%
lista_anni = np.arange(1851, 2015)

### Da: https://www.psl.noaa.gov/data/gridded/data.20thC_ReanV2c.html
### 164 - Mean Sea Level Pressure - Ensemble Mean -	Mean Sea Level - 4x Daily

os.chdir(cartella_download)

for anno in lista_anni:
    print(f'Anno = {anno}')
    stringa_download = f'https://downloads.psl.noaa.gov//Datasets/20thC_ReanV2c/monolevel/prmsl.{anno}.nc'
    
    if not os.path.exists(f'prmsl.{anno}.nc'):
        comando = f'wget --quiet {stringa_download}'
        print(comando)
        os.system(comando)
    else:
        print(f'prmsl.{anno}.nc esiste già. Continuo.')

print('\n\nDone')
