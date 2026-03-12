
import os

import numpy as np
import pandas as pd
import xarray as xr

import cartopy.crs as ccrs
import cartopy.feature as cfeature

import matplotlib.pyplot as plt
import matplotlib.font_manager as mfont

lista_possibili_cartelle_lavoro = [
    '/media/daniele/Daniele2TB/test/dati_Sasha',
    '/run/media/daniele.carnevale/Daniele2TB/test/dati_Sasha',
]

cartella_lavoro = [x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)

font_files = mfont.findSystemFonts(fontpaths='./font/Helvetica')
for font_file in font_files:
    mfont.fontManager.addfont(font_file)
del (font_files)

plt.rc('font', family='Helvetica', weight='normal', size=8)

"""
HO RISOLTO!

Per vedere il confronto runna tutto lo script.
- Il problema principale erano le latitudini del NOAA sottosopra rispetto a quelle di ERA5.
- Poi i valori più grandi del gradiente del NOAA sono dovuti (credo) alla più bassa risoluzione,
perché le distanze ij o lonlat sono più grandi.

"""

# %%

def f_correzione_NOAA(ds):
    ds = ds.rename({'lon': 'longitude'})
    ds = ds.rename({'lat': 'latitude'})
    
    ds['_longitude_180'] = xr.where(ds['longitude'] > 180, ds['longitude'] - 360, ds['longitude'])
    ds = (ds.swap_dims({'longitude': '_longitude_180'}).sel(**{'_longitude_180': sorted(ds['_longitude_180'])}).drop_vars('longitude'))
    ds = ds.rename({'_longitude_180': 'longitude'})
    
    return ds


era5 = xr.open_dataset(f'{cartella_lavoro}/ERA5_annuali/ERA5_1989.nc', engine='netcdf4')
cerra = xr.open_dataset(f'{cartella_lavoro}/CERRA_annuali/CERRA_1989.nc', engine='netcdf4')
noaa = f_correzione_NOAA(xr.open_dataset(f'{cartella_lavoro}/NOAA_annuali/prmsl.1989.nc', engine='netcdf4'))

### Metadati
df_attrs_era5 = pd.DataFrame.from_dict(era5['msl'].attrs, orient='index')
df_attrs_cerra = pd.DataFrame.from_dict(cerra['msl'].attrs, orient='index')
df_attrs_noaa = pd.DataFrame.from_dict(noaa['prmsl'].attrs, orient='index')

### Coordinate
lon_era5_2D, lat_era5_2D = np.meshgrid(era5['longitude'].values, era5['latitude'].values)
lon_cerra_2D, lat_cerra_2D = cerra['longitude'].values, cerra['latitude'].values
lon_noaa_2D, lat_noaa_2D = np.meshgrid(noaa['longitude'].values, noaa['latitude'].values)

fig, axs = plt.subplots(2, 3, figsize=(12, 8))

axs[0,0].imshow(lon_era5_2D)
axs[0,1].imshow(lon_cerra_2D)
axs[0,2].imshow(lon_noaa_2D)

axs[1,0].imshow(lat_era5_2D)
axs[1,1].imshow(lat_cerra_2D)
axs[1,2].imshow(lat_noaa_2D)

axs[0,0].set_title(f'lon era5 - min: {lon_era5_2D.min()}, max: {lon_era5_2D.max()}')
axs[0,1].set_title(f'lon cerra - min: {lon_cerra_2D.min().round(2)}, max: {lon_cerra_2D.max().round(2)}')
axs[0,2].set_title(f'lon noaa - min: {lon_noaa_2D.min()}, max: {lon_noaa_2D.max()}')

axs[1,0].set_title(f'lat era5 - min: {lat_era5_2D.min()}, max: {lat_era5_2D.max()}')
axs[1,1].set_title(f'lat cerra - min: {lat_cerra_2D.min().round(2)}, max: {lat_cerra_2D.max().round(2)}')
axs[1,2].set_title(f'lat noaa - min: {lat_noaa_2D.min()}, max: {lat_noaa_2D.max()}')

