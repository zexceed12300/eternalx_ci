#!/usr/bin/env python

import time
import subprocess as subp
from subprocess import check_call
import os
import sys
import shutil as copy
import configparser

config = configparser.ConfigParser()
config.read('build.cfg')
compiler_cfg = config['COMPILER_CFG']
build_cfg = config['BUILD_CFG']
klib_cfg = config['BUILD_KLIB_CFG']
flashable_cfg = config['FLASHABLE_CFG']

ARCH = compiler_cfg['ARCH']
BUILD_OUTPUT = compiler_cfg['BUILD_OUTPUT']
CROSS_COMPILE = compiler_cfg['CROSS_COMPILE']
CLANG_TRIPLE = compiler_cfg['CLANG_TRIPLE']
CC = compiler_cfg['CC']

KERNELSTRING = build_cfg['KERNELSTRING']
DEFCONFIG = build_cfg['DEFCONFIG']
THREADS_JOBS = build_cfg['THREADS_JOBS']

INSTALL_MOD_PATH = klib_cfg['INSTALL_MOD_PATH']

ZIPNAME = flashable_cfg['ZIPNAME']

def build_image():
    time.sleep(10)
    with open('./build.log', 'w+') as log:
        start_time = time.time()
        check_call(['echo', '---------------', 'BUILD_DEFCONFIG', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
        check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
        check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
        check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
        end_time = time.time()  
        if os.path.exists("./out/arch/arm64/boot/Image.gz-dtb"):
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
            check_call(['zip', '-r9', '%s.zip' %ZIPNAME, '*'], cwd='anykernel', stdout=log, stderr=log, stdin=subp.PIPE)

build_image()