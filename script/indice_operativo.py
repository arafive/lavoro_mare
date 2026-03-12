
import os
import cfgrib
import distinctipy

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as mfont

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from shapely.geometry import Polygon
from shapely.geometry import Point

from metpy.units import units
from metpy.calc import wind_direction

from scipy import stats

lista_possibili_cartelle_lavoro = [
    '/media/daniele/Daniele2TB/test/lavoro_mare',
    '/run/media/daniele.carnevale/Daniele2TB/test/lavoro_mare',
]

lista_possibili_cartelle_archvio = [
    '/media/daniele/Caradhras/varie/piccolo_ARC_STORICO',
    '/mnt/ARC_STORICO',
]

cartella_lavoro = [x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

cartella_archivio = [x for x in lista_possibili_cartelle_archvio if os.path.exists(x)][0]
del (lista_possibili_cartelle_archvio)

font_da_usare = 'Helvetica' # Helvetica, NotesEsa
font_files = mfont.findSystemFonts(fontpaths=f'./font/{font_da_usare}')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)

plt.rc('font', family=font_da_usare, weight='normal', size=8)


def f_log_ciclo_for(lista_di_liste):
    """Log per un ciclo for."""
    # lista_di_liste. Ogni lista contiene 3 elementi:
    # Il primo è la descrizione, il secondo è l'elemento di ogni ciclo, il terzo è la lista iterata.

    str_output = ''
    for n, i in enumerate(lista_di_liste, 1):
        assert len(i) == 3, 'Ci sono meno di 3 elementi. Modifica.'
        
        if not type(i[2]) == list:
            i[2] = list(i[2])
            
        sub_str = f'{i[0]}{i[1]} [{i[2].index(i[1]) + 1}/{len(i[2])}]'
        str_output = str_output + sub_str
        if not n == len(lista_di_liste):
            str_output = str_output + ' · '

    print(str_output)


def f_dataframe_ds_variabili(lista_ds):
    """Ritorna il dataframe che lega dataset alle variabili.
    
    Parameters
    ----------
    lista_ds : list
        Lista che contiene i vari dataset.

    Returns
    -------
    df_attributi : pandas.core.frame.DataFrame
        Il dataframe che contiene gli attributi, oltre
        all'indice del dataset che contiene quella variabile.

    """
    df_attrs = pd.DataFrame()
    
    for i, ds in enumerate(lista_ds):
        for v in [x for x in ds.data_vars]:
            df_attrs = pd.concat([df_attrs, pd.DataFrame({**{'id_ds': i}, **ds[v].attrs}, index=[v])])
            
    ### Elimino le colonne i vuoi valori sono comuni a tutte le righe
    for i in df_attrs:
        if len(set(df_attrs[i].tolist())) == 1:
            df_attrs = df_attrs.drop(columns=[i])
    
    df_attrs = df_attrs.drop(columns=['long_name']) # doppione di 'GRIB_name'
    df_attrs = df_attrs.drop(columns=['standard_name']) # doppione di 'GRIB_cfName'
    df_attrs = df_attrs.drop(columns=['GRIB_cfName']) # non ha importanza, sono quasi tutti 'unknown'
    df_attrs = df_attrs.drop(columns=['units']) # doppione di 'GRIB_units'
    df_attrs = df_attrs.drop(columns=['GRIB_shortName', 'GRIB_cfVarName']) # doppioni dell'index
    
    if 'GRIB_dataType' not in df_attrs:
        df_attrs['GRIB_dataType'] = 'fc' # Nei grib più recenti 'an' e 'fc' sono uniti

    return df_attrs


dict_punti = {
    'boa00296': {'lat': 43.96, 'lon': 9.44},
    'spezia': {'lat': 44.10, 'lon': 9.82},
    'bejaja': {'lat': 36.75, 'lon': 5.06},
    'perpignano': {'lat': 42.69, 'lon': 2.89},
    'ventimiglia': {'lat': 43.79, 'lon': 7.60},
    'eolie': {'lat': 38.48, 'lon': 14.93},
    'genova': {'lat': 44.40, 'lon': 8.93},
    'punto_S': {'lat': 41.88, 'lon': 7.55},
}


