#!/usr/bin/env python3

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
config.read('ci_build.cfg')
tele_notifier = config['TELE_NOTIFIER']
dir_name = config['DIRNAME_CFG']
compiler_cfg = config['COMPILER_CFG']
build_cfg = config['BUILD_CFG']
flashable_cfg = config['FLASHABLE_CFG']

SOURCE_DIR = dir_name['SOURCE']
ANYKERNEL_DIR = dir_name['ANYKERNEL']

os.environ['PATH'] = compiler_cfg['PATH']+":"+os.environ["PATH"]
COMPILER = compiler_cfg['COMPILER']
os.environ['CROSS_COMPILE'] = compiler_cfg['CROSS_COMPILE']
os.environ['CROSS_COMPILE_ARM32'] = compiler_cfg['CROSS_COMPILE_ARM32']
os.environ['CLANG_TRIPLE'] = compiler_cfg['CLANG_TRIPLE']
CC = compiler_cfg['CC']

os.environ['ARCH'] = build_cfg['ARCH']
BUILD_OUTPUT = build_cfg['BUILD_OUTPUT']
KERNELSTRING = build_cfg['KERNELSTRING']
DEFCONFIG = build_cfg['DEFCONFIG']
USER = build_cfg['USER']
HOST = build_cfg['HOST']

ZIPNAME = "KERNEL"+KERNELSTRING
DEVICE = flashable_cfg['DEVICE']
FLASHABLE_STRING = flashable_cfg['FLASHABLE_STRING']
FLASHABLE_ANDROID = flashable_cfg['FLASHABLE_ANDROID']

TELETOKEN = tele_notifier['TOKEN']

date = subp.run(['date'], stdout=subp.PIPE).stdout.decode("utf-8")

args_create_flashable = "False"
args_build_klib = "False"

elapsed_time = []
error_detail = ""
error_count = 0
warning_count = 0

class TeleNotifier:
    def __init__(self):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/getUpdates"
        resp = requests.post(url).content
        data = json.loads(resp)
        latest_id = len(data['result']) - 1
        self.cfg = eval(str(data['result'][latest_id]['message']['text'].split()).replace("=", "':'").replace("[","{").replace("]", "}").replace("\s",""))
        self.chat_id = data['result'][latest_id]['message']['chat']['id']

    def SendMessage(self, message):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/sendMessage"
        data = {'chat_id': self.chat_id, 'parse_mode': 'html', 'text': message}
        resp = requests.post(url, data=data)

    def SendFile(self, file):
        url = "https://api.telegram.org/bot"+TELETOKEN+"/sendDocument"
        data = {'chat_id': self.chat_id}
        resp = requests.post(url, data=data, files={'document': file}).json()

    def SetEnviron(self):
        global DEVICE
        DEVICE = self.cfg['DEVICE']
        global FLASHABLE_STRING
        FLASHABLE_STRING = self.cfg['FLASHABLE_STRING'].replace("<s>", " ")
        global FLASHABLE_ANDROID
        FLASHABLE_ANDROID = self.cfg['FLASHABLE_ANDROID'].replace("-", " - ")
        global args_build_klib
        args_build_klib = self.cfg['BUILD_KLIB']
        global args_create_flashable
        args_create_flashable = self.cfg['FLASHABLEZIP']
        global KERNELSTRING
        KERNELSTRING = self.cfg['KERNELSTRING']
        os.environ['KBUILD_BUILD_VERSION'] = KERNELSTRING
        global THREADS_JOBS
        THREADS_JOBS = self.cfg['THREADS_JOBS']
        global COMPILER
        COMPILER = self.cfg['COMPILER']
        global DEFCONFIG
        DEFCONFIG = self.cfg['DEFCONFIG']
        global USER
        USER = self.cfg['USER']
        os.environ['KBUILD_BUILD_USER'] = USER
        global HOST
        HOST = self.cfg['HOST']
        os.environ['KBUIL_BUILD_HOST'] = HOST

def parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-image", help="Build Kernel Image.gz-dtb And Modules", action="store_true")
    parser.add_argument("--build-klib", help="Export Kernel Libraries and Modules", action="store_true")
    parser.add_argument("--create-flashable", help="Packing Kernel Image and modules. Ready for flash", action="store_true")
    args = parser.parse_args()

    if args.build_image:
        TeleNotifier().SetEnviron()
        TeleNotifier().SendMessage('<b>[ + ] BUILDING STARTED!</b>\nat <b>{}</b>\n<b>Device</b> : {}\n<b>Supported Android</b> : {}\n<b>Kernel String</b> : {}\n<b>Compiler</b> : {}\n<b>Defconfig</b> : {}\n<b>CPU Jobs</b> : {}\n<b>User</b> : {}\n<b>Host</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date ,DEVICE, FLASHABLE_ANDROID ,KERNELSTRING, COMPILER, DEFCONFIG, THREADS_JOBS, USER, HOST))
        build_image()
    else:
        print("--build-image is required!")
        sys.exit
    if args_build_klib == "True":
        if args.build_image:
            build_klib()
        else:
            print("cant --build-klib without --build-image")
            sys.exit()
    if args_create_flashable == "True":
        if args.build_image:
            create_zip()
        else:
            print("cant --create-flashable without --build-image")
            sys.exit()

def build_image():
    global elapsed_time
    global error_detail
    global error_count
    global warning_count
    with open('./build.log', 'w+') as log:
        start_time = time.time()
        time.sleep(3)
        try:
            check_call(['echo', '---------------', 'BUILD_DEFCONFIG', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            if COMPILER == "clang" and CLANG_TRIPLE and CC:
                print("build with clang")
                check_call(['make', 'CC=%s' %CC, 'O=../%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd=SOURCE_DIR, stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['make', 'CC=%s' %CC, 'O=../%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd=SOURCE_DIR, stdout=log, stderr=log, stdin=subp.PIPE)
            else:
                print("build with gcc")
                check_call(['make', 'O=../%s' %BUILD_OUTPUT, '%s' %DEFCONFIG], cwd=SOURCE_DIR, stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['echo', '\n------------------', 'COMPILING', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['make', 'O=../%s' %BUILD_OUTPUT, '-j%s' %THREADS_JOBS], cwd=SOURCE_DIR, stdout=log, stderr=log, stdin=subp.PIPE) 
            elapsed_time.append(float(int(time.time() - start_time) / 3600))
            elapsed_time.append(float(int(time.time() - start_time) / 60))
            elapsed_time.append(float(int(time.time() - start_time)))
            if os.path.exists("./%s/arch/arm64/boot/Image.gz-dtb" %BUILD_OUTPUT):
                print('KERNEL: Build Success!')
                for i in open("build.log", "r").readlines():
                    if "make" in i:
                        i = "" 
                    if "warning" in i:
                        i = ""  
                        warning_count += 1
                    if ":" in i:
                        if not error_detail:
                            error_detail += i
                            print(error_detail)
                        error_count += 1
                if args_create_flashable == "False":
                    copy.copy2("./%s/arch/arm64/boot/Image.gz-dtb" %BUILD_OUTPUT, ".")
                    TeleNotifier().SendMessage('<b>[ * ] BUILDING FINISHED!</b>\nat <b>{}</b>\n<b>Elapsed Time</b> : {:.0f} h {:.0f} min {:.0f} sec\n<b>Warning : {}</b>\n<b>Errors</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date , elapsed_time[0], elapsed_time[1], elapsed_time[2], warning_count, error_count))
                    print("sending build.log")
                    TeleNotifier().SendFile(open("build.log", "rb"))
                    TeleNotifier().SendFile(open("Image.gz-dtb", "rb"))
            else:
                print('KERNEL: Build Failed!')
        except subp.CalledProcessError:
                elapsed_time.append(float(int(time.time() - start_time) / 3600))
                elapsed_time.append(float(int(time.time() - start_time) / 60))
                elapsed_time.append(float(int(time.time() - start_time)))
                print('KERNEL: Build Failed!')
                for i in open("build.log", "r").readlines():
                    if "make" in i:
                        i = "" 
                    if "warning" in i:
                        i = ""  
                        warning_count += 1
                    if ":" in i:
                        if not error_detail:
                            error_detail += i
                            print(error_detail)
                        error_count += 1
                TeleNotifier().SendMessage('<b>[ ! ] BUILDING FAILED!</b>\nat <b>{}</b>\n<b>Error Preview: </b>\n{}.  .  .\n\n<b>Elapsed Time</b> : {:.0f} h {:.0f} min {:.0f} sec\n<b>Warnings : {}</b>\n<b>Errors</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date , error_detail, elapsed_time[0], elapsed_time[1], elapsed_time[2], warning_count, error_count))
                TeleNotifier().SendFile(open("build.log", "rb"))
                sys.exit()

def build_klib():
    global elapsed_time
    global error_detail
    global error_count
    global warning_count
    with open('./build.log', 'a') as log:
        try:
            check_call(['echo', '\n-----------------', 'BUILD_KLIB', '------------------'], stdout=log, stderr=log, stdin=subp.PIPE)
            check_call(['make', 'O=../%s' %BUILD_OUTPUT, 'modules_install', 'INSTALL_MOD_PATH=../'], cwd=SOURCE_DIR, stdout=log, stderr=log, stdin=subp.PIPE)
            if os.path.exists("lib"):
                print("KLIB: Build Success!")
            else:
                print("KLIB: Build Failed!")
        except subp.CalledProcessError:
            for i in open("build.log", "r").readlines():
                    if "make" in i:
                        i = "" 
                    if "warning" in i:
                        i = ""  
                        warning_count += 1
                    if ":" in i:
                        if not error_detail:
                            error_detail += i
                            print(error_detail)
                        error_count += 1
            TeleNotifier().SendMessage('<b>[ ! ] BUILDING FAILED!</b>\nat <b>{}</b>\n<b>Error Preview: </b>\nFailed to build klib\n.  .  .\n\n<b>Elapsed Time</b> : {:.0f} h {:.0f} min {:.0f} sec\n<b>Warnings : {}</b>\n<b>Errors</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date, elapsed_time[0], elapsed_time[1], elapsed_time[2], warning_count, error_count))
            TeleNotifier().SendFile(open("build.log", "rb"))
            print("KLIB: Build Failed!")

def create_zip():
    global elapsed_time
    global error_detail
    global error_count
    global warning_count
    with open("./build.log", "a") as log:
        if os.path.exists("%s/arch/arm64/boot/Image.gz" %BUILD_OUTPUT):
            copy.copy2("%s/arch/arm64/boot/Image.gz-dtb" %BUILD_OUTPUT, "%s/" %ANYKERNEL_DIR)
            buf = open("%s/anykernel.sh" %ANYKERNEL_DIR, "r").readlines()
            buf[6] = ['kernel.string=%s\n' %FLASHABLE_STRING]
            if args_build_klib =="True":
                buf[8] = ['do.modules=1\n']
            buf[12] = ['device.name1=%s\n' %DEVICE]
            buf[17] = ['supported.version=%s\n' %FLASHABLE_ANDROID]
            wbuf = open("%s/anykernel.sh" %ANYKERNEL_DIR, "w")
            for i in buf:
                wbuf.writelines(i)
            dirs = []
            if args_build_klib == "True":
                for i in os.walk("./lib/modules"):
                    for j in i:
                        dirs.append(j)
                        break
                os.unlink("%s/source" %dirs[1])
                os.unlink("%s/build" %dirs[1])
                try:
                    copy.copytree(dirs[1], "%s/modules/system/%s" %(ANYKERNEL_DIR, dirs[1]))
                except FileExistsError:
                    pass
            if args_build_klib == "True":
                copy.copy2("%s/arch/arm64/boot/Image.gz-dtb" %BUILD_OUTPUT, "%s/modules/" %ANYKERNEL_DIR)
            try:
                check_call(['echo', '\n--------------', 'CREATE_FLASHABLE', '---------------'], stdout=log, stderr=log, stdin=subp.PIPE)
                check_call(['zip', '-r9', '%s.zip' %ZIPNAME, '.', '-x', 'LICENSE', '.git/', 'README.md'], cwd=ANYKERNEL_DIR, stdout=log, stderr=log, stdin=subp.PIPE)
                if os.path.exists("%s/%s.zip" %(ANYKERNEL_DIR, ZIPNAME)):
                    copy.copy2("%s/%s.zip" %(ANYKERNEL_DIR, ZIPNAME), ".")
                    TeleNotifier().SendMessage('<b>[ * ] BUILDING FINISHED!</b>\nat <b>{}</b>\n<b>Elapsed Time</b> : {:.0f} h {:.0f} min {:.0f} sec\n<b>Warning : {}</b>\n<b>Errors</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date , elapsed_time[0], elapsed_time[1], elapsed_time[2], warning_count, error_count))
                    TeleNotifier().SendFile(open("build.log", "rb"))
                    TeleNotifier().SendFile(open("%s.zip" %ZIPNAME, "rb"))
                    print("ANYKERNEL: Build Success!")
                else:
                    print("ANYKERNEL: Build Failed!")
            except subp.CalledProcessError:
                for i in open("build.log", "r").readlines():
                    if "make" in i:
                        i = "" 
                    if "warning" in i:
                        i = ""  
                        warning_count += 1
                    if ":" in i:
                        if not error_detail:
                            error_detail += i
                            print(error_detail)
                        error_count += 1
                TeleNotifier().SendMessage('<b>[ ! ] BUILDING FAILED!</b>\nat <b>{}</b>\n<b>Error Preview: </b>\nFailed to create flashable zip\n.  .  .\n\n<b>Elapsed Time</b> : {:.0f} h {:.0f} min {:.0f} sec\n<b>Warnings : {}</b>\n<b>Errors</b> : {}\n\n-- CircleCI script by zexceed12300'.format(date, elapsed_time[0], elapsed_time[1], elapsed_time[2], warning_count, error_count))
                TeleNotifier().SendFile(open("build.log", "rb"))
                print("ANYKERNEL: Build Failed!")

parameters()
