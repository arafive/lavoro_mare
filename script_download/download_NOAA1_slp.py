
import os

import numpy as np

lista_possibili_cartelle_lavoro = [
    '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

cartella_download = f'{cartella_lavoro}/NOAA1_annuali'
os.makedirs(cartella_download, exist_ok=True)

# %%
lista_anni = np.arange(1948, 2024)

### Da: https://www.psl.noaa.gov/data/gridded/data.ncep.reanalysis.html
### 77 - Sea Level Pressure	- Individual Obs - Sea Level - 4x Daily

os.chdir(cartella_download)

for anno in lista_anni:
    print('Anno = {anno}')
    stringa_download = f'https://downloads.psl.noaa.gov//Datasets/ncep.reanalysis/surface/slp.{anno}.nc'
    
    if not os.path.exists(f'prmsl.{anno}.nc'):
        comando = f'wget --quiet {stringa_download}'
        print(comando)
        os.system(comando)
    else:
        print(f'prmsl.{anno}.nc esiste già. Continuo.')

print('\n\nDone')
