import os
import json
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime

def sync_photo_metadata(folder_path):
    """
    Klasördeki JPG ve JSON dosyalarını eşleştirip EXIF bilgilerini günceller
    """
    # Klasördeki tüm dosyaları listele
    files = os.listdir(folder_path)
    jpg_files = [f for f in files if f.lower().endswith('.jpg')]
    json_files = [f for f in files if f.lower().endswith('.json')]
    
    for jpg_file in jpg_files:
        # JSON dosyasını bul
        json_name = jpg_file + '.json'
        if json_name not in json_files:
            print(f"UYARI: {jpg_file} için JSON dosyası bulunamadı")
            continue
            
        # JSON dosyasını oku
        with open(os.path.join(folder_path, json_name), 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        # Fotoğraf dosyası yolunu oluştur
        photo_path = os.path.join(folder_path, jpg_file)
        
        try:
            # Mevcut EXIF verilerini al
            exif_dict = piexif.load(photo_path)
            
            # Tarihi düzenle
            if 'photoTakenTime' in metadata:
                timestamp = int(metadata['photoTakenTime']['timestamp'])
                date_str = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d %H:%M:%S")
                
                # DateTimeOriginal güncelle
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_str.encode('utf-8')
                
            # GPS verilerini güncelle
            if 'geoData' in metadata and metadata['geoData']['latitude'] != 0:
                lat = metadata['geoData']['latitude']
                lon = metadata['geoData']['longitude']
                
                # GPS bilgilerini dönüştür
                lat_deg = int(abs(lat))
                lat_min = int((abs(lat) - lat_deg) * 60)
                lat_sec = int(((abs(lat) - lat_deg) * 60 - lat_min) * 60)
                
                lon_deg = int(abs(lon))
                lon_min = int((abs(lon) - lon_deg) * 60)
                lon_sec = int(((abs(lon) - lon_deg) * 60 - lon_min) * 60)
                
                # GPS verilerini EXIF formatına dönüştür
                exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [(lat_deg, 1), (lat_min, 1), (lat_sec, 1)]
                exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [(lon_deg, 1), (lon_min, 1), (lon_sec, 1)]
                exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
                exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
            
            # Yeni EXIF verilerini kaydet
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, photo_path)
            
            print(f"Başarılı: {jpg_file} güncellendi")
            
        except Exception as e:
            print(f"HATA: {jpg_file} güncellenirken hata oluştu: {str(e)}")

if __name__ == "__main__":
    # Klasör yolunu belirtin
    folder_path = "."  # Mevcut klasör
    sync_photo_metadata(folder_path)