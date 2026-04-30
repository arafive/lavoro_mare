
import os

import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cf

import matplotlib.pyplot as plt
import matplotlib.font_manager as mfont

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import BoundaryNorm

###
###

font_files = mfont.findSystemFonts(fontpaths='../Helvetica')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)

plt.rc('font', family='Helvetica', weight='normal', size=8)

# %%

cartella_plot = '/run/media/daniele.carnevale/Daniele2TB/repo/lavoro_mare/dati/NOAAv2c_singoli/plot_NOAAv2c'
os.makedirs(cartella_plot, exist_ok=True)

# lista_cartelle_cicloni = [x for x in os.listdir(cartella_lavoro) if x.startswith('ciclone_')]
lista_range_tempi = [
    ['1910-01-18', '1910-01-22'],
    ['1935-12-03', '1935-12-05'],
    ['1981-12-11', '1981-12-14'],
]

cartella_msl = '/run/media/daniele.carnevale/Daniele2TB/repo/lavoro_mare/dati/NOAAv2c_prmsl_annuali'
cartella_u = '/run/media/daniele.carnevale/Daniele2TB/repo/lavoro_mare/dati/NOAAv2c_u-wind_annuali'
cartella_v = '/run/media/daniele.carnevale/Daniele2TB/repo/lavoro_mare/dati/NOAAv2c_v-wind_annuali'

### Definisco il dizionario delle aree
dict_aree = {
    'Med': [0, 14, 37, 45],
    'Med1': [0, 20, 36, 47],
    'Med1D': [-2, 20, 36, 48],
    'Med2': [5, 18, 36, 45],
    'alps': [3, 16, 40, 50],
    'METEOSAT': [-20, 29.95, 30, 59.95],
    'EC08': [-30, 50, 20, 70]
}

### Definisco la colorbar
colori_ms = np.array([
    [255, 255, 255], # < 2
    [71, 158, 248], # 2-5
    [100, 217, 64], # 5-10
    [222, 177, 74], # 10-15
    [220, 48, 129], # 15-25
    [119, 21, 212], # 25-40
    [37, 59, 245], # > 40
])

colorbar_ms = [[color / 255 for color in liste] for liste in [list(x) for x in colori_ms[1:-1]]]
colorbar_ms = LinearSegmentedColormap.from_list('colorbar_ms', colorbar_ms, len(colorbar_ms))
bounds = [2, 5, 10, 15, 25, 40]
colorbar_ms.set_over(np.array(colori_ms[-1]) / 255)
colorbar_ms.set_under(np.array(colori_ms[0]) / 255)
norm = BoundaryNorm(bounds, colorbar_ms.N)

# %%
### Parametri

area = 'EC08'
colore_confini = 'black'
spessore_confini = 0.8
spessore_isobare = 0.4
skip_hPa = 2
livelli_msl = np.arange(900, 1050, skip_hPa)
colore_msl = 'black'
skip_vento = 1
zorder_vento = 100
lunghezza_barbette = 4 # 4.5
spessore_barbette = 0.4
dpi = 300
limite_inferiore_kn = 5
ms2knt = 1.94384

def f_correzione_NOAA(ds):
    ds = ds.rename({'lon': 'longitude'})
    ds = ds.rename({'lat': 'latitude'})
    
    ds['_longitude_180'] = xr.where(ds['longitude'] > 180, ds['longitude'] - 360, ds['longitude'])
    ds = (ds.swap_dims({'longitude': '_longitude_180'}).sel(**{'_longitude_180': sorted(ds['_longitude_180'])}).drop_vars('longitude'))
    ds = ds.rename({'_longitude_180': 'longitude'})
    
    return ds