"""
Come fare l'rsync dei modelli che mi servono
BOLAM
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/BOLAM/2024/11/19/bo08*.grib2 /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/BOLAM/2024/11/19/.
MOLOCH
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/BOLAM/2024/11/19/molita15*.grib2 /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/BOLAM/2024/11/19/.
GFS
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/GFS/2024/11/19/* /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/GFS/2024/11/19/.
COSMO5
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/COSMO/2024/11/19/lm5_* /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/COSMO/2024/11/19/.
COSMO2
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/COSMO/2024/11/19/lm22_* /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/COSMO/2024/11/19/.
ECITA
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/ECMWF/2024/11/19/ecmf_0.1_2024111900_181x161_2_20_34_50_undef_undef.* /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/ECMWF/2024/11/19/.
ECSYN
    rsyncd daniele.carnevale@01588-lenovo.cfmi.arpal.org:/mnt/ARC_STORICO/ECMWF/2024/11/19/ecmf_0.2_2024111900_551x301_-60_50_20_80_fc_0.* /media/daniele/Daniele2TB/varie/piccolo_ARC_STORICO/ECMWF/2024/11/19/.

"""

# %%

# data = pd.to_datetime('2026-01-08 00:00:00')
data = pd.to_datetime('today').normalize()

def f_ECSYN(data, var):
    nome_file = f'ecmf_0.2_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}_551x301_-60_50_20_80_fc_0.grb'
    print(f'Apro {nome_file} ...')
    
    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/ECMWF/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_ECITA(data, var):
    nome_file = f'ecmf_0.1_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}_181x161_2_20_34_50_undef_undef.grb'
    print(f'Apro {nome_file} ...')

    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/ECMWF/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_BOLAM(data, var):
    nome_file = f'bo08_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
    print(f'Apro {nome_file} ...')

    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/BOLAM/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_MOLOCH(data, var):
    nome_file = f'molita15_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
    print(f'Apro {nome_file} ...')

    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/BOLAM/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_GFS(data, var):
    try:
        nome_file = f'gfsWorld_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
        print(f'Apro {nome_file} ...')

        lista_ds = cfgrib.open_datasets(
            f'{cartella_archivio}/GFS/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
            backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
        )
    except FileNotFoundError:
        nome_file = f'gfs_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
        print(f'Apro {nome_file} ...')

        lista_ds = cfgrib.open_datasets(
            f'{cartella_archivio}/GFS/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
            backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
        )
        
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_COSMO2(data, var):
    nome_file = f'lm22_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
    print(f'Apro {nome_file} ...')

    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/COSMO/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

def f_COSMO5(data, var):
    nome_file = f'lm5_{data.year}{data.month:02d}{data.day:02d}{data.hour:02d}.grib2'
    print(f'Apro {nome_file} ...')

    lista_ds = cfgrib.open_datasets(
        f'{cartella_archivio}/COSMO/{data.year}/{data.month:02d}/{data.day:02d}/{nome_file}',
        backend_kwargs={'indexpath': f'/tmp/{nome_file}_lista_ds.idx'}
    )
    
    df_attrs = f_dataframe_ds_variabili(lista_ds)
    ds_msl = lista_ds[df_attrs.loc[var]['id_ds']][var]
    
    return ds_msl

print('\nCarico i modelli...')
dict_modelli = {
    'ecita': f_ECITA(data, 'mslp'),
    # 'ecsyn': f_ECSYN(data, 'msl'), # non serve perchè nel lungo ecita == ecsyn
    'gfs': f_GFS(data, 'mslp'),
    'bolam': f_BOLAM(data, 'mslp'),
    'moloch': f_MOLOCH(data, 'mslp'),
    # 'cosmo2': f_COSMO2(data, 'pmsl'),
    # 'cosmo5': f_COSMO5(data, 'pmsl'),
}

