from flask import Flask, request, send_file, render_template
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image
import io
import os
import logging

app = Flask(__name__, template_folder='templates')

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Store dynamic URLs
dynamic_urls = {}

@app.route('/')
def index():
    app.logger.debug('Rendering index.html')
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_qr():
    app.logger.debug('Received request to generate QR code')
    data = request.form.get('data')
    if not data:
        app.logger.error('No data provided')
        return "Error: No data provided", 400

    color = request.form.get('color', '#000000').lstrip('#')
    bg_color = request.form.get('bg_color', '#ffffff').lstrip('#')
    logo = request.files.get('logo')
    size = int(request.form.get('size', 10))

    color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    bg_color = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))

    qr_id = len(dynamic_urls) + 1
    dynamic_urls[qr_id] = data

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(back_color=bg_color, front_color=color)
    )

    if logo:
        try:
            logo_img = Image.open(logo)
        except IOError:
            app.logger.error('Uploaded file is not a valid image')
            return "Error: Uploaded file is not a valid image", 400

        logo_size = 50
        logo_img = logo_img.resize((logo_size, logo_size))
        pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
        img.paste(logo_img, pos, logo_img)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    app.logger.debug('QR code generated successfully')
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    # Ensure the templates folder exists
    templates_path = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_path):
        os.makedirs(templates_path)
    # Ensure index.html exists in the templates folder
    index_path = os.path.join(templates_path, 'index.html')
    if not os.path.exists(index_path):
        with open(index_path, 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Dynamic QR Code Generator</title>
  </head>
  <body>
    <h1>Generate Dynamic QR Code</h1>
    <form action="/generate" method="post" enctype="multipart/form-data">
      <label for="data">Enter URL or Data:</label>
      <input type="text" id="data" name="data" required><br><br>
      <label for="color">QR Code Color:</label>
      <input type="color" id="color" name="color" value="#000000"><br><br>
      <label for="bg_color">Background Color:</label>
      <input type="color" id="bg_color" name="bg_color" value="#ffffff"><br><br>
      <label for="logo">Upload Logo (optional):</label>
      <input type="file" id="logo" name="logo" accept="image/*"><br><br>
      <label for="size">QR Code Size:</label>
      <input type="number" id="size" name="size" value="10" min="1" max="40"><br><br>
      <button type="submit">Generate QR Code</button>
    </form>
  </body>
</html>''')
    app.logger.debug('Starting Flask app')
    app.run(debug=True, host='0.0.0.0', port=5000)