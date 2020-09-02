#!/usr/bin/env python

import time
import subprocess as subp
from subprocess import check_call
import os
import sys
import shutil as copy
import configparser
import requests
import json
import argparse

# Configuration - build.cfg
config = configparser.ConfigParser()
config.read('build.cfg')
compiler_cfg = config['COMPILER_CFG']
build_cfg = config['BUILD_CFG']
klib_cfg = config['BUILD_KLIB_CFG']
tele_notifier = config['TELE_NOTIFIER']

COMPILER = compiler_cfg['COMPILER']
CROSS_COMPILE = compiler_cfg['CROSS_COMPILE']
CLANG_TRIPLE = compiler_cfg['CLANG_TRIPLE']
CC = compiler_cfg['CC']

ARCH = build_cfg['ARCH']
BUILD_OUTPUT = build_cfg['BUILD_OUTPUT']
KERNELSTRING = build_cfg['KERNELSTRING']
DEFCONFIG = build_cfg['DEFCONFIG']
USER = build_cfg['USER']
HOST = build_cfg['HOST']

INSTALL_MOD_PATH = klib_cfg['INSTALL_MOD_PATH']

ZIPNAME = "KERNEL-"+KERNELSTRING

TELETOKEN = tele_notifier['TOKEN']

def parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("")

class TeleNotifier:
    def __init__(self):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/getUpdates"
        resp = requests.post(url).content
        data = json.loads(resp)
        latest_id = len(data['result']) - 1
        self.cfg = eval(str(data['result'][latest_id]['message']['text'].split()).replace("=", "':'").replace("[","{").replace("]", "}").replace("\s",""))
        self.chat_id = data['result'][latest_id]['message']['chat']['id']

    def sendMessage(self, message):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/sendMessage"
        data = {'chat_id': self.chat_id, 'parse_mode': 'html', 'text': message}
        resp = requests.post(url, data=)

    def SendFile(self, file):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/sendDocument"
        resp = requests.post(url, files={'document': file}).json()

    def SetEnviron(self):
        global KERNELSTRING
        KERNELSTRING = self.cfg['KERNELSTRING']
        global THREADS_JOBS
        THREADS_JOBS = self.cfg['THREADS_JOBS']
        global COMPILER
        COMPILER = self.cfg['COMPILER']
        global DEFCONFIG
        DEFCONFIG = self.cfg['DEFCONFIG']
        global USER
        USER = self.cfg['USER']
        global HOST
        HOST = self.cfg['HOST']

def build_image():
    with open('./build.log', 'w+') as log:
        start_time = time.time()
        try:
            check_call(['echo', '---------------', 'BUILD_DEFCONFIG', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            if COMPILER == "clang" and CLANG_TRIPLE and CC:
                check_call(['make', 'ARCH=%s' %ARCH, 'KBUILD_BUILD_USER=%s' %USER, 'KBUILD_BUILD_HOST=%s' %HOST, 'CC=%s' %CC, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'CLANG_TRIPLE=%s' %CLANG_TRIPLE, 'O=%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['make', 'ARCH=%s' %ARCH, 'KBUILD_BUILD_USER=%s' %USER, 'KBUILD_BUILD_HOST=%s' %HOST, 'CC=%s' %CC, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'CLANG_TRIPLE=%s' %CLANG_TRIPLE, 'O=%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
            else:
                check_call(['make', 'ARCH=%s' %ARCH, 'KBUILD_BUILD_USER=%s' %USER, 'KBUILD_BUILD_HOST=%s' %HOST, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['make', 'ARCH=%s' %ARCH, 'KBUILD_BUILD_USER=%s' %USER, 'KBUILD_BUILD_HOST=%s' %HOST, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
            end_time = time.time()  
            if os.path.exists("./out/arch/arm64/boot/Image.gz-dtb"):
                print('KERNEL: Build Success!')
            else:
                print('KERNEL: Build Failed!')
        except subp.CalledProcessError:
                print('KERNEL: Build Failed!')

def build_klib():
    with open('./build.log', 'r+') as log:
        try:
            check_call(['echo', '\n-----------------', 'BUILD_KLIB', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            check_call(['make', 'ARCH=%s' %ARCH, 'CROSS_COMPILE=%s' %CROSS_COMPILE, 'O=%s' %BUILD_OUTPUT, 'modules_install', 'INSTALL_MOD_PATH=%s' %INSTALL_MOD_PATH], cwd='kernel', stdout=log, stderr=log, stdin=subp.PIPE)
            if os.path.exist("%s/lib" %INSTALL_MOD_PATH):
                print("KLIB: Build Success!")
            else:
                print("KLIB: Build Failed!")
        except subp.CalledProcessError:
                print("KLIB: Build Failed!")

def create_zip():
    with open("./build.log", "r+") as log:
        if os.path.exists("./out/arch/arm64/boot/Image.gz"):
            if ARCH == "arm64":
                copy.copy2("./out/arch/arm64/boot/Image.gz-dtb", "./anykernel/")
            try:
                check_call(['echo', '\n--------------', 'CREATE_FLASHABLE', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['zip', '-r9', '%s.zip' %ZIPNAME, '*'], cwd='anykernel', stdout=log, stderr=log, stdin=subp.PIPE)
                if os.path.exist("./anykernel/%s.zip" %ZIPNAME):
                    copy.copy2("./anykernel/%s.zip" %ZIPNAME, ".")
                    print("ANYKERNEL: Build Success!")
                else:
                    print("ANYKERNEL: Build Failed!")
            except subp.CalledProcessError:
                print("ANYKERNEL: Build Failed!")
    
