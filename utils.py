import os
import secrets
from PIL import Image
from flask import current_app

def save_picture(form_picture, folder_name='post_pics', output_size=(800, 800)):
    """
    ინახავს სურათს:
    1. ქმნის უნიკალურ სახელს (Random Hex).
    2. იღებს ფაილის გაფართოებას.
    3. პატარა ზომაზე "კუმშავს" სურათს (Pillow-ს გამოყენებით).
    4. ინახავს მითითებულ საქაღალდეში.
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', folder_name, picture_fn)

    # Image Resizing (Pillow)
    i = Image.open(form_picture)
    i.thumbnail(output_size) # ინარჩუნებს პროპორციებს
    i.save(picture_path)

    return picture_fn

def time_ago(date_obj):
    """
    gamosadegari funqcia: აბრუნებს დროს ადამიანურ ენაზე.
    მაგ: '5 წუთის წინ', '2 საათის წინ', 'გუშინ'.
    """
    from datetime import datetime
    now = datetime.utcnow()
    diff = now - date_obj

    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)

    if seconds < 60:
        return "ახლახანს"
    elif minutes < 60:
        return f"{minutes} წუთის წინ"
    elif hours < 24:
        return f"{hours} საათის წინ"
    elif days == 1:
        return "გუშინ"
    else:
        return f"{days} დღის წინ"