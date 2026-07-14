from PIL import Image
import sys

img_path = r'C:\Users\l26m1\.gemini\antigravity\brain\b45ee3c2-a887-420d-a7fe-5b57ebf8546f\media__1783988445527.png'
out_path = r'd:\document\huystp\img\reaper_pixel.png'

try:
    img = Image.open(img_path).convert('RGBA')
    datas = img.getdata()
    new_data = []
    for item in datas:
        # Transparent for white-ish pixels
        if item[0] > 230 and item[1] > 230 and item[2] > 230:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    # Crop to bounding box to remove excess transparency
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.save(out_path)
    print('Saved transparent pixel reaper to', out_path)
except Exception as e:
    print('Error:', e)
