import os, uuid, shutil
from flask import Flask, request, send_file, jsonify, render_template
from packer import repack

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "*"
    return r

JOBS = "/tmp/bypass_jobs"
os.makedirs(JOBS, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pack", methods=["POST","OPTIONS"])
def pack():
    if request.method == "OPTIONS": return "",204
    job = os.path.join(JOBS, str(uuid.uuid4()))
    os.makedirs(job)
    inp = os.path.join(job,"input.apk")
    out = os.path.join(job,"output.apk")
    try:
        request.files["apk"].save(inp)
        app_name = request.form.get("app_name","").strip() or None
        visual   = request.form.get("visual","playstore")
        icon_path = None
        if "icon" in request.files and request.files["icon"].filename:
            icon_path = os.path.join(job,"icon.png")
            request.files["icon"].save(icon_path)
        repack(inp, out, app_name=app_name, icon_path=icon_path, visual=visual)
        return send_file(out, as_attachment=True,
                         download_name="bypass_packed.apk",
                         mimetype="application/vnd.android.package-archive")
    except Exception as e:
        return jsonify({"error":str(e)}),500
    finally:
        shutil.rmtree(job, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
