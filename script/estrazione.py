
import os
import pickle

import numpy as np
import pandas as pd
import xarray as xr

import cartopy.crs as ccrs
import cartopy.feature as cfeature

import matplotlib.pyplot as plt
import matplotlib.font_manager as mfont

from haversine import haversine

from cartopy.geodesic import Geodesic
from shapely.geometry import Polygon
from shapely.geometry import Point

from metpy.units import units
from metpy.calc import wind_direction
from metpy.calc import gradient as metpy_gradient

from scipy import stats

lista_possibili_cartelle_lavoro = [
    '/media/daniele/Caradhras/test/dati_Sasha',
    '/run/media/daniele.carnevale/Caradhras/test/dati_Sasha',
]

cartella_lavoro = [x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

font_files = mfont.findSystemFonts(fontpaths='./font/Helvetica')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)

plt.rc('font', family='Helvetica', weight='normal', size=8)


# %%
#  ______               _             _
# |  ____|             (_)           (_)
# | |__ _   _ _ __  _____  ___  _ __  _
# |  __| | | | '_ \|_  / |/ _ \| '_ \| |
# | |  | |_| | | | |/ /| | (_) | | | | |
# |_|   \__,_|_| |_/___|_|\___/|_| |_|_|

def f_log_ciclo_for(lista_di_liste):
    """Log per un ciclo for.

    Lista_di_liste. Ogni lista contiene 3 elementi:
    Il primo è la descrizione, il secondo è l'elemento di ogni ciclo, il terzo è la lista iterata.
    """
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


def f_init_plot(proj, estensione):
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_extent(estensione)
    ax.add_feature(cfeature.BORDERS, lw=0.4)
    ax.add_feature(cfeature.COASTLINE, lw=0.4)
    ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])
    ax.set_aspect('auto', adjustable=None)

    return fig, ax


def f_cerchio_genova(diz):
    raggio = 300 # km
    n_samples = 100

    circles = Polygon(Geodesic().circle(diz['genova']['lon'], diz['genova']['lat'], raggio * 1000, n_samples=n_samples))

    feature = cfeature.ShapelyFeature([circles], ccrs.Geodetic(), fc='None', ec='grey', lw=1, linestyle="-")
    ax.add_feature(feature)


def f_poligono_SBP(diz):
    ### Libeccio lungo
    poligono = Polygon(
        [(diz['spezia']['lon'], diz['spezia']['lat']),
         (diz['bejaja']['lon'], diz['bejaja']['lat']),
         (diz['perpignano']['lon'], diz['perpignano']['lat']),
         (diz['spezia']['lon'], diz['spezia']['lat'])]
    )

    poligono_feature = cfeature.ShapelyFeature(
        [poligono],
        ccrs.PlateCarree(),
        edgecolor='tab:orange',
        facecolor='tab:orange',
        alpha=0.3
    )

    ax.add_feature(poligono_feature)


def f_poligono_EVS(diz):
    ### Scirocco
    poligono = Polygon(
        [(diz['eolie']['lon'], diz['eolie']['lat']),
         (9.8, diz['eolie']['lat']),
         (9.8, 43),
         (diz['ventimiglia']['lon'], diz['ventimiglia']['lat']),
         (diz['spezia']['lon'], diz['spezia']['lat']),
         (10.4, 42.8),
         (diz['eolie']['lon'], 39.75),
         (diz['eolie']['lon'], diz['eolie']['lat'])]
    )

    poligono_feature = cfeature.ShapelyFeature(
        [poligono],
        ccrs.PlateCarree(),
        edgecolor='tab:red',
        facecolor='tab:red',
        alpha=0.3
    )

    ax.add_feature(poligono_feature)


def f_correzione_NOAAv3(ds, estensione=None):
    ds = ds.rename({'lon': 'longitude'})
    ds = ds.rename({'lat': 'latitude'})

    ds['_longitude_180'] = xr.where(ds['longitude'] > 180, ds['longitude'] - 360, ds['longitude'])
    ds = (ds.swap_dims({'longitude': '_longitude_180'}).sel(**{'_longitude_180': sorted(ds['_longitude_180'])}).drop_vars('longitude'))
    ds = ds.rename({'_longitude_180': 'longitude'})

    ### Serve comunque prendere un sottoinsieme altrimenti i file temporanei pesano troppo
    if estensione:
        ds = ds.sel(longitude=slice(estensione[0], estensione[1]), latitude=slice(estensione[2], estensione[3]))

    return ds


def f_prendi_anno(f, q):
    if q == 'ERA5':
        return f.split('_')[-1].split('.')[0]
    else:
        return f.split('.')[1]


def f_estrazione_punti(riprendi, quali_file, f, nome_pressione, cartella_lavoro, cartella_estrazioni, estensioni):
    anno = f_prendi_anno(f, quali_file)

    if riprendi:
        if not os.path.exists(f'{cartella_estrazioni}/df_{anno}.csv'):
            ds = xr.open_dataset(f'{cartella_lavoro}/{quali_file}_annuali/{f}', engine='netcdf4')

            if quali_file == 'NOAAv3':
                ds = f_correzione_NOAAv3(ds, estensioni)

            tempi = pd.to_datetime(ds[nome_tempo].values)
            df = pd.DataFrame(index=tempi)

            for chiave, valore in dict_punti.items():
                df[chiave] = ds[nome_pressione].sel(longitude=valore['lon'], latitude=valore['lat'], method='nearest').values / 100 # Pa -> hPa

            df.to_csv(f'{cartella_estrazioni}/df_{anno}.csv', index=True, header=True, na_rep=np.nan, mode='w')

        else:
            df = pd.read_csv(f'{cartella_estrazioni}/df_{anno}.csv', index_col=0, parse_dates=True)

    else:
        ds = xr.open_dataset(f'{cartella_lavoro}/{quali_file}_annuali/{f}', engine='netcdf4')

        if quali_file == 'NOAAv3':
            ds = f_correzione_NOAAv3(ds, estensioni)

        tempi = pd.to_datetime(ds[nome_tempo].values)
        df = pd.DataFrame(index=tempi)

        for chiave, valore in dict_punti.items():
            df[chiave] = ds[nome_pressione].sel(longitude=valore['lon'], latitude=valore['lat'], method='nearest').values / 100 # Pa -> hPa

        df.to_csv(f'{cartella_estrazioni}/df_{anno}.csv', index=True, header=True, na_rep=np.nan, mode='w')

    return df


