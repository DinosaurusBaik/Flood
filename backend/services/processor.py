import os
import xarray as xr
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def auto_scan_data():
    """Membuka koneksi ke folder data luar."""
    data_folder = r"D:\debitsumbar"
    print(f"--- Memulai Scanning di: {data_folder} ---")
    
    if not os.path.exists(data_folder):
        print(f"Gagal: Folder '{data_folder}' tidak ditemukan.")
        return None

    # Mengambil file CHRTOUT untuk data streamflow
    all_files = [f for f in os.listdir(data_folder) if 'CHRTOUT' in f]
    if not all_files:
        print("Gagal: Tidak ditemukan file CHRTOUT.")
        return None

    print(f"Berhasil menemukan {len(all_files)} file.")
    
    # Tips: Kita ambil file ke-10 atau tengah agar model sudah 'panas' dan ada isinya
    index_file = 10 if len(all_files) > 10 else 0
    sample_file = all_files[index_file]
    full_path = os.path.join(data_folder, sample_file)
    
    try:
        ds = xr.open_dataset(full_path)
        print(f"[ STATUS: KONEKSI BERHASIL! ] -> Membaca: {sample_file}")
        return ds
    except Exception as e:
        print(f"Error saat membuka dataset: {e}")
        return None

def process_to_geojson(ds):
    """Mengubah dataset NetCDF menjadi file GeoJSON yang ringan."""
    if ds is None:
        return

    print("\n--- Memulai Ekstraksi Data Spasial ---")
    
    try:
        # 1. Konversi Dataset ke DataFrame
        df = ds.to_dataframe().reset_index()
        
        # 2. Standarisasi nama kolom koordinat
        if 'latitude' in df.columns:
            lat_col, lon_col = 'latitude', 'longitude'
        elif 'lat' in df.columns:
            lat_col, lon_col = 'lat', 'lon'
        else:
            lat_col = [c for c in df.columns if 'lat' in c.lower()][0]
            lon_col = [c for c in df.columns if 'lon' in c.lower()][0]

        # 3. Filter Data (UPDATE: Mengambil semua titik sungai agar tidak 0)
        if 'streamflow' in df.columns:
            # Kita ambil semua titik yang didefinisikan sebagai sungai (debit >= 0)
            df_filtered = df[df['streamflow'] >= 0].copy()
            print(f"Berhasil mengambil {len(df_filtered)} titik jaringan sungai.")
        else:
            print("Peringatan: Kolom 'streamflow' tidak ditemukan.")
            df_filtered = df.copy()

        # 4. Buat Geometri Titik
        geometry = [Point(xy) for xy in zip(df_filtered[lon_col], df_filtered[lat_col])]
        gdf = gpd.GeoDataFrame(df_filtered, geometry=geometry)
        gdf.set_crs(epsg=4326, inplace=True)

        # 5. Simpan ke folder project PPMI
        output_dir = r"D:\PPMI FITB 2026\data"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "preview_sumbar.json")
        
        # Simpan kolom penting saja
        columns_to_keep = ['streamflow', 'geometry'] if 'streamflow' in df.columns else ['geometry']
        
        # Opsional: Jika data terlalu banyak (misal > 50rb titik), kita ambil sampel setiap 5 titik
        # agar frontend tidak lag
        if len(gdf) > 10000:
            gdf = gdf.iloc[::5]
            print("Data terlalu padat, melakukan downsampling (ambil setiap 5 titik).")

        gdf[columns_to_keep].to_file(output_path, driver='GeoJSON')
        
        print(f"--- SELESAI! ---")
        print(f"File GeoJSON tersimpan di: {output_path}")

    except Exception as e:
        print(f"Gagal memproses data: {e}")

if __name__ == "__main__":
    dataset = auto_scan_data()
    if dataset:
        process_to_geojson(dataset)