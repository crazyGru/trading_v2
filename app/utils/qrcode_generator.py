import qrcode
from io import BytesIO
from fastapi import HTTPException
import base64  # Add this import

def generate_qr_code() -> str:
    try:
        img_io = BytesIO()
        with open('qr.png', 'rb') as f:
            img_io.write(f.read())
        img_io.seek(0)
        return img_io.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating QR code")