# %%

### Controllo la griglia
"""
for chiave, valore in dict_modelli.items():
    lon, lat = valore['longitude'].values, valore['latitude'].values
    
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

    proiezione = ccrs.LambertConformal(central_longitude=8)
    # !!! Il gfs è plottato male ma non importa perché ha tutto il mondo
    
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(1, 1, 1, projection=proiezione)
    ax.set_extent((lon.min(), lon.max(), lat.min(), lat.max()))
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS)
    
    plt.title(chiave)
    plt.show()
    plt.close()
"""

# %% Estraggo le pressioni al suolo

dict_df_msl = {x: {} for x in dict_modelli.keys()}

### Devo stare attento ai modelli ruotati
# modello = 'cosmo5'

# a = dict_modelli[modello]
# lon, lat = a['longitude'], a['latitude']

# if lon.ndim == 1:
#     lon, lat = np.meshgrid(lon, lat)

# if modello == 'bolam':
#     lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
# elif modello == 'moloch':
#     lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
# elif modello == 'cosmo2':
#     lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
# elif modello == 'cosmo5':
#     lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
    
# plt.imshow(lon)
# plt.title(f'lon, {modello}')
# plt.show()
# plt.close()

# plt.imshow(lat)
# plt.title(f'lat, {modello}')
# plt.show()
# plt.close()

print('\nEstraggo le pressioni al suolo...')
for modello, ds in dict_modelli.items():
    print(modello)
    lon, lat = ds['longitude'].values, ds['latitude'].values
    tempi = pd.to_datetime(ds['valid_time'].values)
    
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)
        
    msl = ds
    df_estrazione = pd.DataFrame(index=tempi)
    
    if modello in ['bolam', 'moloch', 'cosmo2', 'cosmo5']:
        lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
        msl = np.rot90(msl.values.T, 1)
        
        for punto, coord_p in dict_punti.items():
            distanze_2D = (np.abs(lon - coord_p['lon']) + np.abs(lat - coord_p['lat']))
            distanze_1D = np.sort(distanze_2D.flatten())
    
            lat_min, lon_min = np.where(distanze_2D == distanze_1D[0])
            
            estrazione = msl[lat_min, lon_min, :].squeeze()
            df_estrazione[punto] = msl[lat_min, lon_min, :].squeeze() / 100 # Pa -> hPa

    else:
        for punto, coord_p in dict_punti.items():
            df_estrazione[punto] = msl.sel(longitude=coord_p['lon'], latitude=coord_p['lat'], method='nearest').values / 100 # Pa -> hPa

    dict_df_msl[modello] = df_estrazione


# %% Calcolo il gradiente del campo di pressione

dict_gradienti = {x: {} for x in dict_modelli.keys()}

print('\nCalcolo il gradiente del campo di pressione...')
for modello, ds in dict_modelli.items():
    print(modello)
    msl = ds
    assi = (2, 1)
    
    if modello in ['bolam', 'moloch', 'cosmo2', 'cosmo5']:
        msl = np.rot90(msl.values.T, 1)
        assi = (1, 0)
        ### Cambio gli assi del gradiente.
        ### Contfronta:
        ###   np.rot90(dict_modelli['bolam'].values.T, 1).shape
        ###   dict_modelli['bolam'].shape

    dict_gradienti[modello]['x'], dict_gradienti[modello]['y'] = np.gradient(msl, axis=assi)
    dict_gradienti[modello]['mod'] = np.sqrt(dict_gradienti[modello]['x'] ** 2 + dict_gradienti[modello]['y'] ** 2)

# %% Calcolo l'angolo del campo di gradiente di pressione

convenzione = 'from'
dict_theta = {x: {} for x in dict_modelli.keys()}

