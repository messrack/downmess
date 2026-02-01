#!/bin/bash
set -e
echo "Installing Git..."
sudo apt-get install -y git

echo "Configuring Git Global (Force LF)..."
git config --global core.autocrlf false

echo "Cloning Flutter SDK..."
mkdir -p ~/development
# Force clean clone
rm -rf ~/development/flutter

git clone https://github.com/flutter/flutter.git -b stable ~/development/flutter

echo "Configuring Environment..."
grep -q "development/flutter/bin" ~/.bashrc || echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> ~/.bashrc
grep -q "ANDROID_HOME" ~/.bashrc || echo 'export ANDROID_HOME="$HOME/android-sdk"' >> ~/.bashrc
grep -q "platform-tools" ~/.bashrc || echo 'export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"' >> ~/.bashrc

export PATH="$PATH:$HOME/development/flutter/bin:$HOME/android-sdk/cmdline-tools/latest/bin:$HOME/android-sdk/platform-tools"

echo "Pre-caching Flutter binaries..."
flutter precache

echo "Accepting Android Licenses for Flutter..."
yes | flutter doctor --android-licenses || true

echo "Flutter Doctor..."
flutter doctor

echo "Flutter Setup Complete."
