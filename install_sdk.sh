#!/bin/bash
set -e
mkdir -p ~/android-sdk/cmdline-tools
echo "Downloading Command Line Tools..."
wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O tools.zip
unzip -q tools.zip -d ~/android-sdk/cmdline-tools
# If the zip extracts to 'cmdline-tools' we move it to 'latest'
if [ -d "~/android-sdk/cmdline-tools/cmdline-tools" ]; then
    mv ~/android-sdk/cmdline-tools/cmdline-tools ~/android-sdk/cmdline-tools/latest
else
    # Some versions extract differently, let's ensure structure is cmdline-tools/latest
    # If it extracted directly into cmdline-tools, we need to move it.
    # Actually, simpler: just rename whatever was extracted if it's not 'latest'
    # But usually it extracts a folder named 'cmdline-tools'.
    mv ~/android-sdk/cmdline-tools/cmdline-tools ~/android-sdk/cmdline-tools/latest
fi
rm tools.zip

export ANDROID_HOME=$HOME/android-sdk
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

echo "Accepting Licenses..."
yes | sdkmanager --licenses > /dev/null

echo "Installing Platform Tools & SDK..."
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

echo "Android SDK Setup Complete."
