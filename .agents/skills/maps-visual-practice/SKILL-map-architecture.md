# SKILL: Pure Front-End Map Architecture

## 1. Konteks dan Tujuan
Modul ini mendefinisikan standar (best practices) untuk membangun aplikasi web pemetaan geografis murni di sisi front-end. Sistem ini tidak memerlukan framework backend, database, atau proses rendering di sisi server (SSR). Semua transformasi data dari bentuk mentah dilakukan secara offline, diubah menjadi `GeoJSON`, dan dirender secara dinamis di browser klien.

## 2. Prinsip Desain UI/UX
*   **Estetika Visual:** Terapkan gaya 2D minimalis yang bersih dan modern.
*   **Palet Warna:** Gunakan skema warna *earth-tones* (nuansa bumi seperti hijau zaitun, cokelat pasir, krem) untuk mempertahankan tampilan yang profesional dan membumi.
*   **Komposisi:** Hindari penggunaan efek 3D atau *drop-shadow* yang berlebihan. Gunakan garis batas yang tegas dan *flat design*. Fokuskan antarmuka pada area peta, dengan panel informasi yang mengambang (floating) secara subtil.

## 3. Struktur Direktori Standar
Pastikan proyek mematuhi struktur modular berikut untuk pemisahan *concern* yang jelas:
```text
/public
  ├── /data
  │   └── regional-data.geojson  # File sumber utama
/src
  ├── /components
  │   └── MapViewer.js           # Logika rendering Leaflet
  ├── /services
  │   └── GeoJsonService.js      # Logika fetch/pengambilan data
  ├── /utils
  │   └── MapHelpers.js          # Fungsi utilitas (format warna, dll)
  └── main.js                    # Entry point aplikasi
index.html
style.css