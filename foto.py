import os
import json
import piexif
from PIL import Image

# Fotoğraflar ve JSON dosyalarının bulunduğu klasör
input_folder = "foto_klasoru"  # Değiştirin

# Tüm dosyaları döngüye al
for file_name in os.listdir(input_folder):
    if file_name.lower().endswith(".jpg"):
        jpg_path = os.path.join(input_folder, file_name)
        json_path = os.path.join(input_folder, file_name.replace(".jpg", ".json"))

        # JSON dosyası varsa işlem yap
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as json_file:
                exif_data = json.load(json_file)

            # EXIF verilerini dönüştür
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}
            for key, value in exif_data.items():
                try:
                    tag = piexif.ExifIFD.__dict__.get(key, None)
                    if tag:
                        exif_dict["Exif"][tag] = value
                except Exception as e:
                    print(f"EXIF için hata: {key} - {e}")

            # Görüntüye EXIF ekle
            exif_bytes = piexif.dump(exif_dict)
            img = Image.open(jpg_path)
            img.save(jpg_path, exif=exif_bytes)

            print(f"{file_name} - EXIF bilgileri başarıyla eklendi.")
        else:
            print(f"{file_name} için JSON dosyası bulunamadı.")
