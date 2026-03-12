
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

cartella_lavoro = '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati/ERA5_singoli'
os.chdir(cartella_lavoro)
cartella_plot = '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati/ERA5_singoli/plot_ERA5'
os.makedirs(cartella_plot, exist_ok=True)

lista_cartelle_cicloni = [x for x in os.listdir(cartella_lavoro) if x.startswith('ciclone_')]

### Definisco il dizionario delle aree
dict_aree = {
    'Med': [0, 14, 37, 45],
    'Med1': [0, 20, 36, 47],
    'Med1D': [-2, 20, 36, 48],
    'Med2': [5, 18, 36, 45],
    'alps': [3, 16, 40, 50],
    'METEOSAT': [-20, 29.95, 30, 59.95],
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

area = 'Med1D'
colore_confini = 'black'
spessore_confini = 1.1
spessore_isobare = 0.4
skip_hPa = 1
livelli_msl = np.arange(900, 1050, skip_hPa)
colore_msl = 'black'
skip_vento = 2 # 8
zorder_vento = 100
lunghezza_barbette = 4 # 4.5
spessore_barbette = 0.4
dpi = 300
limite_inferiore_kn = 5
ms2knt = 1.94384

for cartella in lista_cartelle_cicloni[0:1]:

    sub_cartella_plot = f"{cartella_plot}/{cartella}"
    os.makedirs(sub_cartella_plot, exist_ok=True)

    lista_file_nc = sorted(os.listdir(f'{cartella_lavoro}/{cartella}'))

    for f in lista_file_nc:

        ds = xr.open_dataset(f'{cartella_lavoro}/{cartella}/{f}', engine='netcdf4')

        valid_time = pd.to_datetime(ds['valid_time'].values)
        latitude = ds['latitude'].values
        longitude = ds['longitude'].values

        longitude, latitude = np.meshgrid(longitude, latitude)

        u10 = ds['u10'].values
        v10 = ds['v10'].values
        msl = ds['msl'].values / 100 # da Pa a hPa

        si10 = np.sqrt(u10 ** 2 + v10 ** 2)
        nodi10 = si10 * ms2knt

        for ind_t, t in enumerate(valid_time):

            nome_png = f"{area}_{str(t).replace(' ', '_').replace(':', '-')}.png"

            if os.path.exists(f'{sub_cartella_plot}/{nome_png}'):
                print(f'\n{sub_cartella_plot}/{nome_png} esiste. Continuo.\n')
                continue

            print(cartella, f, str(t))

            fig = plt.figure(figsize=(7, 4))
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

            ax.set_extent(dict_aree[area])
            ax.add_feature(cf.COASTLINE, lw=spessore_confini, edgecolor=colore_confini)
            ax.add_feature(cf.BORDERS, lw=spessore_confini, edgecolor=colore_confini)

            ### Contorni MSL
            plot_msl = ax.contour(
                longitude,
                latitude,
                msl[ind_t, ...],
                transform=ccrs.PlateCarree(),
                colors=colore_msl,
                levels=livelli_msl,
                linewidths=spessore_isobare,
            )

            clabels = ax.clabel(plot_msl,
                                colors=colore_msl,
                                inline_spacing=10,
                                inline=True,
                                fontsize=6,
                                zorder=zorder_vento + 1 # devono essere sempre sopra
                                )

            [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=1)) for txt in clabels]
            [txt.set_rotation(0) for txt in clabels]

            ### Barbette del vento a 10m
            knu10_t, knv10_t = u10[ind_t, :, :] * ms2knt, v10[ind_t, :, :] * ms2knt
            ws10_t = si10[ind_t, :, :]
            nodi10_t = nodi10[ind_t, :, :]

            mask = nodi10_t[::skip_vento, ::skip_vento] >= limite_inferiore_kn

            plot_ws10 = ax.barbs(
                longitude[::skip_vento, ::skip_vento][mask],
                latitude[::skip_vento, ::skip_vento][mask],
                knu10_t[::skip_vento, ::skip_vento][mask],
                knv10_t[::skip_vento, ::skip_vento][mask],
                ws10_t[::skip_vento, ::skip_vento][mask],
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

            plt.title(f"ERA5   {str(t)} UTC\n{ds['msl'].attrs['long_name']} [hPa] (interval: {skip_hPa} hPa)        10 meter wind speed [m/s]", fontsize=9)

            plt.savefig(f"{sub_cartella_plot}/{nome_png}", dpi=dpi, format='png', bbox_inches='tight')

            plt.show()
            plt.close()
            sss

print("\n\nDone")
