from flask import Flask, render_template, request, send_file, redirect, url_for
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

def make_wifi_payload(ssid: str, password: str, auth: str, hidden: bool=False) -> str:
    """
    Format payload sesuai standard: WIFI:T:<WPA|WEP|nopass>;S:<ssid>;P:<password>;H:<true|false>;;
    """
    ssid_escaped = ssid.replace('"', '\\"')
    password_escaped = password.replace('"', '\\"')
    hidden_str = "true" if hidden else "false"
    if auth.lower() == "nopass":
        return f"WIFI:T:nopass;S:{ssid_escaped};;"
    return f"WIFI:T:{auth};S:{ssid_escaped};P:{password_escaped};H:{hidden_str};;"

def generate_qr_image(data: str, box_size: int = 10) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", qr_b64=None, payload=None)

@app.route("/generate", methods=["POST"])
def generate():
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password", "").strip()
    auth = request.form.get("auth", "WPA").upper()
    hidden = bool(request.form.get("hidden", False))

    if not ssid:
        return redirect(url_for("index"))

    payload = make_wifi_payload(ssid, password, auth, hidden)
    img_buf = generate_qr_image(payload)

    b64 = base64.b64encode(img_buf.getvalue()).decode("utf-8")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"wifi_qr_{ssid}_{timestamp}.png"

    # store image bytes in sessionless way: pass via query? simpler: render with b64 and include hidden form to download
    return render_template("index.html", qr_b64=b64, payload=payload, filename=filename)

@app.route("/download", methods=["POST"])
def download():
    # receives payload string and regenerates PNG to send as file
    payload = request.form.get("payload", "")
    if not payload:
        return redirect(url_for("index"))
    img_buf = generate_qr_image(payload)
    # send as attachment
    return send_file(
        img_buf,
        mimetype="image/png",
        as_attachment=True,
        download_name="wifi_qr.png"
    )

if __name__ == "__main__":
    app.run(debug=True)