
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

from metpy.units import units
from metpy.calc import wind_components

font_files = mfont.findSystemFonts(fontpaths='../Helvetica')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)

plt.rc('font', family='Helvetica', weight='normal', size=8)

def f_rot(a):
    """Ruoto in modo opportuno."""
    return np.rot90(a.T, 1)


def f_correzione_NOAA(ds):
    # ds = ds.rename({'lon': 'longitude'})
    # ds = ds.rename({'lat': 'latitude'})
    
    ds['_longitude_180'] = xr.where(ds['lon'] > 180, ds['lon'] - 360, ds['lon'])
    ds = (ds.swap_dims({'lon': '_longitude_180'}).sel(**{'_longitude_180': sorted(ds['_longitude_180'])}).drop_vars('lon'))
    ds = ds.rename({'_longitude_180': 'lon'})
    
    return ds

# %%

cartella_lavoro = '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati'
os.chdir(cartella_lavoro)
cartella_plot = '/home/cfmi.arpal.org/daniele.carnevale/Scrivania/lavoro_mare/dati/plot_singoli_uniti'
os.makedirs(cartella_plot, exist_ok=True)

### Definisco il dizionario delle aree
dict_aree = {
    'Med': [0, 14, 37, 45],
    'Med1': [0, 20, 36, 47],
    'Med1D': [-2, 20, 36, 48],
    'Med2': [5, 18, 36, 45],
    'alps': [3, 16, 40, 50],
    'METEOSAT': [-20, 29.95, 30, 59.95],
    'Europa': [-20, 60, 30, 70],
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

### Parametri

area = 'Med1D'
colore_confini = 'grey'
spessore_confini = 1
spessore_isobare = 0.4
skip_hPa = 1
livelli_msl = np.arange(900, 1050, skip_hPa)
colore_msl = 'black'
###
zorder_vento = 100
lunghezza_barbette = 4.5
spessore_barbette = 0.5
dpi = 300
limite_inferiore_kn = 5
ms2knt = 1.94384

lista_range_tempi = [
    # ['1948-01-26', '1948-01-29'],
    # ['1952-12-16', '1952-12-18'],
    # ['1953-02-09', '1953-02-12'],
    # ['1955-02-17', '1955-02-21'],
    # ['1957-02-17', '1957-02-19'],
    # ['1962-12-14', '1962-12-17'],
    # ['1968-01-06', '1968-01-08'],
    # ['1974-02-05', '1974-02-08'],
    # ['1976-11-30', '1976-12-06'],
    # ['1978-12-30', '1979-01-02'],
    # ['1979-03-15', '1979-03-18'],
    # ['1981-12-06', '1981-12-11'],
    # ['1981-12-13', '1981-12-19'],
    # ['1986-01-22', '1986-01-25'],
    # ['1989-02-24', '1989-03-02'],
    # ['1990-02-12', '1990-02-17'],
    # ['1990-02-25', '1990-03-01'],
    # ['1992-03-22', '1992-03-25'],
    # ['1996-11-18', '1996-11-22'],
    # ['1999-02-07', '1999-02-11'],
    # ['1999-12-24', '1999-12-28'],
    # ['1999-12-26', '1999-12-30'],
    # ['2000-11-05', '2000-11-10'],
    # ['2001-11-07', '2001-11-10'],
    # ['2002-02-19', '2002-02-22'],
    # ['2003-02-02', '2003-02-05'],
    # ['2006-03-02', '2006-03-06'],
    # ['2007-02-28', '2007-03-03'],
    # ['2008-03-20', '2008-03-23'],
    # ['2008-10-28', '2008-11-01'],
    # ['2008-11-28', '2008-12-03'],
    # ['2011-12-14', '2011-12-18'],
    # ['2015-11-19', '2015-11-22'],
    # ['2019-12-20', '2019-12-24'],
    # ['2021-01-21', '2021-01-26'],
    ['2023-11-01', '2023-11-07'],
    ['2024-11-18', '2024-11-24'],
    ['2025-01-26', '2025-01-30']
]

# %%

for range_tempo in lista_range_tempi:
    print(range_tempo)
    
    cartella_ciclone = f"ciclone_{range_tempo[0].split('-')[0]}_{range_tempo[0].split('-')[1]}_{range_tempo[0].split('-')[2]}"
    
    sub_cartella_plot = f'{cartella_plot}/{cartella_ciclone}'
    os.makedirs(sub_cartella_plot, exist_ok=True)
    
    range_giorno = pd.date_range(range_tempo[0], pd.to_datetime(range_tempo[1]) + pd.Timedelta(days=1), freq='1D')
    
    for giorno in range_giorno:

        tempi_completi = pd.date_range(giorno, giorno + pd.Timedelta(days=1), freq='3h')

        ### CERRA
        try:
            ds_cerra = xr.open_dataset(f"{cartella_lavoro}/CERRA_singoli/{cartella_ciclone}/CERRA_{giorno.year}_{giorno.month:02d}_{giorno.day:02d}.nc", engine='netcdf4')
        except FileNotFoundError:
            ds_cerra = xr.open_dataset(f"{cartella_lavoro}/CERRA_singoli/ciclone_1986_01_22/CERRA_1986_01_22.nc", engine='netcdf4')
            
        dict_cerra = {
            'valid_time': pd.to_datetime(ds_cerra['valid_time'].values),
            'latitude': ds_cerra['latitude'].values,
            'longitude': (ds_cerra['longitude'].values + 180) % 360 - 180,
            }
        
        ### ERA5
        try:
            ds_era5 = xr.open_dataset(f"{cartella_lavoro}/ERA5_singoli/{cartella_ciclone}/ERA5_{giorno.year}_{giorno.month:02d}_{giorno.day:02d}.nc", engine='netcdf4')
        except FileNotFoundError:
            ds_era5 = xr.open_dataset(f"{cartella_lavoro}/ERA5_singoli/ciclone_1986_01_22/ERA5_1986_01_22.nc", engine='netcdf4')
            
        dict_era5 = {
            'valid_time': pd.to_datetime(ds_era5['valid_time'].values),
            'latitude': np.meshgrid(ds_era5['longitude'].values, ds_era5['latitude'].values)[1],
            'longitude': np.meshgrid(ds_era5['longitude'].values, ds_era5['latitude'].values)[0],
            }
        
        ### NOAAv2c
        try:
            ds_noaav2c_prmsl = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_prmsl_annuali/prmsl.{giorno.year}.nc", engine='netcdf4'))
            ds_noaav2c_u = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_u-wind_annuali/uwnd.10m.{giorno.year}.nc", engine='netcdf4'))
            ds_noaav2c_v = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_v-wind_annuali/vwnd.10m.{giorno.year}.nc", engine='netcdf4'))
        except FileNotFoundError:
            ds_noaav2c_prmsl = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_prmsl_annuali/prmsl.1986.nc", engine='netcdf4'))
            ds_noaav2c_u = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_u-wind_annuali/uwnd.10m.1986.nc", engine='netcdf4'))
            ds_noaav2c_v = f_correzione_NOAA(xr.open_dataset(f"{cartella_lavoro}/NOAAv2c_v-wind_annuali/vwnd.10m.1986.nc", engine='netcdf4'))
            
        dict_noaav2c = {
            'valid_time_prmsl': pd.to_datetime(ds_noaav2c_prmsl['time'].values),
            'latitude_prmsl': np.meshgrid(ds_noaav2c_prmsl['lon'].values, ds_noaav2c_prmsl['lat'].values)[1],
            'longitude_prmsl': np.meshgrid(ds_noaav2c_prmsl['lon'].values, ds_noaav2c_prmsl['lat'].values)[0],
            #!!! Il vento è ogni 3 ore, mentre la pressione ogni 6, inoltre il passo di griglia non è lo stesso
            'valid_time_uv': pd.to_datetime(ds_noaav2c_u['time'].values),
            'latitude_uv': np.meshgrid(ds_noaav2c_u['lon'].values, ds_noaav2c_u['lat'].values)[1],
            'longitude_uv': np.meshgrid(ds_noaav2c_u['lon'].values, ds_noaav2c_u['lat'].values)[0],
            }
            
        ##############
        ##############
        
        # plt.imshow(dict_noaav2c['longitude_prmsl'])
        # plt.show()
        # plt.close()
        
        ##############
        ##############
        
        ### CERRA
        dict_cerra.update(
            {
                'wind_direction_10m': ds_cerra['wdir10'].values,
                'wind_speed_10m': ds_cerra['si10'].values,
                'nodi_10m': ds_cerra['si10'].values * ms2knt,
                'mean_sea_level_pressure': ds_cerra['msl'].values / 100 # da Pa a hPa
                }
            )
        
        ### ERA5
        dict_era5.update(
            {
                'u_10m': ds_era5['u10'].values,
                'v_10m': ds_era5['v10'].values,
                'mean_sea_level_pressure': ds_era5['msl'].values / 100 # da Pa a hPa
                }
            )
        
        dict_era5.update(
            {
                'wind_speed_10m': np.sqrt(dict_era5['u_10m'] ** 2 + dict_era5['v_10m'] ** 2),
                'nodi_10m': np.sqrt(dict_era5['u_10m'] ** 2 + dict_era5['v_10m'] ** 2) * ms2knt,
                }
            )
        
        ### NOAAv2c
        dict_noaav2c.update(
            {
                'u_10m': ds_noaav2c_u['uwnd'].values,
                'v_10m': ds_noaav2c_v['vwnd'].values,
                'mean_sea_level_pressure': ds_noaav2c_prmsl['prmsl'].values / 100 # da Pa a hPa
                }
            )

        dict_noaav2c.update(
            {
                'wind_speed_10m': np.sqrt(dict_noaav2c['u_10m'] ** 2 + dict_noaav2c['v_10m'] ** 2),
                'nodi_10m': np.sqrt(dict_noaav2c['u_10m'] ** 2 + dict_noaav2c['v_10m'] ** 2) * ms2knt
                }
            )
        
        ##############
        ##############
        
        for tempo in tempi_completi:
            print(tempo)
            
            fig, axs = plt.subplots(3, 1, figsize=(7, 12), subplot_kw={'projection': ccrs.PlateCarree()})
            fig.suptitle(f"{str(tempo)} UTC\nMean sea level pressure [hPa] (interval: {skip_hPa} hPa) & 10 meter wind speed [m/s]", fontsize=9, fontweight='bold', y=0.92)

            for ax in axs.flat:
                ax.set_extent(dict_aree[area])
                ax.add_feature(cf.BORDERS, lw=spessore_confini, edgecolor=colore_confini)
                ax.add_feature(cf.COASTLINE, lw=spessore_confini, edgecolor=colore_confini)
                # ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])
                ax.set_aspect('auto', adjustable=None)

            asse_cerra = axs[0]
            asse_era5 = axs[1]
            asse_noaav2c = axs[2]
            
            nome_png = f"{area}_{str(tempo).replace(' ', '_').replace(':', '-')}.png"
            
            if os.path.exists(f'{sub_cartella_plot}/{nome_png}'):
                print(f'\n{sub_cartella_plot}/{nome_png} esiste. Continuo.\n')
                continue

            try:
                ### CERRA - MSLP
                ind_tempo_cerra = dict_cerra['valid_time'].get_loc(tempo)
                
                plot_mslp_cerra = asse_cerra.contour(
                    dict_cerra['longitude'],
                    dict_cerra['latitude'],
                    dict_cerra['mean_sea_level_pressure'][ind_tempo_cerra, ...],
                    transform=ccrs.PlateCarree(),
                    colors=colore_msl,
                    levels=livelli_msl,
                    linewidths=spessore_isobare,
                )
    
                clabels_cerra = asse_cerra.clabel(plot_mslp_cerra,
                                    colors=colore_msl,
                                    inline_spacing=10,
                                    inline=True,
                                    fontsize=6,
                                    zorder=zorder_vento + 1 # devono essere sempre sopra
                                    )
                
                [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=1)) for txt in clabels_cerra]
                [txt.set_rotation(0) for txt in clabels_cerra]
                
                ### CERRA - VENTO
                knu10_t, knv10_t = wind_components(dict_cerra['nodi_10m'][ind_tempo_cerra, ...] * units('knots'), dict_cerra['wind_direction_10m'][ind_tempo_cerra,...] * units.deg)
                ws10_t = dict_cerra['wind_speed_10m'][ind_tempo_cerra, ...]
                nodi10_t = dict_cerra['nodi_10m'][ind_tempo_cerra, ...]
    
                skip_vento = 8
                mask = nodi10_t[::skip_vento, ::skip_vento] >= limite_inferiore_kn
    
                plot_ws10_cerra = asse_cerra.barbs(
                    dict_cerra['longitude'][::skip_vento, ::skip_vento][mask],
                    dict_cerra['latitude'][::skip_vento, ::skip_vento][mask],
                    knu10_t[::skip_vento, ::skip_vento][mask],
                    knv10_t[::skip_vento, ::skip_vento][mask],
                    ws10_t[::skip_vento, ::skip_vento][mask],
                    length=lunghezza_barbette,
                    linewidth=spessore_barbette,
                    cmap=colorbar_ms,
                    norm=norm,
                    zorder=zorder_vento
                )
            except KeyError:
                pass
            

            try:
                ### ERA5 - MSLP
                ind_tempo_era5 = dict_era5['valid_time'].get_loc(tempo)
                
                plot_mslp_era5 = asse_era5.contour(
                    dict_era5['longitude'],
                    dict_era5['latitude'],
                    dict_era5['mean_sea_level_pressure'][ind_tempo_era5, ...],
                    transform=ccrs.PlateCarree(),
                    colors=colore_msl,
                    levels=livelli_msl,
                    linewidths=spessore_isobare,
                )
    
                clabels_era5 = asse_era5.clabel(plot_mslp_era5,
                                    colors=colore_msl,
                                    inline_spacing=10,
                                    inline=True,
                                    fontsize=6,
                                    zorder=zorder_vento + 1 # devono essere sempre sopra
                                    )
    
                [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=1)) for txt in clabels_era5]
                [txt.set_rotation(0) for txt in clabels_era5]
    
                ### ERA5 - VENTO
                knu10_t, knv10_t = dict_era5['u_10m'][ind_tempo_era5, ...] * ms2knt, dict_era5['v_10m'][ind_tempo_era5, ...] * ms2knt
                ws10_t = dict_era5['wind_speed_10m'][ind_tempo_era5, ...]
                nodi10_t = dict_era5['nodi_10m'][ind_tempo_era5, ...]
    
                skip_vento = 2
                mask = nodi10_t[::skip_vento, ::skip_vento] >= limite_inferiore_kn
    
                plot_ws10_era5 = asse_era5.barbs(
                    dict_era5['longitude'][::skip_vento, ::skip_vento][mask],
                    dict_era5['latitude'][::skip_vento, ::skip_vento][mask],
                    knu10_t[::skip_vento, ::skip_vento][mask],
                    knv10_t[::skip_vento, ::skip_vento][mask],
                    ws10_t[::skip_vento, ::skip_vento][mask],
                    length=lunghezza_barbette,
                    linewidth=spessore_barbette,
                    cmap=colorbar_ms,
                    norm=norm,
                    zorder=zorder_vento
                )
            except KeyError:
                continue #  così perché altrimenti plotta solo NOAA se troppo nel passato
            

            if not tempo.year >= 2015:
                try:
                    ### NOAAv2c - MSLP
                    ind_tempo_noaav2c_prmsl = dict_noaav2c['valid_time_prmsl'].get_loc(tempo)
        
                    plot_mslp_noaav2c = asse_noaav2c.contour(
                        dict_noaav2c['longitude_prmsl'],
                        dict_noaav2c['latitude_prmsl'],
                        dict_noaav2c['mean_sea_level_pressure'][ind_tempo_noaav2c_prmsl, ...],
                        transform=ccrs.PlateCarree(),
                        colors=colore_msl,
                        levels=livelli_msl,
                        linewidths=spessore_isobare,
                    )
        
                    clabels_noaav2c = asse_noaav2c.clabel(plot_mslp_noaav2c,
                                        colors=colore_msl,
                                        manual=[(8, 40), (10, 43), (16, 42), (3, 38), (18, 48)],
                                        inline=True,
                                        fontsize=6,
                                        zorder=zorder_vento + 1 # devono essere sempre sopra
                                        )
                    
                    [txt.set_bbox(dict(facecolor='white', edgecolor='none', pad=1)) for txt in clabels_noaav2c]
                    [txt.set_rotation(0) for txt in clabels_noaav2c]
                
                except KeyError:
                    pass
    
                try:
                    ### NOAAv2c - VENTO
                    ind_tempo_noaav2c_uv = dict_noaav2c['valid_time_uv'].get_loc(tempo)
    
                    knu10_t, knv10_t = dict_noaav2c['u_10m'][ind_tempo_noaav2c_uv, ...] * ms2knt, dict_noaav2c['v_10m'][ind_tempo_noaav2c_uv, ...] * ms2knt
                    ws10_t = dict_noaav2c['wind_speed_10m'][ind_tempo_noaav2c_uv, ...]
                    nodi10_t = dict_noaav2c['nodi_10m'][ind_tempo_noaav2c_uv, ...]
    
                    # skip_vento = 1
                    mask = nodi10_t >= limite_inferiore_kn
                    
                    plot_ws10_noaav2c = asse_noaav2c.barbs(
                        dict_noaav2c['longitude_uv'][mask],
                        dict_noaav2c['latitude_uv'][mask],
                        knu10_t[mask],
                        knv10_t[mask],
                        ws10_t[mask],
                        length=lunghezza_barbette,
                        linewidth=spessore_barbette,
                        cmap=colorbar_ms,
                        norm=norm,
                        zorder=zorder_vento
                    )
                    
                except KeyError:
                    pass
            
            asse_cerra.set_title("CERRA", fontsize=8, loc='left')
            asse_era5.set_title("ERA5", fontsize=8, loc='left')
            asse_noaav2c.set_title("NOAAv2c", fontsize=8, loc='left')
            
            try:
                cbar = fig.colorbar(plot_ws10_noaav2c, ax=axs, extend='both',  spacing='uniform', drawedges=True, location='bottom', pad=0.03, shrink=0.6, fraction=0.05)
            except NameError:
                cbar = fig.colorbar(plot_ws10_cerra, ax=axs, extend='both',  spacing='uniform', drawedges=True, location='bottom', pad=0.03, shrink=0.6, fraction=0.05)
                
            cbar.set_label('m/s', fontsize=10)
            cbar.ax.tick_params(axis='y', which='both', length=0)
            
            plt.savefig(f"{sub_cartella_plot}/{nome_png}", dpi=dpi, format='png', bbox_inches='tight')
            
            # plt.show()
            plt.close()

print("\n\nDone")
