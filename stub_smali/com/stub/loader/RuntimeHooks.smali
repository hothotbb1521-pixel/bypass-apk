.class public Lcom/stub/loader/RuntimeHooks;
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