for range_tempo in lista_range_tempi:
    
    cartella = f"ciclone_{range_tempo[0].split('-')[0]}_{range_tempo[0].split('-')[1]}_{range_tempo[0].split('-')[2]}"
    
    sub_cartella_plot = f'{cartella_plot}/{cartella}'
    os.makedirs(sub_cartella_plot, exist_ok=True)
    
    range_temporale_da_plottare = pd.date_range(range_tempo[0], pd.to_datetime(range_tempo[1]) + pd.DateOffset(days=1), freq='6h')

    ### Devo prendere il file che contiene il range temporale
    
    netcdf_msl = f"{cartella_msl}/prmsl.{range_tempo[0].split('-')[0]}.nc"
    netcdf_u = f"{cartella_u}/uwnd.10m.{range_tempo[0].split('-')[0]}.nc"
    netcdf_v = f"{cartella_v}/vwnd.10m.{range_tempo[0].split('-')[0]}.nc"

    ds_msl = f_correzione_NOAA(xr.open_dataset(netcdf_msl, engine='netcdf4'))
    ds_u = f_correzione_NOAA(xr.open_dataset(netcdf_u, engine='netcdf4'))
    ds_v = f_correzione_NOAA(xr.open_dataset(netcdf_v, engine='netcdf4'))
    
    longitude_msl, latitude_msl = np.meshgrid(ds_msl['longitude'].values, ds_msl['latitude'].values)
    longitude_uv, latitude_uv   = np.meshgrid(ds_u['longitude'].values, ds_u['latitude'].values)
    
    msl = ds_msl['prmsl'] / 100 # da Pa a hPa
    u10 = ds_u['uwnd'] #!!! Il vento è ogni 3 ore, mentre la pressione ogni 6
    v10 = ds_v['vwnd']

    si10 = np.sqrt(u10 ** 2 + v10 ** 2)
    nodi10 = si10 * ms2knt
    
    valid_time = pd.to_datetime(ds_msl['time'].values)
    
    try:
        assert range_temporale_da_plottare[0].year == range_temporale_da_plottare[-1].year, "C'è uno scavallamento di anni"
    except AssertionError:
        continue
    
    for ind_t, t in enumerate(valid_time):
        
        if t in range_temporale_da_plottare:
            pass
        else:
            continue
        
        nome_png = f"{area}_{str(t).replace(' ', '_').replace(':', '-')}.png"
        
        # if os.path.exists(f'{sub_cartella_plot}/{nome_png}'):
        #     print(f'\n{sub_cartella_plot}/{nome_png} esiste. Continuo.\n')
        #     continue
        
        print(cartella, str(t))
        
        fig = plt.figure(figsize=(7, 4))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        ax.set_extent(dict_aree[area])
        ax.add_feature(cf.COASTLINE, lw=spessore_confini, edgecolor=colore_confini)
        ax.add_feature(cf.BORDERS, lw=spessore_confini, edgecolor=colore_confini)

        ### Contorni MSL
        plot_msl = ax.contour(
            longitude_msl,
            latitude_msl,
            msl.sel(time=t),
            transform=ccrs.PlateCarree(),
            colors=colore_msl,
            levels=livelli_msl,
            linewidths=spessore_isobare,
        )

        clabels = ax.clabel(plot_msl,
                            colors=colore_msl,
                            inline_spacing=10,
                            inline=True,
                            fontsize=5,
                            zorder=zorder_vento + 1 # devono essere sempre sopra
                            )

        [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=1)) for txt in clabels]
        [txt.set_rotation(0) for txt in clabels]

        ### Barbette del vento a 10m
        knu10_t = u10.sel(time=t) * ms2knt
        knv10_t = v10.sel(time=t) * ms2knt
        ws10_t = si10.sel(time=t)
        nodi10_t = nodi10.sel(time=t)
        nodi10_t = nodi10_t.where(nodi10_t >= limite_inferiore_kn)

        plot_ws10 = ax.barbs(
            longitude_uv[::skip_vento, ::skip_vento],
            latitude_uv[::skip_vento, ::skip_vento],
            knu10_t[::skip_vento, ::skip_vento],
            knv10_t[::skip_vento, ::skip_vento],
            ws10_t[::skip_vento, ::skip_vento],
            length=lunghezza_barbette,
            linewidth=spessore_barbette,
            cmap=colorbar_ms,
            norm=norm,
            zorder=zorder_vento
        )

        cbar = plt.colorbar(plot_ws10, extend='both', extendfrac=0.1, spacing='uniform', drawedges=True)
        cbar.set_label('m/s', fontsize=10)
        cbar.ax.tick_params(axis='y', which='both', length=0)

        # ax.axis('off')
        ax.set_aspect('auto', adjustable=None)

        plt.title(f"NOAAv2c   {str(t)} UTC\n{ds_msl['prmsl'].attrs['long_name']} [hPa] (interval: {skip_hPa} hPa)        10 meter wind speed [m/s]", fontsize=8)

        plt.savefig(f"{sub_cartella_plot}/{nome_png}", dpi=dpi, format='png', bbox_inches='tight')
        
        # plt.show()
        plt.close()
        # sss
        
        # plt.imshow(nodi10[ind_t])
        # plt.title(t)
        # plt.show()
        # plt.close()
    # sss
        
print("\n\nDone")
