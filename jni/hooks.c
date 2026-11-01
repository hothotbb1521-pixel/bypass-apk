#include <jni.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#if defined(__aarch64__)
  #define EP_OFFSET 0x20
#else
  #define EP_OFFSET 0x14
#endif

static jint stub_gms(JNIEnv* e, jobject t, jobject c) {
    (void)e; (void)t; (void)c; return 9;
}

static void make_rw(void* addr) {
    uintptr_t page = (uintptr_t)addr & ~(uintptr_t)4095;
    mprotect((void*)page, 8192, PROT_READ|PROT_WRITE|PROT_EXEC);
}

JNIEXPORT void JNICALL Java_com_stub_loader_ArtHook_hookMethodNative(
        JNIEnv* env, jclass cls, jobject method) {
    jclass mc = (*env)->GetObjectClass(env, method);
    jfieldID fid = (*env)->GetFieldID(env, mc, "artMethod", "J");
    if (!fid) { (*env)->ExceptionClear(env); return; }
    jlong ptr = (*env)->GetLongField(env, method, fid);
    if (!ptr) return;
    uint8_t* art = (uint8_t*)(uintptr_t)ptr;
    make_rw(art + EP_OFFSET);
    uintptr_t ep = (uintptr_t)stub_gms;
    memcpy(art + EP_OFFSET, &ep, sizeof(uintptr_t));
    __builtin___clear_cache((char*)(art+EP_OFFSET),
                            (char*)(art+EP_OFFSET+sizeof(uintptr_t)));
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* r) {
    (void)r; JNIEnv* env;
    if ((*vm)->GetEnv(vm, (void**)&env, JNI_VERSION_1_6) != JNI_OK) return -1;
    return JNI_VERSION_1_6;
}
