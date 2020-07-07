# -*- coding: utf-8 -*-

from lxml import etree
from Queue import Queue
import threading
import os
import urllib
import sys
import math
import requests
import gzip
import tarfile
import shutil


# system_version = '1014'
system_version = '1015'

base_url = 'https://opensource.apple.com'
source_url = base_url + '/release/macos-'+system_version+'.html'
save_path = os.getcwd() + '/'


class DownloadThread(threading.Thread):
    """
    下载线程
    """
    def __init__(self, queue, path):  # 传入线程名、实例化队列
        threading.Thread.__init__(self)  # t_name即是threadName
        self.queue = queue
        self.path = path
        self.url = str()

    def run(self):
        while True:
            # Get the work from the queue
            url = self.queue.get()
            self.url = url
            print ('正在下载 %s' % self.url)
            self.downloader()
            self.queue.task_done()

    def downloader(self):
        local = os.path.join(self.path, os.path.basename(self.url))
        urllib.urlretrieve(self.url, local)


def downloader_files(urls, path):
    if not os.path.exists(path):
        os.makedirs(path)

    queue = Queue()
    max_thread = 5 if len(urls) > 5 else len(urls)
    for x in range(max_thread):
        worker = DownloadThread(queue, path)
        worker.daemon = True
        worker.start()

    for url in urls:
        queue.put(url)

    queue.join()
    print('全部下载完成')


def downloader_file(url, path):
    print '下载文件 %s' % url
    downloader_path = os.path.join(path, os.path.basename(url))
    try:
        urllib.urlretrieve(url, downloader_path, progressbar)
    except urllib.ContentTooShortError:
        print 'Network conditions is not good.Reloading.'
        downloader_file(url, path)


def progressbar(block_num, bs, size):
    total = 100
    cur = block_num * bs * 100 / (size * 1.0)
    cur = cur if cur < 100.0 else 100.0
    percent = '{:.2%}'.format(cur * 0.01)
    sys.stdout.write('\r')
    sys.stdout.write('[%-50s] %s' % ('=' * int(math.floor(cur * 50 / total)), percent))
    sys.stdout.flush()
    if cur == total:
        sys.stdout.write('\n')


def un_gz(file_path):
    """ungz zip file"""
    # 获取文件的名称，去掉
    new_path = file_path.replace(".gz", "")
    # 创建gzip对象
    g_file = gzip.GzipFile(file_path)
    # gzip对象用read()打开后，写入open()建立的文件里。
    open(new_path, "w+").write(g_file.read())
    # 关闭gzip对象
    g_file.close()
    os.remove(file_path)
    return new_path


def un_tar(file_path):
    """untar zip file"""
    new_path, new_name = os.path.split(file_path)
    tar = tarfile.open(file_path)
    for name in tar.getnames():
        tar.extract(name, new_path)
    tar.close()
    os.remove(file_path)
    return new_path + '/' + os.path.splitext(new_name)[0]


def un_tar_gz(file_name):
    file_name = un_gz(file_name)
    file_name = un_tar(file_name)
    return file_name


def execute_cmd(cmd):
    print cmd
    os.system(cmd)


def handle_pthread_machdep_file(path):
    
    if not os.path.exists(path): return

    data = ''
    with open(path, 'r+') as f:
        flag = 1;
        for line in f.readlines():
            if (line.find('typedef int pthread_lock_t') != -1):
                flag = 0;
            elif (line.find('#define LOCK_INIT(l)') != -1):
                flag = 1;
            
            if flag == 1:
                data += line

    with open(path, 'w') as f:
        f.writelines(data)
    

def handle_dyld_priv_file(path):

    if not os.path.exists(path): return

    data = ''
    with open(path, 'r+') as f:
        flag = 1;
        for line in f.readlines():
            data += line
            if (line.find('#define _MACH_O_DYLD_PRIV_H_') != -1):
                data += "\n"
                data += "#define DYLD_MACOSX_VERSION_10_11 0x000A0B00\n"
                data += "#define DYLD_MACOSX_VERSION_10_12 0x000A0C00\n"
                data += "#define DYLD_MACOSX_VERSION_10_13 0x000A0D00\n"
                data += "#define DYLD_MACOSX_VERSION_10_14 0x000A0E00\n"

    with open(path, 'w') as f:
        f.writelines(data)

def run_main():
   
    response = requests.get(source_url).text
    html = etree.HTML(response)

    # objc4
    downloader_url = base_url + html.xpath("//a[contains(@href,'objc4-')]/@href")[1]
    downloader_file(downloader_url, path=save_path)
    objc4_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    save_paths = {}
    configs = get_configs()

    # 下载
    for key, path in configs["download_urls"].items():
        download_url = base_url + path
        downloader_file(download_url, path=save_path)
        save_paths[key] = un_tar_gz(save_path + download_url.rsplit('/', 1)[-1])

    print save_paths

    include_path = objc4_path + '/include'
    execute_cmd("mkdir -p " + include_path)

    # 复制
    for copy_file in configs["copy_files"]:
        target_dir = include_path + copy_file["target"]
        if not os.path.exists(target_dir):
            execute_cmd("mkdir -p " + target_dir)
        source_file = save_paths[copy_file["framework"]] + copy_file["source"]
        execute_cmd("cp " + source_file + " " + target_dir)

    for key, path in save_paths.items():
            execute_cmd("rm -r " + path)

    if system_version == '1014':
        # 拷贝 /runtime/isa.h 到include
        execute_cmd("cp " + objc4_path + "/runtime/isa.h " + include_path)
        # 删除 #include <objc\/objc-block-trampolines.h>
        execute_cmd("sed -i '' 's/#include <objc\/objc-block-trampolines.h>//g' " + objc4_path +"/runtime/objc-block-trampolines.mm")

    # 修改源文件
    handle_pthread_machdep_file(include_path + "/System/pthread_machdep.h")
    handle_dyld_priv_file(include_path + "/mach-o/dyld_priv.h")

    # 配置工程
    execute_cmd("ruby " + save_path + "config_objc4.rb " + objc4_path+"/objc.xcodeproj")


