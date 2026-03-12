
"""
Mail del 30 gennaio 2026 ore 17:14

"""

import os

import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import matplotlib.pyplot as plt
import matplotlib.font_manager as mfont

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap
from matplotlib.colors import BoundaryNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable

###
###

font_files = mfont.findSystemFonts(fontpaths='../../Helvetica')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)

plt.rc('font', family='Helvetica', weight='normal', size=8)

cartella_lavoro = '/run/media/daniele.carnevale/Daniele2TB/test/lavoro_mare/script/ennesima_richiesta'
os.chdir(cartella_lavoro)

cartella_dati = '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati'

# %%
file_date = '/run/media/daniele.carnevale/Daniele2TB/test/lavoro_mare/script/ennesima_richiesta/eventiSLP_overThreshold_study_period_Daniele.xlsx'

df_date = pd.read_excel(file_date, index_col=0)
df_date['posix_start'] = pd.to_datetime(df_date['posix_start'], format='mixed')
df_date['posix_end'] = pd.to_datetime(df_date['posix_end'], format='mixed')

# lista_colori, livelli = [
#     '#400040',
#     '#600060',
#     '#aa00aa',
#     '#801080',
#     '#600040',
#     '#303366',
#     '#003399',
#     '#0000cc',
#     '#0000ff',
#     '#0055ff',
#     '#0099ff',
#     '#33ccff',
#     '#66ffff',
#     '#66ff99',
#     '#66ff66',
#     '#66ff00',
#     '#bffa0e',
#     '#ffff09',
#     '#ffff86',
#     '#fde851',
#     '#fde851',
#     '#ffcc00',
#     '#ff9900',
#     '#ff6600',
#     '#ff3333',
#     '#ff3300',
#     '#ff0000',
#     '#cc0000',
#     '#990000',
#     '#6c0000',
#     '#4f0000',
#     '#000000'], np.arange(492, 612 + 4, 4)

lista_colori, livelli = ["#aaaaaa", "#00a0ff", "#00dc00", "#e6af2d", "#f00082", "#8200dc", "#1e3cff"], [2, 5, 10, 15, 25, 40]

cmap = ListedColormap(lista_colori[1:-1])
cmap.set_under(lista_colori[0])
cmap.set_over(lista_colori[-1])
norm = BoundaryNorm(livelli, cmap.N)

area_ecsyn = [-40, 40, 25, 70]
ms2knt = 1.94384
step_vento = 1
lunghezza_barb = 5

def f_correzione_NOAA(ds):
    ds = ds.rename({'lon': 'longitude'})
    ds = ds.rename({'lat': 'latitude'})
    
    ds['_longitude_180'] = xr.where(ds['longitude'] > 180, ds['longitude'] - 360, ds['longitude'])
    ds = (ds.swap_dims({'longitude': '_longitude_180'}).sel(**{'_longitude_180': sorted(ds['_longitude_180'])}).drop_vars('longitude'))
    ds = ds.rename({'_longitude_180': 'longitude'})
    
    return ds

