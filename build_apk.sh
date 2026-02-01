#!/bin/bash
set -e

# 1. Environment Setup
export ANDROID_HOME=$HOME/android-sdk
export PATH=$HOME/development/flutter/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

echo "PATH: $PATH"
flutter --version

# 2. Workspace Setup
echo "Setting up build workspace..."
rm -rf ~/downmess_build
mkdir -p ~/downmess_build
cp /mnt/c/Users/MESS/Desktop/downmess/downmess_mobile.py ~/downmess_build/main.py
cp /mnt/c/Users/MESS/Desktop/downmess/downmess_core.py ~/downmess_build/
cp /mnt/c/Users/MESS/Desktop/downmess/requirements.txt ~/downmess_build/

cd ~/downmess_build

# 3. Dependencies
echo "Installing Python dependencies..."
# Create venv to avoid root issues
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install flet

# 4. Build
echo "Building APK..."
flet build apk --verbose

# 5. Retrieve Artifact
echo "Copying APK to Desktop..."
mkdir -p /mnt/c/Users/MESS/Desktop/downmess_apk
cp build/apk/*.apk /mnt/c/Users/MESS/Desktop/downmess_apk/

echo "Build Complete! Check 'downmess_apk' folder on your Desktop."