def configs_1014():
    return {
        "download_urls": {
            "xnu": "/tarballs/xnu/xnu-4570.1.46.tar.gz",
            "dyld": "/tarballs/dyld/dyld-519.2.1.tar.gz",
            "libplatform": "/tarballs/libplatform/libplatform-177.200.16.tar.gz",
            "libc": "/tarballs/Libc/Libc-825.40.1.tar.gz",
            "libpthread": "/tarballs/libpthread/libpthread-218.1.3.tar.gz",
            "libclosure": "/tarballs/libclosure/libclosure-67.tar.gz",
        }, 
        "copy_files": [
            {
                "framework": "xnu",
                "source": "/bsd/sys/reason.h",
                "target": "/sys/"
            },
            {
                "framework": "xnu",
                "source": "/osfmk/machine/cpu_capabilities.h",
                "target": "/System/machine/"
            },
            {
                "framework": "xnu",
                "source": "/libsyscall/os/tsd.h",
                "target": "/os/"
            },
            {
                "framework": "dyld",
                "source": "/include/mach-o/dyld_priv.h",
                "target": "/mach-o/"
            },
            {
                "framework": "dyld",
                "source": "/include/objc-shared-cache.h",
                "target": "/"
            },
            {
                "framework": "libplatform",
                "source": "/private/_simple.h",
                "target": "/"
            },
            {          
                "framework": "libplatform",
                "source": "/private/os/base_private.h",
                "target": "/os/"
            },
            {
                "framework": "libplatform",
                "source": "/private/os/lock_private.h",
                "target": "/os/"
            },
            {
                "framework": "libc",
                "source": "/include/CrashReporterClient.h",
                "target": "/"
            },
            {
                "framework": "libc",
                "source": "/pthreads/pthread_machdep.h",
                "target": "/System/"
            },
            {
                "framework": "libpthread",
                "source": "/private/tsd_private.h",
                "target": "/pthread/"
            },
            {
                "framework": "libpthread",
                "source": "/private/spinlock_private.h",
                "target": "/pthread/"
            },
            {
                "framework": "libclosure",
                "source": "/Block_private.h",
                "target": "/"
            }
        ]
    }

def configs_1015():
    return {
        "download_urls": {
            "xnu": "/tarballs/xnu/xnu-4903.241.1.tar.gz",
            "dyld": "/tarballs/dyld/dyld-655.1.1.tar.gz",
            "libplatform": "/tarballs/libplatform/libplatform-177.250.1.tar.gz",
            "libc": "/tarballs/Libc/Libc-1722.250.1.tar.gz",
            "libpthread": "/tarballs/libpthread/libpthread-330.250.2.tar.gz",
            "libclosure": "/tarballs/libclosure/libclosure-73.tar.gz",
        }, 
        "copy_files": [
            {
                "framework": "xnu",
                "source": "/bsd/sys/reason.h",
                "target": "/sys/"
            },
            {
                "framework": "xnu",
                "source": "/osfmk/machine/cpu_capabilities.h",
                "target": "/System/machine/"
            },
            {
                "framework": "xnu",
                "source": "/libsyscall/os/tsd.h",
                "target": "/os/"
            },
            {
                "framework": "dyld",
                "source": "/include/mach-o/dyld_priv.h",
                "target": "/mach-o/"
            },
            {
                "framework": "dyld",
                "source": "/include/objc-shared-cache.h",
                "target": "/"
            },
            {
                "framework": "libplatform",
                "source": "/private/_simple.h",
                "target": "/"
            },
            {          
                "framework": "libplatform",
                "source": "/private/os/base_private.h",
                "target": "/os/"
            },
            {
                "framework": "libplatform",
                "source": "/private/os/lock_private.h",
                "target": "/os/"
            },
            {
                "framework": "libc",
                "source": "/include/CrashReporterClient.h",
                "target": "/"
            },
            {
                "framework": "libc",
                "source": "/pthreads/pthread_machdep.h",
                "target": "/System/"
            },
            {
                "framework": "libpthread",
                "source": "/private/tsd_private.h",
                "target": "/pthread/"
            },
            {
                "framework": "libpthread",
                "source": "/private/spinlock_private.h",
                "target": "/pthread/"
            },
            {
                "framework": "libclosure",
                "source": "/Block_private.h",
                "target": "/"
            }
        ]
    }

def get_configs():
    if system_version == '1015': return configs_1015()
    return configs_1014()

if __name__ == '__main__':
    run_main()
    print "构建完成"