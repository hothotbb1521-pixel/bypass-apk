.class public Lcom/stub/loader/StubApplication;
.super Landroid/app/Application;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method

.method public attachBaseContext(Landroid/content/Context;)V
    .registers 3
    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    invoke-direct {p0, p1}, Lcom/stub/loader/StubApplication;->loadPayload(Landroid/content/Context;)V
    return-void
.end method

.method public onCreate()V
    .registers 1
    invoke-super {p0}, Landroid/app/Application;->onCreate()V
    return-void
.end method

.method private loadPayload(Landroid/content/Context;)V
    .registers 16

    # ler k.bin
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "k.bin"
    invoke-virtual {v0, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v2

    const/16 v3, 0x30
    new-array v4, v3, [B
    const/4 v5, 0x0
    invoke-virtual {v2, v4, v5, v3}, Ljava/io/InputStream;->read([BII)I
    invoke-virtual {v2}, Ljava/io/InputStream;->close()V

    # key = bytes[0..31]
    const/4 v5, 0x0
    const/4 v6, 0x20
    invoke-static {v4, v5, v6}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v7

    # iv = bytes[32..47]
    const/4 v5, 0x20
    const/16 v6, 0x30
    invoke-static {v4, v5, v6}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v8

    # ler p.bin
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "p.bin"
    invoke-virtual {v0, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v9

    invoke-static {v9}, Lcom/stub/loader/StubApplication;->readAllBytes(Ljava/io/InputStream;)[B
    move-result-object v10
    invoke-virtual {v9}, Ljava/io/InputStream;->close()V

    # SecretKeySpec
    new-instance v11, Ljavax/crypto/spec/SecretKeySpec;
    const-string v0, "AES"
    invoke-direct {v11, v7, v0}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    # IvParameterSpec
    new-instance v12, Ljavax/crypto/spec/IvParameterSpec;
    invoke-direct {v12, v8}, Ljavax/crypto/spec/IvParameterSpec;-><init>([B)V

    # Cipher
    const-string v0, "AES/CBC/PKCS5Padding"
    invoke-static {v0}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;
    move-result-object v13

    const/4 v0, 0x2
    invoke-virtual {v13, v0, v11, v12}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V
    invoke-virtual {v13, v10}, Ljavax/crypto/Cipher;->doFinal([B)[B
    move-result-object v14

    # ByteBuffer + InMemoryDexClassLoader
    invoke-static {v14}, Ljava/nio/ByteBuffer;->wrap([B)Ljava/nio/ByteBuffer;
    move-result-object v0

    invoke-virtual {p1}, Landroid/content/Context;->getClassLoader()Ljava/lang/ClassLoader;
    move-result-object v1

    new-instance v2, Ldalvik/system/InMemoryDexClassLoader;
    invoke-direct {v2, v0, v1}, Ldalvik/system/InMemoryDexClassLoader;-><init>(Ljava/nio/ByteBuffer;Ljava/lang/ClassLoader;)V

    return-void
.end method

.method private static readAllBytes(Ljava/io/InputStream;)[B
    .registers 5
    new-instance v0, Ljava/io/ByteArrayOutputStream;
    invoke-direct {v0}, Ljava/io/ByteArrayOutputStream;-><init>()V
    const/16 v1, 0x1000
    new-array v2, v1, [B
    :loop
    const/4 v3, 0x0
    invoke-virtual {p0, v2, v3, v1}, Ljava/io/InputStream;->read([BII)I
    move-result v3
    if-ltz v3, :done
    invoke-virtual {v0, v2, v3, v3}, Ljava/io/ByteArrayOutputStream;->write([BII)V
    goto :loop
    :done
    invoke-virtual {v0}, Ljava/io/ByteArrayOutputStream;->toByteArray()[B
    move-result-object v4
    return-object v4
.end method
