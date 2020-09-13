## CircleCI Kernel Building Script - Integrated with Telegram Bot

### 1. Set up config.yml on your repository. Example:
```
version: 2.1
jobs:
  compile:
   docker:
      - image: ubuntu:20.04
   steps:
      - run:
          no_output_timeout: 50m
          command: |
           apt-get -y update && apt-get -y upgrade && apt-get -y install bc build-essential bison flex zip gcc clang libc6 curl libstdc++6 git wget libssl-dev && apt-get -y install p7zip-full python python2 python3 python3-pip
           git clone https://github.com/zexceed12300/eternalx_ci
           cd eternalx_ci
           git clone https://github.com/zexceed12300/android_kernel_xiaomi_rosy-3.18.git -b circleci-project-setup --depth=1
           git clone https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9 -b ndk-release-r16 --depth=1
           pip3 install -r requirements.txt   
           python3 ci_build.py --build-image
workflows:
  version: 2.1
  cooking:
    jobs:
      - compile
```
### 2. Set Environtment With Telegram Bot
#### Important! before start building you should send message below to your bot. edit according to your needed
```
BUILD_KLIB=False
FLASHABLEZIP=False
DEVICE=rosy
FLASHABLE_STRING=EternalX<s>Kernel<s>Rev1.5<s>(stable)
FLASHABLE_ANDROID=8-10
KERNELSTRING=-EternalX-r1.5-rosy
DEFCONFIG=EternalX_defconfig
THREADS_JOBS=4
COMPILER=gcc
USER=xzen
HOST=zexceed12300
```
### 3. Done! start building now