for ax in axs.flat:
    ax.set_aspect('auto', adjustable=None)

plt.show()
plt.close()
del (fig, ax, axs)

### Gradienti
t = pd.Timestamp('1989-02-26 00:00:00')
ind_t = list(pd.to_datetime(era5['valid_time'].values)).index(t) ### È lo stesso se uso noaa, era5 o cerra

### Seleziono prima perché il gradiente del cerra non posso farlo tutto insieme
era5 = era5.sel(valid_time=t)
cerra = cerra.sel(valid_time=t)
noaa = noaa.sel(time=t)

# %%

grad_era5_x, grad_era5_y = np.gradient(era5['msl'], axis=(list(era5.dims).index('longitude'), list(era5.dims).index('latitude')))
grad_era5_mod = np.sqrt(grad_era5_x.round(2) ** 2 + grad_era5_y.round(2) ** 2).round(2)

# # # # #
# # # # #

### Metodo 1
# grad_noaa_x, grad_noaa_y = np.gradient(noaa['prmsl'], axis=(list(noaa.dims).index('lon'), list(noaa.dims).index('lat')))

### Metodo 2
# grad_noaa_x, grad_noaa_y = metpy_gradient(noaa['prmsl'], axes=('lon', 'lat')) ### È troppo pesante e crasha

### Metodo 3
grad_noaa_x, grad_noaa_y = noaa['prmsl'].differentiate(coord='longitude').values, noaa['prmsl'].differentiate(coord='latitude').values
grad_noaa_y = - grad_noaa_y # !!! Me lo spiego solo perché le latitudini sono sottosopra rispetto a ERA5
grad_noaa_mod = np.sqrt(grad_noaa_x.round(2) ** 2 + grad_noaa_y.round(2) ** 2).round(2)

# # # # #
# # # # #
# !!! Tutti i grad_y potrebbero non essere corretti perché diminuiscono all'aumentare di y, e invece dovrebbe essere
# il contrario. La x va bene. Se perà metto un meno gi grad_y, le freccine nel modulo cambiano di segno...
# Per ora sembra tornare tutto, poi magari verifico.

### Metodo 3
grad_cerra_x, grad_cerra_y = np.gradient(cerra['msl'], axis=(list(cerra.dims).index('x'), list(cerra.dims).index('y')))
# grad_cerra_x = - grad_cerra_x
grad_cerra_y = - grad_cerra_y
grad_cerra_mod = np.sqrt(grad_cerra_x.round(2) ** 2 + grad_cerra_y.round(2) ** 2).round(2)

##################
##################

livelli_grad_era5_xy = np.linspace(-100, 100, 10)
livelli_grad_cerra_xy = np.linspace(-50, 50, 10)
livelli_grad_noaa_xy = np.linspace(-300, 300, 10)

livelli_grad_era5_mod = np.arange(0, 100+10, 10)
livelli_grad_cerra_mod = np.arange(0, 25+5, 5)
livelli_grad_noaa_mod = np.arange(0, 400+40, 40)

##################
##################

fig, axs = plt.subplots(3, 3, figsize=(12, 9), subplot_kw={'projection': ccrs.PlateCarree()})
fig.suptitle(str(t), fontsize=10, fontweight='bold', y=0.92)

for ax in axs.flat:
    ax.set_extent((-10, 20, 34, 55 - 1))
    ax.add_feature(cfeature.BORDERS, lw=0.3)
    ax.add_feature(cfeature.COASTLINE, lw=0.3)
    # ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])
    ax.set_aspect('auto', adjustable=None)
        
axs[0,0].set_title('grad_era5_x')
axs[0,1].set_title('grad_era5_y')
axs[0,2].set_title('grad_era5_mod')

