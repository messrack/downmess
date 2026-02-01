#!/bin/bash
set -e
echo "Removing broken Flutter clone..."
rm -rf ~/development/flutter
mkdir -p ~/development

echo "Downloading Flutter Tarball..."
# Using a recent stable version
wget -O flutter.tar.xz https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.19.3-stable.tar.xz

echo "Extracting Flutter..."
tar -xf flutter.tar.xz -C ~/development/
rm flutter.tar.xz

echo "Configuring Environment..."
export PATH="$PATH:$HOME/development/flutter/bin:$HOME/android-sdk/cmdline-tools/latest/bin:$HOME/android-sdk/platform-tools"

echo "Pre-caching Flutter binaries..."
flutter precache

echo "Accepting Android Licenses..."
yes | flutter doctor --android-licenses || true

echo "Flutter Doctor..."
flutter doctor

echo "Flutter Setup Complete."
