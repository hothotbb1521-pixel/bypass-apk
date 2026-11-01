.class public Lcom/stub/loader/ArtHook;
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
