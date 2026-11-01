.class public Lcom/stub/loader/StubApplication;
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