print('\nCalcolo l\'angolo del campo di gradiente di pressione...')
for modello, ds in dict_modelli.items():
    print(modello)
    msl = ds

    dict_theta[modello] = np.array(wind_direction(dict_gradienti[modello]['x'] * units('m/s'), dict_gradienti[modello]['y'] * units('m/s'), convention=convenzione))

# %% Calcolo il theta medio solo dentro i poligoni

poligono_SBP = Polygon(
    [(dict_punti['spezia']['lon'], dict_punti['spezia']['lat']),
     (dict_punti['bejaja']['lon'], dict_punti['bejaja']['lat']),
     (dict_punti['perpignano']['lon'], dict_punti['perpignano']['lat']),
     (dict_punti['spezia']['lon'], dict_punti['spezia']['lat'])]
)

poligono_EVS = Polygon(
    [(dict_punti['eolie']['lon'], dict_punti['eolie']['lat']),
     (9.8, dict_punti['eolie']['lat']),
     (9.8, 43),
     (dict_punti['ventimiglia']['lon'], dict_punti['ventimiglia']['lat']),
     (dict_punti['spezia']['lon'], dict_punti['spezia']['lat']),
     (10.4, 42.8),
     (dict_punti['eolie']['lon'], 39.75),
     (dict_punti['eolie']['lon'], dict_punti['eolie']['lat'])]
)

### Calcolo le maschere per ogni modello
dict_sr_theta_medi = {x: {} for x in dict_modelli.keys()}

print('\nCalcolo il theta medio solo dentro i poligoni...')
for modello, ds in dict_modelli.items():
    print(modello)
    lon, lat = ds['longitude'].values, ds['latitude'].values
    
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

    if modello in ['bolam', 'moloch', 'cosmo2', 'cosmo5']:
        lon, lat = np.rot90(lon.T, 1), np.rot90(lat.T, 1)
        
    if modello in ['bolam', 'moloch', 'cosmo2', 'cosmo5']:
        mask_poligono_SBP = np.zeros_like(dict_theta[modello][..., 0], dtype=bool)
        mask_poligono_EVS = np.zeros_like(dict_theta[modello][..., 0], dtype=bool)
    else:
        mask_poligono_SBP = np.zeros_like(dict_theta[modello][0, ...], dtype=bool)
        mask_poligono_EVS = np.zeros_like(dict_theta[modello][0, ...], dtype=bool)
    
    for i in range(lon.shape[0]):
        for j in range(lon.shape[1]):
            point = Point(lon[i, j], lat[i, j])
            if poligono_SBP.contains(point):
                try:
                    mask_poligono_SBP[i, j] = True
                except IndexError:
                    pass

    for i in range(lon.shape[0]):
        for j in range(lon.shape[1]):
            point = Point(lon[i, j], lat[i, j])
            if poligono_EVS.contains(point):
                try:
                    mask_poligono_EVS[i, j] = True
                except IndexError:
                    pass

    # plt.imshow(mask_poligono_SBP)
    # plt.title(modello)
    # plt.show()
    # plt.close()
    
    ###
    tempi = dict_df_msl[modello].index
    sr_theta_medi_triangolo_SBP = pd.Series(index=tempi)
    sr_theta_medi_poligono_EVS = pd.Series(index=tempi)
    
    for ind_t, t in enumerate(tempi):
        
        if modello in ['bolam', 'moloch', 'cosmo2', 'cosmo5']:
            campo_maschera_triangolo_SBP = np.where(mask_poligono_SBP, dict_theta[modello][..., ind_t], np.nan)
            campo_maschera_poligono_EVS = np.where(mask_poligono_EVS, dict_theta[modello][..., ind_t], np.nan)
        else:
            campo_maschera_triangolo_SBP = np.where(mask_poligono_SBP, dict_theta[modello][ind_t, ...], np.nan)
            campo_maschera_poligono_EVS = np.where(mask_poligono_EVS, dict_theta[modello][ind_t, ...], np.nan)
            
        sr_theta_medi_triangolo_SBP.loc[t] = stats.circmean(campo_maschera_triangolo_SBP, nan_policy='omit', low=0, high=360)
        sr_theta_medi_poligono_EVS.loc[t] = stats.circmean(campo_maschera_poligono_EVS, nan_policy='omit', low=0, high=360)
    
    dict_sr_theta_medi[modello]['SBP'] = sr_theta_medi_triangolo_SBP
    dict_sr_theta_medi[modello]['EVS'] = sr_theta_medi_poligono_EVS
    