axs[1,0].set_title('grad_cerra_x')
axs[1,1].set_title('grad_cerra_y')
axs[1,2].set_title('grad_cerra_mod')

axs[2,0].set_title('grad_noaa_x')
axs[2,1].set_title('grad_noaa_y')
axs[2,2].set_title('grad_noaa_mod')


def f_plot_grad(grad, i, j, lon, lat, livelli):
    plot_grad = axs[i,j].contourf(
            lon,
            lat,
            grad,
            levels=livelli,
            extend='both',
            transform=ccrs.PlateCarree()
            )
    
    return plot_grad


plot_grad_era5_x = f_plot_grad(grad_era5_x, 0, 0, lon_era5_2D, lat_era5_2D, livelli_grad_era5_xy)
plot_grad_era5_y = f_plot_grad(grad_era5_y, 0, 1, lon_era5_2D, lat_era5_2D, livelli_grad_era5_xy)
plot_grad_era5_mod = f_plot_grad(grad_era5_mod, 0, 2, lon_era5_2D, lat_era5_2D, livelli_grad_era5_mod)

plot_grad_cerra_x = f_plot_grad(grad_cerra_x, 1, 0, lon_cerra_2D, lat_cerra_2D, livelli_grad_cerra_xy)
plot_grad_cerra_y = f_plot_grad(grad_cerra_y, 1, 1, lon_cerra_2D, lat_cerra_2D, livelli_grad_cerra_xy)
plot_grad_cerra_mod = f_plot_grad(grad_cerra_mod, 1, 2, lon_cerra_2D, lat_cerra_2D, livelli_grad_cerra_mod)

plot_grad_noaa_x = f_plot_grad(grad_noaa_x, 2, 0, lon_noaa_2D, lat_noaa_2D, livelli_grad_noaa_xy)
plot_grad_noaa_y = f_plot_grad(grad_noaa_y, 2, 1, lon_noaa_2D, lat_noaa_2D, livelli_grad_noaa_xy)
plot_grad_noaa_mod = f_plot_grad(grad_noaa_mod, 2, 2, lon_noaa_2D, lat_noaa_2D, livelli_grad_noaa_mod)

### Non le uso più da quando le palette xy e mod devono essere diverse
# fig.colorbar(plot_grad_era5_x, ax=axs[0, :], location='right', fraction=0.05, pad=0.02)
# fig.colorbar(plot_grad_cerra_x, ax=axs[1, :], location='right', fraction=0.05, pad=0.02)
# fig.colorbar(plot_grad_noaa_x, ax=axs[2, :], location='right', fraction=0.05, pad=0.02)


def f_plot_count(ds, ind_t, i, j, lon, lat):
    
    count = axs[i,j].contour(
        lon,
        lat,
        ds / 100,
        levels=20,
        colors='black',
        linewidths=0.8,
        transform=ccrs.PlateCarree()
        )
    
    axs[i,j].clabel(
        count,
        inline=True,
        fmt=' {:.0f}'.format,
        fontsize=6
        )


f_plot_count(era5['msl'], ind_t, 0, 0, lon_era5_2D, lat_era5_2D)
f_plot_count(era5['msl'], ind_t, 0, 1, lon_era5_2D, lat_era5_2D)
f_plot_count(era5['msl'], ind_t, 0, 2, lon_era5_2D, lat_era5_2D)

f_plot_count(cerra['msl'], ind_t, 1, 0, lon_cerra_2D, lat_cerra_2D)
f_plot_count(cerra['msl'], ind_t, 1, 1, lon_cerra_2D, lat_cerra_2D)
f_plot_count(cerra['msl'], ind_t, 1, 2, lon_cerra_2D, lat_cerra_2D)

f_plot_count(noaa['prmsl'], ind_t, 2, 0, lon_noaa_2D, lat_noaa_2D)
f_plot_count(noaa['prmsl'], ind_t, 2, 1, lon_noaa_2D, lat_noaa_2D)
f_plot_count(noaa['prmsl'], ind_t, 2, 2, lon_noaa_2D, lat_noaa_2D)


