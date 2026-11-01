.class public Lcom/stub/loader/StubApplication;
.super Landroid/app/Application;

.field private dexLoader:Ldalvik/system/InMemoryDexClassLoader;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method

.method protected attachBaseContext(Landroid/content/Context;)V
    .registers 3
    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    :try_start_0
    invoke-direct {p0, p1}, Lcom/stub/loader/StubApplication;->loadPayload(Landroid/content/Context;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    goto :goto_0
    :catch_0
    move-exception v0
    invoke-virtual {v0}, Ljava/lang/Exception;->printStackTrace()V
    :goto_0
    return-void
.end method

.method public onCreate()V
    .registers 1
    invoke-super {p0}, Landroid/app/Application;->onCreate()V
    return-void
.end method

.method private loadPayload(Landroid/content/Context;)V
    .registers 16

    # --- ler k.bin (key 32 bytes + iv 16 bytes = 48 bytes) ---
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "k.bin"
    invoke-virtual {v0, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v2

    const/16 v3, 0x30
    new-array v3, v3, [B
    const/4 v14, 0x0
    const/16 v15, 0x30
    invoke-virtual {v2, v3, v14, v15}, Ljava/io/InputStream;->read([BII)I
    invoke-virtual {v2}, Ljava/io/InputStream;->close()V

    # key = kb[0..32)
    const/4 v14, 0x0
    const/16 v15, 0x20
    invoke-static {v3, v14, v15}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v4

    # iv = kb[32..48)
    const/16 v14, 0x20
    const/16 v15, 0x30
    invoke-static {v3, v14, v15}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v5

    # --- ler p.bin (dex criptografado) ---
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "p.bin"
    invoke-virtual {v0, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v6

    invoke-static {v6}, Lcom/stub/loader/StubApplication;->readAll(Ljava/io/InputStream;)[B
    move-result-object v7
    invoke-virtual {v6}, Ljava/io/InputStream;->close()V

    # --- AES/CBC decrypt ---
    new-instance v8, Ljavax/crypto/spec/SecretKeySpec;
    const-string v0, "AES"
    invoke-direct {v8, v4, v0}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    new-instance v9, Ljavax/crypto/spec/IvParameterSpec;
    invoke-direct {v9, v5}, Ljavax/crypto/spec/IvParameterSpec;-><init>([B)V

    const-string v0, "AES/CBC/PKCS5Padding"
    invoke-static {v0}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;
    move-result-object v10

    const/4 v0, 0x2
    invoke-virtual {v10, v0, v8, v9}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    invoke-virtual {v10, v7}, Ljavax/crypto/Cipher;->doFinal([B)[B
    move-result-object v11

    # --- InMemoryDexClassLoader ---
    invoke-static {v11}, Ljava/nio/ByteBuffer;->wrap([B)Ljava/nio/ByteBuffer;
    move-result-object v12

    invoke-virtual {p1}, Landroid/content/Context;->getClassLoader()Ljava/lang/ClassLoader;
    move-result-object v13

    new-instance v0, Ldalvik/system/InMemoryDexClassLoader;
    invoke-direct {v0, v12, v13}, Ldalvik/system/InMemoryDexClassLoader;-><init>(Ljava/nio/ByteBuffer;Ljava/lang/ClassLoader;)V

    # salvar loader no campo
    iput-object v0, p0, Lcom/stub/loader/StubApplication;->dexLoader:Ldalvik/system/InMemoryDexClassLoader;

    return-void
.end method

.method private static readAll(Ljava/io/InputStream;)[B
    .registers 5
    new-instance v0, Ljava/io/ByteArrayOutputStream;
    invoke-direct {v0}, Ljava/io/ByteArrayOutputStream;-><init>()V

    const/16 v1, 0x1000
    new-array v2, v1, [B

    :read_loop
    const/4 v3, 0x0
    invoke-virtual {p0, v2, v3, v1}, Ljava/io/InputStream;->read([BII)I
    move-result v3
    if-ltz v3, :read_done
    const/4 v4, 0x0
    invoke-virtual {v0, v2, v4, v3}, Ljava/io/ByteArrayOutputStream;->write([BII)V
    goto :read_loop

    :read_done
    invoke-virtual {v0}, Ljava/io/ByteArrayOutputStream;->toByteArray()[B
    move-result-object v4
    return-object v4
.end method
