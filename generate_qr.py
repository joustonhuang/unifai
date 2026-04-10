#!/usr/bin/env python3
"""Generate a QR code image for a given URL."""

import qrcode
import sys


def generate_qr(url: str, output_path: str = "qr_code.png") -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    print(f"QR code saved to: {output_path}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://velodash.page.link/pVvJ"
    output = sys.argv[2] if len(sys.argv) > 2 else "qr_code.png"
    generate_qr(url, output)
