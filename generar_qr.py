import qrcode

def generar_qr(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"✅ QR generado: {filename}")

# Puedes cambiar el contenido del código QR aquí
generar_qr("codigo_qr_1", "codigo_qr_1.png")
