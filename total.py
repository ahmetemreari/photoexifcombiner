import os
import json
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime
import subprocess
from pathlib import Path

def update_video_metadata(video_path, metadata):
    """
    FFmpeg kullanarak video metadata'sını günceller
    """
    try:
        timestamp = metadata['photoTakenTime']['timestamp']
        date_str = datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Geçici dosya adını .mp4 uzantılı olarak oluştur
        temp_path = os.path.splitext(video_path)[0] + "_temp.mp4"
        
        # FFmpeg komutu oluştur
        command = [
            'ffmpeg',
            '-y',  # Var olan dosyanın üzerine yaz
            '-i', video_path,
            '-metadata', f'creation_time={date_str}',
            '-c', 'copy',  # Codec'i kopyala
            '-movflags', '+faststart',  # Web için optimize et
            temp_path
        ]
        
        # FFmpeg'i çalıştır
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg çıktısı: {result.stderr}")
            raise Exception(f"FFmpeg hatası: {result.stderr}")
        
        # Başarılı olduysa, orijinal dosyayı yedekle
        backup_path = video_path + ".bak"
        os.rename(video_path, backup_path)
        
        try:
            # Geçici dosyayı orijinal isimle taşı
            os.rename(temp_path, video_path)
            # Yedek dosyayı sil
            os.remove(backup_path)
        except Exception as e:
            # Hata durumunda yedeklenen dosyayı geri getir
            os.rename(backup_path, video_path)
            raise e
        
        return True
    except Exception as e:
        print(f"Video metadata güncellenirken hata: {str(e)}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def update_photo_metadata(photo_path, metadata):
    """
    Fotoğraf EXIF bilgilerini günceller
    """
    try:
        # Önce dosyanın var olduğunu kontrol et
        if not os.path.exists(photo_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {photo_path}")

        # Mevcut EXIF verilerini yükle veya yeni oluştur
        try:
            exif_dict = piexif.load(photo_path)
        except:
            exif_dict = {'0th':{}, 'Exif':{}, 'GPS':{}, '1st':{}, 'thumbnail':None}
        
        # Tarihi düzenle
        if 'photoTakenTime' in metadata:
            timestamp = int(metadata['photoTakenTime']['timestamp'])
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_str.encode('utf-8')
            
        # GPS verilerini güncelle
        if 'geoData' in metadata and metadata['geoData']['latitude'] != 0:
            lat = metadata['geoData']['latitude']
            lon = metadata['geoData']['longitude']
            
            lat_deg = int(abs(lat))
            lat_min = int((abs(lat) - lat_deg) * 60)
            lat_sec = int(((abs(lat) - lat_deg) * 60 - lat_min) * 60)
            
            lon_deg = int(abs(lon))
            lon_min = int((abs(lon) - lon_deg) * 60)
            lon_sec = int(((abs(lon) - lon_deg) * 60 - lon_min) * 60)
            
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [(lat_deg, 1), (lat_min, 1), (lat_sec, 1)]
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [(lon_deg, 1), (lon_min, 1), (lon_sec, 1)]
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
        
        # Yeni EXIF verilerini kaydet
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, photo_path)
        
        return True
    except Exception as e:
        print(f"Fotoğraf metadata güncellenirken hata: {str(e)}")
        return False

def sync_media_metadata(folder_path, delete_json=True):
    """
    Klasördeki medya dosyaları ve JSON dosyalarını eşleştirip metadata'yı günceller
    """
    # Klasördeki tüm dosyaları listele
    files = os.listdir(folder_path)
    media_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.mpg', '.mpeg', '.mp4'))]
    json_files = [f for f in files if f.lower().endswith('.json')]
    
    processed_jsons = []
    
    for media_file in media_files:
        # JSON dosyasını bul
        json_name = f"{media_file}.json"
        if json_name not in json_files:
            print(f"UYARI: {media_file} için JSON dosyası bulunamadı")
            continue
            
        # JSON dosyasını oku
        json_path = os.path.join(folder_path, json_name)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"JSON dosyası okuma hatası ({json_name}): {str(e)}")
            continue
            
        # Medya dosyası yolunu oluştur
        media_path = os.path.join(folder_path, media_file)
        
        if not os.path.exists(media_path):
            print(f"UYARI: Medya dosyası bulunamadı: {media_file}")
            continue
            
        success = False
        
        # Dosya tipine göre işlem yap
        if media_file.lower().endswith(('.jpg', '.jpeg')):
            success = update_photo_metadata(media_path, metadata)
        else:  # Video dosyası
            success = update_video_metadata(media_path, metadata)
        
        if success:
            print(f"Başarılı: {media_file} güncellendi")
            processed_jsons.append(json_path)
        else:
            print(f"HATA: {media_file} güncellenemedi")
    
    # İşlem tamamlandıktan sonra JSON dosyalarını sil
    if delete_json:
        for json_path in processed_jsons:
            try:
                os.remove(json_path)
                print(f"JSON dosyası silindi: {os.path.basename(json_path)}")
            except Exception as e:
                print(f"JSON dosyası silinirken hata: {str(e)}")

if __name__ == "__main__":
    # Klasör yolunu belirtin
    folder_path = "."  # Mevcut klasör
    sync_media_metadata(folder_path, delete_json=True)