package com.stub.loader;

import android.app.Application;
import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import dalvik.system.InMemoryDexClassLoader;

public class StubApplication extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        try { loadPayload(base); } catch (Exception ignored) {}
    }

    private void loadPayload(Context ctx) throws Exception {
        InputStream ks = ctx.getAssets().open("k.bin");
        byte[] kb = new byte[48];
        ks.read(kb, 0, 48);
        ks.close();
        byte[] key = Arrays.copyOfRange(kb, 0, 32);
        byte[] iv  = Arrays.copyOfRange(kb, 32, 48);

        InputStream ps = ctx.getAssets().open("p.bin");
        byte[] enc = readAll(ps);
        ps.close();

        Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");
        c.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"), new IvParameterSpec(iv));
        byte[] dex = c.doFinal(enc);

        new InMemoryDexClassLoader(ByteBuffer.wrap(dex), ctx.getClassLoader());
    }

    private static byte[] readAll(InputStream in) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf, 0, buf.length)) != -1) out.write(buf, 0, n);
        return out.toByteArray();
    }
}
