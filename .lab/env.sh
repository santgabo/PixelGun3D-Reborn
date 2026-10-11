# Bash only. Opt in explicitly: source .lab/env.sh
# Suite restored locally on 2026-10-11; no adjacent checkout is required.
# Python 3.14.7 / UnityPy 1.25.4 + TypeTreeGeneratorAPI 0.0.10,
# REA 6.4.0 / JADX headless MCP 0.7.1. The original lock below is historical;
# current acquisition and functional receipts are in .lab/private/setup and
# .lab/private/runtime-setup; recovered outputs are in .lab/runs/.
# Installed locally: .NET SDK 10.0.401, ILSpyCmd 11.1.0.9782,
# UnityPy 1.25.4 (Python 3.14 venv), AssetRipper Free 2.0.0,
# Temurin JDK 21.0.12.1+1-LTS, JADX 1.5.6, Apktool 3.0.3,
# Android Command-line Tools 17.0 (build 12700392) and Platform-Tools/ADB 37.0.1.
# Current run 20261011T174958Z-completion recovered fields of 490022/490030 objects;
# eight missing-type payloads remain preserved. Original tutorial/menu passed twice
# on API25/x86 with KVM in isolated bubblewrap. Older TCG/deferred reports are historical.
# This file does NOT isolate network or start runtime. Never launch the game outside
# its verified namespace. Private runtime env/commands live in that run; see
# docs/lab/preparacion-runtime.md. No firewall/host administrative changes made.
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
export LAB_REA="$LAB_ROOT/tools/rea/node_modules/.bin/rea"
export REA_JADX_MCP_JAR="$LAB_ROOT/tools/jadx-mcp/jadx-headless-mcp-0.7.1-all.jar"
export REA_ILSPY_CMD_PATH="$LAB_ROOT/tools/ilspy/ilspycmd"
export REA_APKTOOL_COMMAND="$LAB_ROOT/tools/apktool/apktool"
export REA_ADB_PATH="$ANDROID_HOME/platform-tools/adb"
export PATH="$DOTNET_ROOT:$LAB_ROOT/tools/ilspy:$JAVA_HOME/bin:$LAB_ROOT/tools/rea/node_modules/.bin:$LAB_ROOT/tools/apktool:$LAB_ROOT/tools/jadx/bin:$ANDROID_HOME/cmdline-tools/17.0/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
# Deliberately do not activate a venv, accept SDK licenses, launch adb/emulator,
# change LD_LIBRARY_PATH, or modify ~/.bashrc. Use LAB_UNITYPY_PYTHON explicitly.
