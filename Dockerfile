FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk wget unzip zip git cmake make \
    && rm -rf /var/lib/apt/lists/*

# apktool
RUN wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    printf '#!/bin/sh\nexec java -jar /usr/local/bin/apktool.jar "$@"\n' > /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool

# NDK r26d
RUN wget -q https://dl.google.com/android/repository/android-ndk-r26d-linux.zip -O /tmp/ndk.zip && \
    unzip -q /tmp/ndk.zip -d /opt && rm /tmp/ndk.zip
ENV NDK=/opt/android-ndk-r26d

WORKDIR /app
COPY . .

RUN pip install --break-system-packages -q flask gunicorn pycryptodome

# compile libhooks.so
RUN mkdir -p /app/jni/build_arm64 && cd /app/jni/build_arm64 && \
    cmake .. \
      -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
      -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 \
      -DCMAKE_BUILD_TYPE=Release && cmake --build . && \
    mkdir -p /app/prebuilt/arm64-v8a && cp libhooks.so /app/prebuilt/arm64-v8a/libhooks.so

RUN mkdir -p /app/jni/build_v7 && cd /app/jni/build_v7 && \
    cmake .. \
      -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
      -DANDROID_ABI=armeabi-v7a -DANDROID_PLATFORM=android-21 \
      -DCMAKE_BUILD_TYPE=Release && cmake --build . && \
    mkdir -p /app/prebuilt/armeabi-v7a && cp libhooks.so /app/prebuilt/armeabi-v7a/libhooks.so

EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "300", "app:app"]