# %% Calcolo tutto quello che mi serve

theta_opt_SBP = 0
theta_opt_EVS = -1.0472 # -60° in radianti

print('\nCalcolo tutto quello che mi serve...')
for modello, df in dict_df_msl.items():
    print(modello)
    
    df['Dp_bejaja-boa00296'] = np.clip((df['bejaja'] - df['boa00296']), a_min=0, a_max=None)
    df['Dp_eolie-ventimiglia'] = np.clip((df['eolie'] - df['ventimiglia']), a_min=0, a_max=None)
    df['Dp_punto_S-boa00296'] = np.clip((df['punto_S'] - df['boa00296']), a_min=0, a_max=None)
    
    df['theta_medi_grad_triangolo_SBP'] = np.mod(dict_sr_theta_medi[modello]['SBP'] + 180, 360)
    df['theta_medi_grad_poligono_EVS'] = np.mod(dict_sr_theta_medi[modello]['EVS'] + 180, 360)
    
    df['theta_medi_rad_triangolo_SBP'] = np.deg2rad(df['theta_medi_grad_triangolo_SBP'])
    df['theta_medi_rad_poligono_EVS'] = np.deg2rad(df['theta_medi_grad_poligono_EVS'])
    
    df['Ew_poligono_SBP'] = np.clip(df['Dp_bejaja-boa00296'] * np.cos(theta_opt_SBP + df['theta_medi_rad_triangolo_SBP']), a_min=0, a_max=None)
    df['Ew_poligono_EVS'] = np.clip(df['Dp_eolie-ventimiglia'] * np.cos(theta_opt_EVS + df['theta_medi_rad_poligono_EVS']), a_min=0, a_max=None)
    
    df = df.round(2)

# %% Plot

# for modello, df in dict_df_msl.items():
    
#     df[['Dp_bejaja-boa00296', 'Ew_poligono_SBP', 'Dp_eolie-ventimiglia', 'Ew_poligono_EVS']].plot(zorder=3)
    
#     plt.ylim(bottom=-2, top=30)
#     plt.yticks([0, 5, 10, 15, 20, 25, 30])
#     plt.axhline(y=19, color='tab:cyan', ls='-', lw=1.5, zorder=2)
#     plt.ylabel('hPa')
#     plt.grid(zorder=-1, lw=0.5)
#     plt.title(modello)
    
#     plt.show()
#     plt.close()

# %%

df_unico = pd.DataFrame()

for modello, df in dict_df_msl.items():
    df.columns = [f'{x}_{modello}' for x in df.columns]
    df_unico = pd.concat([df_unico, df], axis=1)
    
df_Ew_SBP = df_unico[[x for x in df_unico.columns if x.startswith('Ew_poligono_SBP')]]
df_Ew_EVS = df_unico[[x for x in df_unico.columns if x.startswith('Ew_poligono_EVS')]]

df_Ew_SBP.columns = [x.split('_')[-1] for x in df_Ew_SBP.columns]
df_Ew_EVS.columns = [x.split('_')[-1] for x in df_Ew_EVS.columns]

indici_da_plottare = pd.date_range(df_unico.index[0], df_unico.index[0] + pd.DateOffset(days=5), freq='3h')

df_Ew_SBP = df_Ew_SBP.loc[df_Ew_SBP.index.intersection(indici_da_plottare)]
df_Ew_EVS = df_Ew_EVS.loc[df_Ew_EVS.index.intersection(indici_da_plottare)]