def f_plot_frecce(campo_x, campo_y, i, j, ind_t, lon, lat, skip, scala):
    axs[i,j].quiver(
        lon[::skip, ::skip],
        lat[::skip, ::skip],
        campo_x[::skip, ::skip],
        campo_y[::skip, ::skip],
        transform=ccrs.PlateCarree(),
        scale=scala,
        pivot='tail'
    )


f_plot_frecce(grad_era5_x, grad_era5_y, 0, 2, ind_t, lon_era5_2D, lat_era5_2D, 3, 5_000)
f_plot_frecce(grad_cerra_x, grad_cerra_y, 1, 2, ind_t, lon_cerra_2D, lat_cerra_2D, 12, 1_000)
f_plot_frecce(grad_noaa_x, grad_noaa_y, 2, 2, ind_t, lon_noaa_2D, lat_noaa_2D, 1, 11_000)

fig.subplots_adjust(
    hspace=0.15,  # Vertical spacing
    wspace=0.05,  # Horizontal spacing
    right=0.85   # Space for colorbars
)

plt.savefig(f"{cartella_lavoro}/test_calcolo_gradiente_1.png", dpi=300, format='png', bbox_inches='tight')
plt.show()
plt.close()

##################
##################
# %%
fig, axs = plt.subplots(1, 3, figsize=(12, 4), subplot_kw={'projection': ccrs.PlateCarree()})
fig.suptitle(str(t), fontsize=10, fontweight='bold', y=0.97)

for ax in axs.flat:
    ax.set_extent((-10, 20, 34, 55 - 1))
    ax.add_feature(cfeature.BORDERS, lw=0.4)
    ax.add_feature(cfeature.COASTLINE, lw=0.4)
    # ax.gridlines(lw=0.2, draw_labels=['left', 'bottom'])
    ax.set_aspect('auto', adjustable=None)
    
for nome, i, lon, lat, grad, liv, ds, skip, campo_x, campo_y, scala in zip(
        ['cerra', 'era5', 'noaa'],
        [0, 1, 2],
        [lon_cerra_2D, lon_era5_2D, lon_noaa_2D],
        [lat_cerra_2D, lat_era5_2D, lat_noaa_2D],
        [grad_cerra_mod, grad_era5_mod, grad_noaa_mod],
        [livelli_grad_cerra_mod, livelli_grad_era5_mod, livelli_grad_noaa_mod],
        [cerra['msl'], era5['msl'], noaa['prmsl']],
        [12, 3, 1],
        [grad_cerra_x, grad_era5_x, grad_noaa_x],
        [grad_cerra_y, grad_era5_y, grad_noaa_y],
        [1000, 5000, 11000]
        ):
    
    axs[i].set_title(f'grad_{nome}')

    plot_grad = axs[i].contourf(
            lon,
            lat,
            grad,
            levels=liv,
            extend='max',
            transform=ccrs.PlateCarree()
            )

    count = axs[i].contour(
        lon,
        lat,
        ds / 100,
        levels=20,
        colors='black',
        linewidths=0.8,
        transform=ccrs.PlateCarree()
        )
    
    axs[i].clabel(
        count,
        inline=True,
        fmt=' {:.0f}'.format,
        fontsize=6
        )
    
    axs[i].quiver(
        lon[::skip, ::skip],
        lat[::skip, ::skip],
        campo_x[::skip, ::skip],
        campo_y[::skip, ::skip],
        transform=ccrs.PlateCarree(),
        scale=scala,
        pivot='tail'
    )
    
    cbar = plt.colorbar(plot_grad, location='bottom', pad=0.05)

plt.savefig(f"{cartella_lavoro}/test_calcolo_gradiente_2.png", dpi=300, format='png', bbox_inches='tight')
plt.show()
plt.close()

print('\n\nDone.')