def f_calcolo_gradiente(riprendi, quali_file, f, nome_pressione, cartella_lavoro, cartella_gradienti, estensioni):
    anno = f_prendi_anno(f, quali_file)
    dict_gradiente = {}

    if riprendi:
        if not os.path.exists(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl'):
            ds = xr.open_dataset(f'{cartella_lavoro}/{quali_file}_annuali/{f}', engine='netcdf4')

            if quali_file == 'NOAAv3':
                ds = f_correzione_NOAAv3(ds, estensioni)

            if quali_file == 'ERA5':
                axis = (list(ds.dims).index('longitude'), list(ds.dims).index('latitude'))
                gradiente_msl_x, gradiente_msl_y = np.gradient(ds[nome_pressione], axis=axis) # derivata lungo lungo x, derivata lungo y

            else:
                gradiente_msl_x, gradiente_msl_y = ds[nome_pressione].differentiate(coord='longitude').values, ds[nome_pressione].differentiate(coord='latitude').values # derivata lungo lungo x, derivata lungo y
                gradiente_msl_y = - gradiente_msl_y ### Me lo spiego solo perché le latitudini sono sottosopra rispetto a ERA5

            grad_era5_mod = np.sqrt(gradiente_msl_x.round(2) ** 2 + gradiente_msl_y.round(2) ** 2).round(2)

            dict_gradiente['x'] = gradiente_msl_x.round(2)
            dict_gradiente['y'] = gradiente_msl_y.round(2)
            dict_gradiente['mod'] = grad_era5_mod

            pickle.dump(dict_gradiente, open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl', 'wb'))

        else:
            print(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl esiste già. Continuo.')

    else:
        ds = xr.open_dataset(f'{cartella_lavoro}/{quali_file}_annuali/{f}', engine='netcdf4')

        if quali_file == 'NOAAv3':
            ds = f_correzione_NOAAv3(ds, estensioni)

        if quali_file == 'ERA5':
            axis = (list(ds.dims).index('longitude'), list(ds.dims).index('latitude'))
            gradiente_msl_x, gradiente_msl_y = np.gradient(ds[nome_pressione], axis=axis) # derivata lungo lungo x, derivata lungo y

        else:
            gradiente_msl_x, gradiente_msl_y = ds[nome_pressione].differentiate(coord='longitude').values, ds[nome_pressione].differentiate(coord='latitude').values # derivata lungo lungo x, derivata lungo y
            gradiente_msl_y = - gradiente_msl_y ### Me lo spiego solo perché le latitudini sono sottosopra rispetto a ERA5

        grad_era5_mod = np.sqrt(gradiente_msl_x.round(2) ** 2 + gradiente_msl_y.round(2) ** 2).round(2)

        dict_gradiente['x'] = gradiente_msl_x.round(2)
        dict_gradiente['y'] = gradiente_msl_y.round(2)
        dict_gradiente['mod'] = grad_era5_mod

        pickle.dump(dict_gradiente, open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl', 'wb'))


def f_calcolo_theta(riprendi, quali_file, convenzione, cartella_theta, cartella_gradienti):
    anno = f_prendi_anno(f, quali_file)

    if riprendi:
        if not os.path.exists(f'{cartella_theta}/ndarray_theta_{quali_file}_{anno}.pkl'):
            dict_gradiente = pickle.load(open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl', 'rb'))

            ### Imbroglio 'wind_direction' ma dovrebbe funzionare
            theta = np.array(wind_direction(dict_gradiente['x'] * units('m/s'), dict_gradiente['y'] * units('m/s'), convention=convenzione))
            pickle.dump(theta, open(f'{cartella_theta}/ndarray_theta_{quali_file}_{anno}.pkl', 'wb'))

        else:
            print(f'{cartella_theta}/ndarray_theta_{quali_file}_{anno}.pkl esiste già. Continuo.')

    else:
        dict_gradiente = pickle.load(open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_{anno}.pkl', 'rb'))

        ### Imbroglio 'wind_direction' ma dovrebbe funzionare
        theta = np.array(wind_direction(dict_gradiente['x'] * units('m/s'), dict_gradiente['y'] * units('m/s'), convention=convenzione))
        pickle.dump(theta, open(f'{cartella_theta}/ndarray_theta_{quali_file}_{anno}.pkl', 'wb'))

# %%
#  _____                               _        _
# |  __ \                             | |      (_)
# | |__) |_ _ _ __ __ _ _ __ ___   ___| |_ _ __ _
# |  ___/ _` | '__/ _` | '_ ` _ \ / _ \ __| '__| |
# | |  | (_| | | | (_| | | | | | |  __/ |_| |  | |
# |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__|_|  |_|

# !!!
quali_file = 'ERA5' ### --> Regular latitude-longitude grid
# quali_file = 'NOAAv3' ### --> Cylindrical Equidistant Projection Grid

if quali_file == 'ERA5':
    nome_tempo = 'valid_time'
    nome_pressione = 'msl'
    skip_frecce = 3
    scale = 5_000
    livelli_grad = np.arange(0, 200 + 20, 20)

elif quali_file == 'NOAAv3':
    nome_tempo = 'time'
    nome_pressione = 'prmsl'
    skip_frecce = 1
    scale = 11_000
    livelli_grad = np.arange(0, 500 + 50, 50)

dict_estremi_dominio = {
    'ERA5': (-10, 20, 34, 55 - 1),
    'Med1': (0, 20, 36, 47),
    'lig': (7.2, 10.5, 43.1, 45.4),
    'LILAM+': (4.0, 12.82, 41.05, 47.95),
    'EC20': (-60, 60, 20, 80),
    'Meteosat': (-20, 30, 30, 60)
}

dict_proj = {
    'PlateCarree': ccrs.PlateCarree(),
    'Orthographic': ccrs.Orthographic(central_longitude=8),
    'LambertAzimuthalEqualArea': ccrs.LambertAzimuthalEqualArea(central_longitude=8),
    'LambertConformal': ccrs.LambertConformal(central_longitude=8),
    'AlbersEqualArea': ccrs.AlbersEqualArea(central_longitude=8),
    'NorthPolarStereo': ccrs.NorthPolarStereo(central_longitude=8),
    'EqualEarth': ccrs.EqualEarth(central_longitude=8)
}

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

# %%
#  _____  _       _                _       _ _       _   _
# |  __ \| |     | |              (_)     | (_)     | | (_)
# | |__) | | ___ | |_    __ _ _ __ _  __ _| |_  __ _| |_ _
# |  ___/| |/ _ \| __|  / _` | '__| |/ _` | | |/ _` | __| |
# | |    | | (_) | |_  | (_| | |  | | (_| | | | (_| | |_| |
# |_|    |_|\___/ \__|  \__, |_|  |_|\__, |_|_|\__,_|\__|_|
#                        __/ |        __/ |
#                       |___/        |___/

ds_cerra = xr.open_dataset(f'{cartella_lavoro}/CERRA_annuali/CERRA_1985.nc', engine='netcdf4')
ds_era5 = xr.open_dataset(f'{cartella_lavoro}/ERA5_annuali/ERA5_1985.nc', engine='netcdf4')
ds_noaa1 = xr.open_dataset(f'{cartella_lavoro}/NOAA1_annuali/slp.1985.nc', engine='netcdf4')
ds_noaa2 = xr.open_dataset(f'{cartella_lavoro}/NOAA2_annuali/mslp.1985.nc', engine='netcdf4')
ds_noaav2 = xr.open_dataset(f'{cartella_lavoro}/NOAAv2_annuali/prmsl.1985.nc', engine='netcdf4')
ds_noaav2c = xr.open_dataset(f'{cartella_lavoro}/NOAAv2c_annuali/prmsl.1985.nc', engine='netcdf4')
ds_noaav3 = xr.open_dataset(f'{cartella_lavoro}/NOAAv3_annuali/prmsl.1985.nc', engine='netcdf4')

dict_lat_lon = {
    'CERRA': {'lat': ds_cerra.latitude.values, 'lon': ds_cerra.longitude.values}, # 2D
    'ERA5': {'lat': ds_era5.latitude.values, 'lon': ds_era5.longitude.values}, # 1D
    'NOAA1': {'lat': ds_noaa1.lat.values, 'lon': ds_noaa1.lon.values}, # 1D
    'NOAA2': {'lat': ds_noaa2.lat.values, 'lon': ds_noaa2.lon.values}, # 1D
    'NOAAv2': {'lat': ds_noaav2.lat.values, 'lon': ds_noaav2.lon.values}, # 1D
    'NOAAv2c': {'lat': ds_noaav2c.lat.values, 'lon': ds_noaav2c.lon.values}, # 1D
    'NOAAv3': {'lat': ds_noaav3.lat.values, 'lon': ds_noaav3.lon.values} # 1D
}

for m in dict_lat_lon.keys():
    if m == 'CERRA': continue

    dict_lat_lon[m]['lon'], dict_lat_lon[m]['lat'] = np.meshgrid(dict_lat_lon[m]['lon'], dict_lat_lon[m]['lat'])

dict_marker_style = {
    'CERRA': ['.', 1, 0.],
    'ERA5': ['o', 3, 0.],
    'NOAA1': ['s', 25, 0.3],
    'NOAA2': ['<', 25, 0.3],
    'NOAAv2': ['>', 25, 0.3],
    'NOAAv2c': ['v', 25, 0.3],
    'NOAAv3': ['^', 25, 0.2]
}

dominio = 'Med1'

### Tutte le griglie in un unico plot
fig = plt.figure(figsize=(6, 4))
ax = fig.add_subplot(1, 1, 1, projection=dict_proj['PlateCarree'])
ax.set_extent(dict_estremi_dominio[dominio])
ax.add_feature(cfeature.BORDERS, lw=0.4)
ax.add_feature(cfeature.COASTLINE, lw=0.4)
ax.set_aspect('auto', adjustable=None)
gl = ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])

f_poligono_SBP(dict_punti)
f_poligono_EVS(dict_punti)

for m in dict_lat_lon.keys():
    shape_lat = int(dict_lat_lon[m]['lat'].shape[0] / 2)
    shape_lon = int(dict_lat_lon[m]['lon'].shape[0] / 2)

    lat1 = float(dict_lat_lon[m]['lat'][shape_lat:shape_lat + 1, shape_lat:shape_lat + 1][0][0])
    lon1 = float(dict_lat_lon[m]['lon'][shape_lon:shape_lon + 1, shape_lon:shape_lon + 1][0][0])

    lat2 = float(dict_lat_lon[m]['lat'][shape_lat + 1:shape_lat + 2, shape_lat + 1:shape_lat + 2][0][0])
    lon2 = float(dict_lat_lon[m]['lon'][shape_lon + 1:shape_lon + 2, shape_lon + 1:shape_lon + 2][0][0])

    p1 = (lat1, lon1)
    p2 = (lat2, lon2)
    dist = np.round(haversine(p1, p2), 1)
    # print(f'{m} {dist} km')

    ax.scatter(
        x=dict_lat_lon[m]['lon'],
        y=dict_lat_lon[m]['lat'],
        transform=ccrs.Geodetic(),
        marker=dict_marker_style[m][0],
        s=dict_marker_style[m][1],
        linewidth=dict_marker_style[m][2],
        edgecolors='black',
        # facecolors='black',
        zorder=2,
        label=f'{m} [~{dist} km]'
    )

ax.legend(prop={'size': 5}, loc='upper right', framealpha=1)
gl.xlabel_style = {'size': 5}
gl.ylabel_style = {'size': 5}

plt.savefig(f'{cartella_lavoro}/griglie_{dominio}.png', dpi=600, format='png', bbox_inches='tight')

# plt.show()
plt.close()

### Un plot per griglia
for m in dict_lat_lon.keys():
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(1, 1, 1, projection=dict_proj['PlateCarree'])
    ax.set_extent(dict_estremi_dominio[dominio])
    ax.add_feature(cfeature.BORDERS, lw=0.4)
    ax.add_feature(cfeature.COASTLINE, lw=0.4)
    ax.set_aspect('auto', adjustable=None)
    gl = ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])
    
    f_poligono_SBP(dict_punti)
    f_poligono_EVS(dict_punti)

    shape_lat = int(dict_lat_lon[m]['lat'].shape[0] / 2)
    shape_lon = int(dict_lat_lon[m]['lon'].shape[0] / 2)

    lat1 = float(dict_lat_lon[m]['lat'][shape_lat:shape_lat + 1, shape_lat:shape_lat + 1][0][0])
    lon1 = float(dict_lat_lon[m]['lon'][shape_lon:shape_lon + 1, shape_lon:shape_lon + 1][0][0])

    lat2 = float(dict_lat_lon[m]['lat'][shape_lat + 1:shape_lat + 2, shape_lat + 1:shape_lat + 2][0][0])
    lon2 = float(dict_lat_lon[m]['lon'][shape_lon + 1:shape_lon + 2, shape_lon + 1:shape_lon + 2][0][0])

    p1 = (lat1, lon1)
    p2 = (lat2, lon2)
    dist = np.round(haversine(p1, p2), 1)
    # print(f'{m} {dist} km')

    ax.scatter(
        x=dict_lat_lon[m]['lon'],
        y=dict_lat_lon[m]['lat'],
        transform=ccrs.Geodetic(),
        marker='.',
        s=dict_marker_style[m][1],
        linewidth=dict_marker_style[m][2],
        edgecolors='black',
        # facecolors='black',
        zorder=2,
        # label=f'{m} [~{dist} km]'
    )

    # ax.legend(prop={'size': 5}, loc='upper right', framealpha=1)
    gl.xlabel_style = {'size': 5}
    gl.ylabel_style = {'size': 5}
    
    plt.title(m)
    plt.savefig(f'{cartella_lavoro}/griglie_{dominio}_{m}.png', dpi=600, format='png', bbox_inches='tight')
    
    # plt.show()
    plt.close()

print('esco')
exit()

# %%
# https://patorjk.com/software/taag/#p=display&f=Big&t=Studio%20grafico
#   _____ _             _ _                          __ _
#  / ____| |           | (_)                        / _(_)
# | (___ | |_ _   _  __| |_  ___     __ _ _ __ __ _| |_ _  ___ ___
#  \___ \| __| | | |/ _` | |/ _ \   / _` | '__/ _` |  _| |/ __/ _ \
#  ____) | |_| |_| | (_| | | (_) | | (_| | | | (_| | | | | (_| (_) |
# |_____/ \__|\__,_|\__,_|_|\___/   \__, |_|  \__,_|_| |_|\___\___/
#                                    __/ |
#                                   |___/

fig, ax = f_init_plot(dict_proj['PlateCarree'], dict_estremi_dominio['ERA5'])

f_cerchio_genova(dict_punti)
f_poligono_SBP(dict_punti)
f_poligono_EVS(dict_punti)

###
for i in dict_punti.keys():
    ax.scatter(
        x=dict_punti[i]['lon'],
        y=dict_punti[i]['lat'],
        transform=ccrs.Geodetic(),
        s=15,
        zorder=2
    )

plt.plot(
    [dict_punti['ventimiglia']['lon'], dict_punti['eolie']['lon']],
    [dict_punti['ventimiglia']['lat'], dict_punti['eolie']['lat']],
    transform=ccrs.Geodetic(),
    color='tab:red',
    zorder=0
)

plt.plot(
    [dict_punti['genova']['lon'], dict_punti['bejaja']['lon']],
    [dict_punti['genova']['lat'], dict_punti['bejaja']['lat']],
    transform=ccrs.Geodetic(),
    color='tab:green',
    zorder=0
)

plt.savefig(f"{cartella_lavoro}/studio_grafico.png", dpi=300, format='png', bbox_inches='tight')

# plt.show()
plt.close()

# %%
#  ______     _                 _
# |  ____|   | |               (_)
# | |__   ___| |_ _ __ __ _ _____  ___  _ __   ___
# |  __| / __| __| '__/ _` |_  / |/ _ \| '_ \ / _ \
# | |____\__ \ |_| | | (_| |/ /| | (_) | | | |  __/
# |______|___/\__|_|  \__,_/___|_|\___/|_| |_|\___|

### Da un confronto ERA5/NOAAv3 ho visto che l'estrazione è corretta, quindi non la tocco più

cartella_analisi = f'{quali_file}_analisi'
os.makedirs(cartella_analisi, exist_ok=True)

cartella_estrazioni = f'{cartella_analisi}/estrazioni'
os.makedirs(cartella_estrazioni, exist_ok=True)

lista_file_nc = sorted(os.listdir(f'{cartella_lavoro}/{quali_file}_annuali'))

df_msl = pd.DataFrame()

for f in lista_file_nc:
# for f in [x for x in lista_file_nc if '2011' in x]:
    f_log_ciclo_for([['estrazione - ', f, lista_file_nc]])

    riprendi = True
    df = f_estrazione_punti(riprendi, quali_file, f, nome_pressione, cartella_lavoro, cartella_estrazioni, dict_estremi_dominio['ERA5'])
    df_msl = pd.concat([df_msl, df], axis=0)

df_msl = df_msl.sort_index()

df_msl['Dp_bejaja-boa00296'] = np.clip((df_msl['bejaja'] - df_msl['boa00296']), a_min=0, a_max=None)
df_msl['Dp_eolie-ventimiglia'] = np.clip((df_msl['eolie'] - df_msl['ventimiglia']), a_min=0, a_max=None)
df_msl['Dp_punto_S-boa00296'] = np.clip((df_msl['punto_S'] - df_msl['boa00296']), a_min=0, a_max=None)

### È solo il plot, l'ho già fatto
df_msl[['Dp_bejaja-boa00296', 'Dp_punto_S-boa00296', 'Dp_eolie-ventimiglia']].plot(figsize=(12, 4), lw=0.8)
plt.axhline(y=19, color='grey', ls='-', lw=0.8, zorder=10)
plt.axhline(y=12, color='grey', ls='-', lw=0.8, zorder=10)
plt.ylim(bottom=0, top=40)
plt.legend(ncol=3)
plt.ylabel('hPa')
plt.title(quali_file, loc='left', fontsize=10, fontweight='bold')

if quali_file == 'NOAAv3':
    plt.axvline(x='1940-01-01 00:00:00', color='grey', ls='-', lw=0.8, zorder=10)

plt.savefig(f'{cartella_analisi}/prima_estrazione.png', dpi=300, format='png', bbox_inches='tight')

plt.show()
plt.close()

###
df_msl.loc[pd.date_range('1940-01-01 00:00:00', '2015-12-31 21:00:00', freq='3h'), ['Dp_bejaja-boa00296', 'Dp_punto_S-boa00296', 'Dp_eolie-ventimiglia']].plot(figsize=(12, 4), lw=0.8)
plt.axhline(y=19, color='grey', ls='-', lw=0.8, zorder=10)
plt.axhline(y=12, color='grey', ls='-', lw=0.8, zorder=10)
plt.ylim(bottom=0, top=40)
plt.legend(ncol=3)
plt.ylabel('hPa')
plt.title(f'{quali_file} inizio 1940 - fine 2015', loc='left', fontsize=10, fontweight='bold')

plt.savefig(f'{cartella_analisi}/prima_estrazione_1940-2015.png', dpi=300, format='png', bbox_inches='tight')

plt.show()
plt.close()

# %% Grafici di test sulla pressione

range_date = list(pd.date_range('2011-01-01 00:00:00', '2011-12-31 21:00:00', freq='3h'))
range_argidx = np.arange(len(range_date))

ds = xr.open_dataset(f"{cartella_lavoro}/{quali_file}_annuali/{[x for x in lista_file_nc if '2011' in x][0]}", engine='netcdf4')

if quali_file == 'NOAAv3':
    ds = f_correzione_NOAAv3(ds)

###
for t in pd.date_range('2011-12-16 00:00:00', '2011-12-16 12:00:00', freq='3h'):
    argidx = range_date.index(t)

    lon_2D, lat_2D = np.meshgrid(ds['longitude'], ds['latitude'])

    fig, ax = f_init_plot(dict_proj['PlateCarree'], dict_estremi_dominio['ERA5'])
    plt.title(f'{quali_file}, {str(t)}, modulo della pressione', loc='left', fontsize=8)

    pres = ax.contourf(
        lon_2D,
        lat_2D,
        ds[nome_pressione][argidx, ...] / 100,
        levels=20,
        extend='both',
        transform=dict_proj['PlateCarree']
    )

    count = ax.contour(
        lon_2D,
        lat_2D,
        ds[nome_pressione][argidx, ...] / 100,
        levels=20,
        colors='black',
        linewidths=1,
        transform=dict_proj['PlateCarree']
    )

    clabels = ax.clabel(
        count,
        inline=True,
        fmt=' {:.0f}'.format,
        fontsize=6
    )

    for l in clabels:
        l.set_rotation(0)

    f_poligono_SBP(dict_punti)
    f_poligono_EVS(dict_punti)

    cbar = plt.colorbar(pres)

    nome_png = f"test_pressione_{str(t).replace(' ', '_').replace(':', '-')}"
    plt.savefig(f'{cartella_analisi}/{nome_png}.png', dpi=300, format='png', bbox_inches='tight')

    # plt.show()
    plt.close()

# %%

"""
gruppi_anni = list(df_msl.groupby(df_msl.index.year))

for picco in [20, 22.5, 25, 27.5, 30]:
    if quali_file == 'ERA5':
        sr_picchi = pd.Series(np.nan, pd.date_range(f"{lista_file_nc[0].split('_')[-1].split('.')[0]}", f"{lista_file_nc[-1].split('_')[-1].split('.')[0]}", freq='1YS'))
    elif quali_file == 'NOAAv3':
        sr_picchi = pd.Series(np.nan, pd.date_range(f"{lista_file_nc[0].split('.')[1]}", f"{lista_file_nc[-1].split('.')[1]}", freq='1YS'))

    for gruppo in gruppi_anni:
        anno = gruppo[0]
        df_anno = gruppo[1]

        sr_picchi.loc[f'{anno}-01-01'] = (df_anno['Dp_bejaja-boa00296'].values > picco).sum()

        # df_anno['Dp_bejaja-boa00296'].plot()
        # plt.title(f"picchi {sr_picchi.loc[f'{anno}-01-01']}")
        # plt.ylim(bottom=-2, top=40)
        # plt.axhline(y=19, color='grey', ls='-', lw=0.8, zorder=-10)
        # plt.show()
        # plt.close()

    sr_picchi.plot()
    plt.title(f'Serie dei picchi oltre {picco} hPa su Dp_bejaja-boa00296')
    plt.show()
    plt.close()
"""

# %% Calcolo il gradiente del campo di pressione
#   _____               _ _            _
#  / ____|             | (_)          | |
# | |  __ _ __ __ _  __| |_  ___ _ __ | |_ ___
# | | |_ | '__/ _` |/ _` | |/ _ \ '_ \| __/ _ \
# | |__| | | | (_| | (_| | |  __/ | | | ||  __/
#  \_____|_|  \__,_|\__,_|_|\___|_| |_|\__\___|

cartella_gradienti = f'{cartella_analisi}/gradienti'
os.makedirs(cartella_gradienti, exist_ok=True)

for f in lista_file_nc:
# for f in [x for x in lista_file_nc if '2011' in x]:
    f_log_ciclo_for([['gradiente - ', f, lista_file_nc]])

    riprendi = True
    f_calcolo_gradiente(riprendi, quali_file, f, nome_pressione, cartella_lavoro, cartella_gradienti, dict_estremi_dominio['ERA5'])

# %% Grafici di test sul gradiente

range_date = list(pd.date_range('2011-01-01 00:00:00', '2011-12-31 21:00:00', freq='3h'))
range_argidx = np.arange(len(range_date))

gradiente_msl = pickle.load(open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_2011.pkl', 'rb'))

ds = xr.open_dataset(f"{cartella_lavoro}/{quali_file}_annuali/{[x for x in lista_file_nc if '2011' in x][0]}", engine='netcdf4')

if quali_file == 'NOAAv3':
    ds = f_correzione_NOAAv3(ds, dict_estremi_dominio['ERA5'])

###
for t in pd.date_range('2011-12-16 00:00:00', '2011-12-16 12:00:00', freq='3h'):
    argidx = range_date.index(t)

    lon_2D, lat_2D = np.meshgrid(ds['longitude'], ds['latitude'])

    fig, ax = f_init_plot(dict_proj['PlateCarree'], dict_estremi_dominio['ERA5'])
    plt.title(f'{quali_file}, {str(t)}, modulo del gradiente di pressione', loc='left', fontsize=8)

    grad = ax.contourf(
        lon_2D,
        lat_2D,
        gradiente_msl['mod'][argidx, ...],
        levels=livelli_grad,
        extend='max',
        transform=ccrs.PlateCarree()
    )

    frecce_grad = ax.quiver(
        lon_2D[::skip_frecce, ::skip_frecce],
        lat_2D[::skip_frecce, ::skip_frecce],
        gradiente_msl['x'][argidx, ::skip_frecce, ::skip_frecce],
        gradiente_msl['y'][argidx, ::skip_frecce, ::skip_frecce],
        transform=ccrs.PlateCarree(),
        scale=scale,
        pivot='tail'
    )

    count = ax.contour(
        lon_2D,
        lat_2D,
        ds[nome_pressione][argidx, ...] / 100,
        levels=20,
        colors='black',
        linewidths=1,
        transform=ccrs.PlateCarree()
    )

    clabels = ax.clabel(
        count,
        inline=True,
        fmt=' {:.0f}'.format,
        fontsize=6
    )

    f_poligono_SBP(dict_punti)
    f_poligono_EVS(dict_punti)

    cbar = plt.colorbar(grad)

    nome_png = f"test_gradiente_{str(t).replace(' ', '_').replace(':', '-')}"
    plt.savefig(f"{cartella_analisi}/{nome_png}.png", dpi=300, format='png', bbox_inches='tight')

    # plt.show()
    plt.close()

# %%
#                             _         _   _          _
#     /\                     | |       | | | |        | |
#    /  \   _ __   __ _  ___ | | ___   | |_| |__   ___| |_ __ _
#   / /\ \ | '_ \ / _` |/ _ \| |/ _ \  | __| '_ \ / _ \ __/ _` |
#  / ____ \| | | | (_| | (_) | | (_) | | |_| | | |  __/ || (_| |
# /_/    \_\_| |_|\__, |\___/|_|\___/   \__|_| |_|\___|\__\__,_|
#                  __/ |
#                 |___/

convenzione = 'from'

cartella_theta = f'{cartella_analisi}/theta'
os.makedirs(cartella_theta, exist_ok=True)

for f in lista_file_nc:
    f_log_ciclo_for([['theta - ', f, lista_file_nc]])

    riprendi = True
    f_calcolo_theta(riprendi, quali_file, convenzione, cartella_theta, cartella_gradienti)

# %% Grafici di test su theta

range_date = list(pd.date_range('2011-01-01 00:00:00', '2011-12-31 21:00:00', freq='3h'))
range_argidx = np.arange(len(range_date))

livelli_theta_completi = np.linspace(0, 360, 31)
livelli_theta = list(np.linspace(0, 360, 5))
angoli_thate = ['N', 'E', 'S', 'W', 'N']

theta = pickle.load(open(f'{cartella_theta}/ndarray_theta_{quali_file}_2011.pkl', 'rb'))
gradiente_msl = pickle.load(open(f'{cartella_gradienti}/dict_gradiente_{quali_file}_2011.pkl', 'rb'))

ds = xr.open_dataset(f"{cartella_lavoro}/{quali_file}_annuali/{[x for x in lista_file_nc if '2011' in x][0]}", engine='netcdf4')

if quali_file == 'NOAAv3':
    ds = f_correzione_NOAAv3(ds, dict_estremi_dominio['ERA5'])

for t in pd.date_range('2011-12-16 00:00:00', '2011-12-16 12:00:00', freq='3h'):
    argidx = range_date.index(t)

    lon_2D, lat_2D = np.meshgrid(ds['longitude'], ds['latitude'])

    fig, ax = f_init_plot(dict_proj['PlateCarree'], dict_estremi_dominio['ERA5'])
    plt.title(f'{quali_file}, {str(t)}, angolo del gradiente di pressione', loc='left', fontsize=8)

    if convenzione == 'to':
        cmap = 'twilight'
    else:
        cmap = 'twilight_shifted'

    plot = ax.contourf(
        lon_2D,
        lat_2D,
        theta[argidx, ...],
        levels=livelli_theta_completi,
        cmap=cmap,
        transform=ccrs.PlateCarree()
    )

    frecce_grad = ax.quiver(
        lon_2D[::skip_frecce, ::skip_frecce],
        lat_2D[::skip_frecce, ::skip_frecce],
        gradiente_msl['x'][argidx, ::skip_frecce, ::skip_frecce],
        gradiente_msl['y'][argidx, ::skip_frecce, ::skip_frecce],
        transform=ccrs.PlateCarree(),
        scale=scale,
        pivot='tail'
    )

    cbar = plt.colorbar(plot)
    cbar.set_ticks(livelli_theta)
    cbar.set_ticklabels(angoli_thate)

    f_poligono_SBP(dict_punti)
    f_poligono_EVS(dict_punti)

    nome_png = f"test_theta_{str(t).replace(' ', '_').replace(':', '-')}"
    plt.savefig(f"{cartella_analisi}/{nome_png}.png", dpi=300, format='png', bbox_inches='tight')

    # plt.show()
    plt.close()

# %%
#  __  __          _ _                    _               _ _                   _
# |  \/  |        | (_)                  (_)             | (_)                 (_)
# | \  / | ___  __| |_  __ _   _ __   ___ _   _ __   ___ | |_  __ _  ___  _ __  _
# | |\/| |/ _ \/ _` | |/ _` | | '_ \ / _ \ | | '_ \ / _ \| | |/ _` |/ _ \| '_ \| |
# | |  | |  __/ (_| | | (_| | | | | |  __/ | | |_) | (_) | | | (_| | (_) | | | | |
# |_|  |_|\___|\__,_|_|\__,_| |_| |_|\___|_| | .__/ \___/|_|_|\__, |\___/|_| |_|_|
#                                            | |               __/ |
#                                            |_|              |___/

### Creo una maschera per i punti dentro il poligono
poligono_SBP = Polygon(
    [(dict_punti['spezia']['lon'], dict_punti['spezia']['lat']),
     (dict_punti['bejaja']['lon'], dict_punti['bejaja']['lat']),
     (dict_punti['perpignano']['lon'], dict_punti['perpignano']['lat']),
     (dict_punti['spezia']['lon'], dict_punti['spezia']['lat'])]
    )

mask_poligono_SBP = np.zeros_like(theta[argidx, ...], dtype=bool)
for i in range(lon_2D.shape[0]):
    for j in range(lon_2D.shape[1]):
        point = Point(lon_2D[i, j], lat_2D[i, j])
        if poligono_SBP.contains(point):
            mask_poligono_SBP[i, j] = True

plt.imshow(mask_poligono_SBP)
plt.savefig(f'{cartella_analisi}/maschera_poligono_SBP.png', dpi=300, format='png', bbox_inches='tight')
# plt.show()
plt.close()

### Creo una maschera per i punti dentro il poligono
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

mask_poligono_EVS = np.zeros_like(theta[argidx, ...], dtype=bool)
for i in range(lon_2D.shape[0]):
    for j in range(lon_2D.shape[1]):
        point = Point(lon_2D[i, j], lat_2D[i, j])
        if poligono_EVS.contains(point):
            mask_poligono_EVS[i, j] = True

plt.imshow(mask_poligono_EVS)
plt.savefig(f'{cartella_analisi}/maschera_poligono_EVS.png', dpi=300, format='png', bbox_inches='tight')
# plt.show()
plt.close()

# !!! È possibile che debba girare le latitudini del NOAAv3 --> sembra di no

# %%
sr_theta_medi_poligono_SBP = pd.Series(index=df_msl.index)
sr_theta_medi_poligono_EVS = pd.Series(index=df_msl.index)

for f in lista_file_nc:
    f_log_ciclo_for([['theta medi - ', f, lista_file_nc]])

    anno = f_prendi_anno(f, quali_file)
    theta = pickle.load(open(f'{cartella_theta}/ndarray_theta_{quali_file}_{anno}.pkl', 'rb'))
    range_date = pd.date_range(start=f'{anno}-01-01 00:00:00', periods=theta.shape[0], freq='3h')

    for i, t in enumerate(range_date):
        campo_maschera_poligono_SBP = np.where(mask_poligono_SBP, theta[i, ...], np.nan)
        media_poligono_SBP = stats.circmean(campo_maschera_poligono_SBP, nan_policy='omit', low=0, high=360)
        sr_theta_medi_poligono_SBP.loc[t] = media_poligono_SBP

        campo_maschera_poligono_EVS = np.where(mask_poligono_EVS, theta[i, ...], np.nan)
        media_poligono_EVS = stats.circmean(campo_maschera_poligono_EVS, nan_policy='omit', low=0, high=360)
        sr_theta_medi_poligono_EVS.loc[t] = media_poligono_EVS

# !!! Il problema è che devo aggiungere un offset a degli angoli

# In questo modo un 'Sud' corrisponde a delle linee di gradiente perfettamente dirette verso 'Nord'.
# 'Sud' corrisponde quindi alla direzione ottimale del gradiente.
# Ma 'Sud' corrisponde a 3.14 rad, non a 0 deg come come invece è scritto nelle bozze di Sasha.
# Che metta convention='to' oppure convention='from', devo comunque mettere (o togliere) pi greco

print(sr_theta_medi_poligono_SBP.loc['2011-12-16 00:00:00':'2011-12-16 12:00:00'])
print(np.deg2rad(sr_theta_medi_poligono_SBP.loc['2011-12-16 00:00:00':'2011-12-16 12:00:00']))

# df_msl['theta_medi_poligono_SBP'] = np.deg2rad(sr_theta_medi_poligono_SBP)
# df_msl['theta_medi_poligono_EVS'] = np.deg2rad(sr_theta_medi_poligono_EVS)

### Questo è il modo corretto di aggiungere un offset ad una variabile circolare
df_msl['theta_medi_grad_poligono_SBP'] = np.mod(sr_theta_medi_poligono_SBP + 180, 360)
df_msl['theta_medi_grad_poligono_EVS'] = np.mod(sr_theta_medi_poligono_EVS + 180, 360)

df_msl['theta_medi_rad_poligono_SBP'] = np.deg2rad(df_msl['theta_medi_grad_poligono_SBP'])
df_msl['theta_medi_rad_poligono_EVS'] = np.deg2rad(df_msl['theta_medi_grad_poligono_EVS'])

print(df_msl.loc['2011-12-16 00:00:00':'2011-12-16 12:00:00', 'theta_medi_grad_poligono_SBP'])
print(np.deg2rad(df_msl.loc['2011-12-16 00:00:00':'2011-12-16 12:00:00', 'theta_medi_grad_poligono_SBP']))

# %%
#  _____                               _               ______
# |  __ \                             | |             |  ____|
# | |__) |_ _ _ __ __ _ _ __ ___   ___| |_ _ __ ___   | |____      __
# |  ___/ _` | '__/ _` | '_ ` _ \ / _ \ __| '__/ _ \  |  __\ \ /\ / /
# | |  | (_| | | | (_| | | | | | |  __/ |_| | | (_) | | |___\ V  V /
# |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__|_|  \___/  |______\_/\_/

theta_opt_SBP = 0
theta_opt_EVS = np.deg2rad(-60)

df_msl['Ew_poligono_SBP'] = df_msl['Dp_bejaja-boa00296'] * np.cos(theta_opt_SBP + df_msl['theta_medi_rad_poligono_SBP'])
df_msl['Ew_poligono_EVS'] = df_msl['Dp_eolie-ventimiglia'] * np.cos(theta_opt_EVS + df_msl['theta_medi_rad_poligono_EVS'])

cartella_risultati_annuali = f'{cartella_analisi}/risultati_annuali'
os.makedirs(cartella_risultati_annuali, exist_ok=True)

for f in lista_file_nc:
    f_log_ciclo_for([['Ew - ', f, lista_file_nc]])

    anno = int(f_prendi_anno(f, quali_file))

    for i, j in zip(['Dp_bejaja-boa00296', 'Dp_eolie-ventimiglia'], ['SBP', 'EVS']):

        if os.path.exists(f'{cartella_risultati_annuali}/risultati_{j}_{anno}.png'):
            continue

        fig, ax = plt.subplots(figsize=(9, 9))
        df_msl.loc[[x for x in df_msl.index if x.year==anno], [i, f'Ew_poligono_{j}']].plot(ax=ax, figsize=(10, 4), lw=1, color=['tab:blue', 'tab:orange', 'tab:green'])
        ax.legend(prop={'size': 7}, ncol=2, loc='lower left')
        ax.set_ylabel('hPa')
        ax.set_ylim(bottom=-2, top=30)
        ax.set_yticks([-4, 0, 5, 10, 15, 20, 25, 30])
        ax.set_yticklabels(['', 0, 5, 10, 15, 20, 25, 30])
        ax.axhline(y=19, color='grey', ls='--', lw=0.5, zorder=-10)
        ax.set_title(f'{quali_file} {j}', fontsize=10, fontweight='bold', loc='left')

        ax2 = ax.twinx()
        df_msl.loc[[x for x in df_msl.index if x.year==anno], f'theta_medi_grad_poligono_{j}'].plot(ax=ax2, figsize=(10, 4), lw=1, legend=True, color=['tab:green'])
        ax2.legend(prop={'size': 7}, loc='lower right')
        ax2.set_ylabel('direzione del gradiente')
        ax2.set_ylim(bottom=-22, top=360)
        ax2.set_yticks([-1260, 0, 90, 180, 270, 360, 450])
        ax2.set_yticklabels(['', 'N', 'E', 'S', 'W', 'N', ''])
        ax2.axhline(y=0, color='grey', ls=':', lw=0.5, zorder=-10)
        ax2.axhline(y=360, color='grey', ls=':', lw=0.5, zorder=-10)

        plt.savefig(f'{cartella_risultati_annuali}/risultati_{j}_{anno}.png', dpi=300, format='png', bbox_inches='tight')

        # plt.show()
        plt.close()

df_msl = df_msl.round(2)
df_msl.to_csv(f'{cartella_analisi}/df_analisi.csv', index=True, header=True, mode='w', na_rep=np.nan)

print('\n\nDone.')