### Per il GFS devo riempire i NaN altrimenti non posso plottarlo con passo triorario
df_Ew_SBP['gfs'] = df_Ew_SBP['gfs'].interpolate(method='linear')
df_Ew_EVS['gfs'] = df_Ew_EVS['gfs'].interpolate(method='linear')

# %%

os.makedirs(f'{cartella_lavoro}/indice_operativo', exist_ok=True)

# colori_modelli = distinctipy.get_colors(df_Ew_EVS.shape[1])
colori_modelli = {
    'ecita': 'tab:green',
    'gfs': 'tab:blue',
    'bolam': 'tab:orange',
    'moloch': 'tab:cyan',
    'cosmo2': 'tab:pink',
    'cosmo5': 'tab:gray',
}

fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True, sharey=True)

df_Ew_SBP.plot(ax=axs[0], color=colori_modelli, zorder=10)
# axs[0].scatter(df_Ew_SBP.index, df_Ew_SBP['gfs'])
df_Ew_EVS.plot(ax=axs[1], legend=False, color=colori_modelli, zorder=10)

axs[0].set_ylim(bottom=-2, top=30)
axs[0].legend(ncol=2, prop={'size': 10}, columnspacing=0.8)
axs[0].tick_params(labelbottom=False, bottom=False)

for i in range(axs.shape[0]):
    axs[i].axhline(y=19, color='tab:red', ls='--', lw=1.5, zorder=3)
    axs[i].grid(lw=0.6, ls=':')
    axs[i].margins(x=0.02)

axs[0].set_ylabel('Eff. Libeccio Lungo', fontsize=10)
axs[1].set_ylabel('Eff. Scirocco', fontsize=10)

#
##
### Formattazione dei tempi A MANO
axs[1].set_xticks([x for x in df_Ew_EVS.index if x.hour in [0, 6, 12, 18]])
    
xlabels = []
for i in df_Ew_EVS.index:
    if i.hour in [0]:
        xlabels.append(f'{i.month_name()[0:3]}-{i.day}')
    elif i.hour in [6, 12, 18]:
        xlabels.append(f'{i.hour:02d}:{i.minute:02d}')
    else:
        pass

axs[1].set_xticklabels(xlabels)

for label in axs[1].get_xticklabels():
    label.set_rotation(45)
    label.set_horizontalalignment('center')
    
    if not ':00' in label.get_text():
        label.set_fontweight('bold')
    else:
        label.set_fontsize(7)

for label in axs[1].get_xticklabels()[1:-1]: # [1:-1] per non mettere le righe anche al primo e ultimo giorno
    if not ':00' in label.get_text():
        axs[0].axvline(x=label.get_position()[0], color='gray', ls='-', lw=0.6, zorder=2)
        axs[1].axvline(x=label.get_position()[0], color='gray', ls='-', lw=0.6, zorder=2)

        # axs[0].plot([label.get_position()[0], label.get_position()[0]], [-2, 20], color='gray', ls='-', lw=0.7, zorder=2)
        # axs[1].plot([label.get_position()[0], label.get_position()[0]], [-2, 20], color='gray', ls='-', lw=0.7, zorder=2)

### Formattazione dei tempi A MANO
##
#

axs[0].set_title(f'Run del {str(data)}', fontsize=10, fontweight='bold', loc='left')

nome_file = f"indice_operativo_{str(data).replace(' ', '_').replace(':', '-')}"
plt.savefig(f"{cartella_lavoro}/indice_operativo/indice_operativo_{nome_file}.png", dpi=600, format='png', bbox_inches='tight')
# plt.show()
plt.close()

print(f"\n\neog {cartella_lavoro}/indice_operativo/indice_operativo_{nome_file}.png\n")
# TODO Aggiungi informazioni sulle maree

print('\n\nDone.')