for ind_ciclone in df_date.index:
    
    cartella = f'ciclone_{ind_ciclone}'
    sub_cartella_plot = f'{cartella_lavoro}/{cartella}'
    os.makedirs(sub_cartella_plot, exist_ok=True)
    
    anno = df_date.loc[ind_ciclone]['posix_start'].year
    assert df_date.loc[ind_ciclone]['posix_start'].year == df_date.loc[ind_ciclone]['posix_end'].year

    netcdf_msl = f"{cartella_dati}/NOAAv2c_prmsl_annuali/prmsl.{anno}.nc"
    netcdf_gh = f"{cartella_dati}/NOAAv2c_hgt_annuali/hgt.{anno}.nc"
    netcdf_u = f"{cartella_dati}/NOAAv2c_u-wind_annuali/uwnd.10m.{anno}.nc"
    netcdf_v = f"{cartella_dati}/NOAAv2c_v-wind_annuali/vwnd.10m.{anno}.nc"

    ds_msl = f_correzione_NOAA(xr.open_dataset(netcdf_msl, engine='netcdf4'))
    ds_gh = f_correzione_NOAA(xr.open_dataset(netcdf_gh, engine='netcdf4'))
    ds_u = f_correzione_NOAA(xr.open_dataset(netcdf_u, engine='netcdf4'))
    ds_v = f_correzione_NOAA(xr.open_dataset(netcdf_v, engine='netcdf4'))
    
    longitude_msl, latitude_msl = np.meshgrid(ds_msl['longitude'].values, ds_msl['latitude'].values)
    longitude_gh, latitude_gh   = np.meshgrid(ds_gh['longitude'].values, ds_gh['latitude'].values)
    
    valid_time = pd.to_datetime(ds_msl['time'].values)
    
    range_temporale_da_plottare = pd.date_range(df_date.loc[ind_ciclone]['posix_start'], df_date.loc[ind_ciclone]['posix_end'] + pd.DateOffset(hours=6), freq='6h')

    # ds_subset = ds.where((ds.valid_time >= range_evento[0]) & (ds.valid_time <= range_evento[-1]), drop=True)
    # tempi_subset = pd.to_datetime(ds_subset['valid_time'].values)
    
    for t in range_temporale_da_plottare:
        
        if not os.path.exists(f"{sub_cartella_plot}/{t.strftime('%Y-%m-%d-%H%M%S')}.png"):
        # if os.path.exists(f"{sub_cartella_plot}/{t.strftime('%Y-%m-%d-%H%M%S')}.png"):
            
            print(f'{ind_ciclone} - {t}')
            
            fig, ax = plt.subplots(figsize=(8, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    
            ax.set_extent(area_ecsyn)
            ax.add_feature(cfeature.LAND, facecolor='gainsboro')
            ax.coastlines(resolution='50m', lw=0.8)
            ax.add_feature(cfeature.BORDERS, lw=0.8)
            
            msl = ds_msl.sel(time=t)['prmsl'] / 100 # da Pa a hPa
            # gh500 = ds_gh.sel(time=t, level=500)['hgt'] / 10 # da m a dam
            u10 = ds_u.sel(time=t)['uwnd']
            v10 = ds_v.sel(time=t)['vwnd']
            u10kt = ds_u.sel(time=t)['uwnd'] * ms2knt # da m/s a nodi
            v10kt = ds_v.sel(time=t)['vwnd'] * ms2knt # da m/s a nodi
    
            si10 = np.sqrt(u10 ** 2 + v10 ** 2)
            # nodi10 = si10 * ms2knt
        
            # cf = ax.contourf(
            #     ds_gh.longitude,
            #     ds_gh.latitude,
            #     gh500.values,
            #     levels=livelli,
            #     cmap=cmap,
            #     norm=norm,
            #     extend="both",
            #     transform=ccrs.PlateCarree()
            # )
    
            # cfc = ax.contour(
            #     ds_gh.longitude,
            #     ds_gh.latitude,
            #     gh500.values,
            #     levels=livelli,
            #     colors='black',
            #     linewidths=0.2,
            #     transform=ccrs.PlateCarree()
            # )
        
            cs = ax.contour(
                ds_msl.longitude,
                ds_msl.latitude,
                msl.values,
                levels=np.arange(950, 1050 + 2, 2),
                colors='black',
                linewidths=0.5,
                transform=ccrs.PlateCarree()
            )   
    
            clabel = ax.clabel(cs, fmt='%d', fontsize=3, zorder=100)
            for l in clabel:
                l.set_color('black')
                l.set_rotation(0)
                l.set_bbox(dict(facecolor='white', edgecolor='none', boxstyle='square,pad=0.1', alpha=0.9))    
    
            cf = ax.barbs(
                ds_u.longitude[::step_vento],
                ds_u.latitude[::step_vento],
                u10[::step_vento, ::step_vento],
                v10[::step_vento, ::step_vento],
                si10[::step_vento, ::step_vento],
                length=lunghezza_barb,
                linewidth=0.3,
                # color='black',
                cmap=cmap,
                norm=norm,
                zorder=200,
                pivot='middle',
                # sizes={'emptybarb': 0.025},
                sizes={'emptybarb': 0.0},
                transform=ccrs.PlateCarree()
            )
    
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="2%", pad=0.15, axes_class=plt.Axes)
        
            cbar = plt.colorbar(
                cf,
                cax=cax,
                ticks=livelli,
                orientation="vertical",
                extend='both',
                drawedges=True,
                # shrink=0.45,
                # pad=0.015,
                # fraction=0.03,
                # aspect=30
            )
            
            cbar.ax.tick_params(labelsize=5, length=0)
    
            # titolo_variabili = 'Geopotenziale a 500 hPa (dam, shaded) e MSLP (hPa, contour)'
            # titolo_variabili = 'Geopotenziale a 500 hPa (dam, shaded), MSLP (hPa, contour) e vento a 10 metri (knots, barbs)'
            titolo_variabili = 'MSLP (hPa, contour) e vento a 10 metri (knots, barbs, m/s colorbar)'
            ax.set_title(titolo_variabili, loc='left', fontsize=8)
            ax.set_title(t, loc='right', fontsize=8)
            
            plt.savefig(f"{sub_cartella_plot}/{t.strftime('%Y-%m-%d-%H%M%S')}.png", dpi=300, format='png', bbox_inches='tight')
    
            # plt.show()
            plt.close()
        
            # sss

print('\n\nDone.')