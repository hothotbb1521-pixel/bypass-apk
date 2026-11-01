FROM eclipse-temurin:17-jdk-jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 python3-pip wget unzip zip git cmake make \
    && rm -rf /var/lib/apt/lists/*

# apktool
RUN wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    printf '#!/bin/sh\nexec java -jar /usr/local/bin/apktool.jar "$@"\n' > /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool

# zipalign + apksigner + d8 via cmdline-tools
RUN wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdtools.zip && \
    mkdir -p /opt/android-sdk/cmdline-tools && \
    unzip -q /tmp/cmdtools.zip -d /opt/android-sdk/cmdline-tools && \
    mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest && \
    rm /tmp/cmdtools.zip
ENV ANDROID_HOME=/opt/android-sdk
RUN yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses > /dev/null 2>&1 && \
    /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager "build-tools;34.0.0" "platforms;android-34" > /dev/null 2>&1
ENV PATH=$PATH:/opt/android-sdk/build-tools/34.0.0

# NDK r26d
RUN wget -q https://dl.google.com/android/repository/android-ndk-r26d-linux.zip -O /tmp/ndk.zip && \
    unzip -q /tmp/ndk.zip -d /opt && rm /tmp/ndk.zip
ENV NDK=/opt/android-ndk-r26d

WORKDIR /app
COPY . .

RUN wget -q https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && \
    python3 /tmp/get-pip.py && \
    pip3 install flask gunicorn pycryptodome

# compile libhooks.so arm64
RUN mkdir -p /app/jni/build_arm64 && cd /app/jni/build_arm64 && \
    cmake .. \
      -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
      -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 \
      -DCMAKE_BUILD_TYPE=Release && cmake --build . && \
    mkdir -p /app/prebuilt/arm64-v8a && cp libhooks.so /app/prebuilt/arm64-v8a/

# compile libhooks.so armeabi-v7a
RUN mkdir -p /app/jni/build_v7 && cd /app/jni/build_v7 && \
    cmake .. \
      -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
      -DANDROID_ABI=armeabi-v7a -DANDROID_PLATFORM=android-21 \
      -DCMAKE_BUILD_TYPE=Release && cmake --build . && \
    mkdir -p /app/prebuilt/armeabi-v7a && cp libhooks.so /app/prebuilt/armeabi-v7a/

EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "300", "app:app"]
