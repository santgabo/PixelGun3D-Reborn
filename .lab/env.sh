# Bash only. Opt in explicitly: source .lab/env.sh
# Installed locally: .NET SDK 10.0.401, ILSpyCmd 11.1.0.9782,
# UnityPy 1.25.4 (Python 3.14 venv), AssetRipper Free 2.0.0,
# Temurin JDK 21.0.12.1+1-LTS, JADX 1.5.6, Apktool 3.0.3,
# Android Command-line Tools 17.0 (build 12700392) and Platform-Tools/ADB 37.0.1.
# SDK/ADB CLI_READY only; android-sdk-license accepted for these two packages.
# UnityPy object decoding is partial: STATIC_READY=DEFERRED.
# RUNTIME_READY=BLOCKED; emulator/image installation is not authorized.
# KVM, device ABI, network isolation and restoration remain unverified.
# Invoke Apktool explicitly: java -jar "$LAB_APKTOOL_JAR" (decode only).
# Sourcing neither starts tools nor certifies readiness.
export LAB_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
umask 077
export LAB_MIN_FREE_GIB=10
export DOTNET_ROOT="$LAB_ROOT/tools/dotnet"
export DOTNET_CLI_HOME="$LAB_ROOT/private/dotnet-home"
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
export DOTNET_NOLOGO=1
export DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true
export NUGET_PACKAGES="$LAB_ROOT/private/nuget-packages"
export JAVA_HOME="$LAB_ROOT/tools/java"
export ANDROID_HOME="$LAB_ROOT/tools/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_USER_HOME="$LAB_ROOT/private/android-user"
export ANDROID_AVD_HOME="$LAB_ROOT/private/android-avd"
export XDG_CACHE_HOME="$LAB_ROOT/private/cache"
export XDG_CONFIG_HOME="$LAB_ROOT/private/config"
export XDG_DATA_HOME="$LAB_ROOT/private/data"
export PIP_CACHE_DIR="$LAB_ROOT/private/pip-cache"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_REQUIRE_VIRTUALENV=true
export PYTHONNOUSERSITE=1
export LAB_UNITYPY_PYTHON="$LAB_ROOT/venvs/unitypy/bin/python"
export LAB_APKTOOL_JAR="$LAB_ROOT/tools/apktool/apktool_3.0.3.jar"
export LAB_ASSETRIPPER="$LAB_ROOT/tools/assetripper/AssetRipper.GUI.Free"
export PATH="$DOTNET_ROOT:$LAB_ROOT/tools/ilspy:$JAVA_HOME/bin:$LAB_ROOT/tools/jadx/bin:$ANDROID_HOME/cmdline-tools/17.0/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
# Deliberately do not activate a venv, accept SDK licenses, launch adb/emulator,
# change LD_LIBRARY_PATH, or modify ~/.bashrc. Use LAB_UNITYPY_PYTHON explicitly.
