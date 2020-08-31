#!/usr/bin/env python

# COMPILER SETUP
ARCH                = "arm64"                           # Device Architecture
BUILD_OUTPUT        = "../out"                          # Compiling output
CROSS_COMPILE       = "/bin/aarch64-linux-android-"     # PATH to gcc toolchains
CLANG_TRIPLE        = ""                                # leave empty if not using clang
CC                  = ""                                # leave empty if not using clang

# BUILD KERNEL IMAGE
KERNELSTRING        = "EternalX-HMP-r1.5-rosy"
DEFCONFIG           = "rosy-doge_defconfig"             # Kernel Configuration
THREADS_JOBS        = 4                                 # Number of CPU threads to using it for compile

# BUILD KLIB
INSTALL_MOD_PATH    = "../"                             # Path to install Kernel Library And Modules

# CREATE FLASHABLE
FLASHABLE_NAME      = "KERNEL-EternalX-HMP-r1.5-rosy"   # Flashable zip name


import time
import subprocess as subp
from subprocess import check_call
import os
import sys
import shutil as copy

def build_image():
    time.sleep(10)
    with open('./build.log', 'w+') as log:
        start_time = time.time()
        check_call(['echo', '---------------', 'BUILD_DEFCONFIG', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
        check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
        try:
            check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
            end_time = time.time()  
        except KeyboardInterrupt:
            print('[*] Build Failed!')
        if os.path.exist("./out/arch/arm64/boot/Image.gz-dtb"):
            print('[*] Build Success!')
        else:
            print('[*] Build Failed!')

def build_klib():
    with open('./build.log', 'r+') as log:
        check_call(['echo', '\n-----------------', 'BUILD_KLIB', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
        check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, 'modules_install', 'INSTALL_MOD_PATH=%s' %INSTALL_MOD_PATH], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)

def create_zip():
    with open("./build.log", "r+") as log:
        if os.path.exist("./out/arch/arm64/boot/Image.gz"):
            if ARCH == "arm64":
                copy.copy2("./out/arch/arm64/boot/Image.gz-dtb", "./anykernel/")
            check_call(['echo', '\n--------------', 'CREATE_FLASHABLE', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            check_call(['zip', '-r9', '%s.zip' %FLASHABLE_NAME, '*'], cwd='anykernel', stdout=log, stderr=log, stdin=subp.PIPE)
