## CircleCI Kernel Building Script - Integrated with Telegram Bot
### HowTo build kernel with this script
1. You can show script feature by --help argument
```
$ python3 ci_build.py --help
usage: ci_build.py [-h] [--build] [--clean] [--verbose] [--tele-notifier] [--tele-check]
                   [--tele-tz <Geographic Area/City or Region>] [--tele-ship <File>]

optional arguments:
  -h, --help            show this help message and exit
  --build               Start building kernel
  --clean               Clean building & log
  --verbose             Verbosely building process
  --tele-notifier       Enable telegram bot notifier & fetch configuration
  --tele-check          Enable build confirmation dialog to telegram bot
  --tele-tz <Geographic Area/City or Region>
                        Synchrone Telegram Time Zone (e.g: Asia/Jakarta)
  --tele-ship <File>    Ship a file to telegram bot
```
2. Do it yourself.
### Integration with CircleCI
1. Set up config.yml on your repository. Example:
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
           apt-get -y update && apt-get -y upgrade && apt-get -y install bc build-essential bison flex zip gcc clang libc6 curl libstdc++6 git wget libssl-dev && apt-get -y install p7zip-full python python2 python3 python3-pip tzdata
           git clone https://github.com/zexceed12300/eternalx_ci
           cd eternalx_ci
           git clone https://github.com/zexceed12300/android_kernel_xiaomi_rosy-3.18.git -b circleci-project-setup --depth=1
           git clone https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9 -b ndk-release-r16 --depth=1
           pip3 install -r requirements.txt   
           python3 ci_build.py --build --tele-notifier --tele-check --verbose --tele-tz Asia/Jakarta
workflows:
  version: 2.1
  cooking:
    jobs:
      - compile
```
2. Edit ci_build.cfg according to your needed (instruction inside)

3. (Optional) Before you start building, you can override the ci_build.cfg by sending configuration message to telegram bot. example:
```
KLIB=True
FLASHABLE=True
DO_DEVICE=rosy
KERNEL_STRING=EternalX<s>Kernel<s>Stable
SUPPORTED_VER=8-9
ZIPNAME=kernel-name
DEFCONFIG=someone_defconfig
CPU=6
COMPILER=clang
USER=zexceed
HOST=lawliet
```
NOTE
* space not allowed (except KERNEL_STRING use ```<s>``` for space).
* sending after/during building will cause the configuration not be replaced.
* message on telegram bot will be readable for 24 hours. if past 24 hour you need send the message again.
* if configurations is not in the message. it will be follow default ci_build.cfg.
* that message case sensitive.

4. Start building by push some commit to your repository or start in circleci pipelines.
