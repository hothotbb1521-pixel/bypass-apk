.class public Lcom/stub/loader/StubApplication;
.super Landroid/app/Application;

.field private realApp:Landroid/app/Application;

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
    .registers 2
    invoke-super {p0}, Landroid/app/Application;->onCreate()V
    iget-object v0, p0, Lcom/stub/loader/StubApplication;->realApp:Landroid/app/Application;
    if-eqz v0, :skip
    invoke-virtual {v0}, Landroid/app/Application;->onCreate()V
    :skip
    return-void
.end method

.method private loadPayload(Landroid/content/Context;)V
    .registers 16

    # ler k.bin (32 key + 16 iv = 48 bytes)
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

    const/4 v14, 0x0
    const/16 v15, 0x20
    invoke-static {v3, v14, v15}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v4

    const/16 v14, 0x20
    const/16 v15, 0x30
    invoke-static {v3, v14, v15}, Ljava/util/Arrays;->copyOfRange([BII)[B
    move-result-object v5

    # ler p.bin (dex encriptado)
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "p.bin"
    invoke-virtual {v0, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v6
    invoke-static {v6}, Lcom/stub/loader/StubApplication;->readAll(Ljava/io/InputStream;)[B
    move-result-object v7
    invoke-virtual {v6}, Ljava/io/InputStream;->close()V

    # decrypt AES/CBC
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

    # criar InMemoryDexClassLoader
    invoke-static {v11}, Ljava/nio/ByteBuffer;->wrap([B)Ljava/nio/ByteBuffer;
    move-result-object v12

    invoke-virtual {p1}, Landroid/content/Context;->getClassLoader()Ljava/lang/ClassLoader;
    move-result-object v13

    new-instance v0, Ldalvik/system/InMemoryDexClassLoader;
    invoke-direct {v0, v12, v13}, Ldalvik/system/InMemoryDexClassLoader;-><init>(Ljava/nio/ByteBuffer;Ljava/lang/ClassLoader;)V

    # ler nome da Application original de a.bin
    invoke-virtual {p1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v1
    const-string v2, "a.bin"
    invoke-virtual {v1, v2}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v2
    invoke-static {v2}, Lcom/stub/loader/StubApplication;->readAll(Ljava/io/InputStream;)[B
    move-result-object v3
    invoke-virtual {v2}, Ljava/io/InputStream;->close()V
    new-instance v1, Ljava/lang/String;
    invoke-direct {v1, v3}, Ljava/lang/String;-><init>([B)V

    # loadClass(nome) via novo classloader
    invoke-virtual {v0, v1}, Ljava/lang/ClassLoader;->loadClass(Ljava/lang/String;)Ljava/lang/Class;
    move-result-object v2

    # instanciar a Application real
    invoke-virtual {v2}, Ljava/lang/Class;->newInstance()Ljava/lang/Object;
    move-result-object v3

    check-cast v3, Landroid/app/Application;
    iput-object v3, p0, Lcom/stub/loader/StubApplication;->realApp:Landroid/app/Application;

    # chamar attachBaseContext na app real
    invoke-virtual {v3, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V

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
