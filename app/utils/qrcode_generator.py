import qrcode
from io import BytesIO
from fastapi import HTTPException
import base64  # Add this import

def generate_qr_code(data: str) -> str:
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img.save('aaa.png')
        img_io.seek(0)
        
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        return img_base64
        # return img_io
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating QR code")