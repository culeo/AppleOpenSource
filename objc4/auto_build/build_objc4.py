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


system_version = '1014'
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

    # xnu
    downloader_url = base_url + "/tarballs/xnu/xnu-4570.1.46.tar.gz"
    downloader_file(downloader_url, path=save_path)
    xnu_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    # dyld_path
    downloader_url = base_url + "/tarballs/dyld/dyld-519.2.1.tar.gz"
    downloader_file(downloader_url, path=save_path)
    dyld_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    # libplatform_path
    downloader_url = base_url + "/tarballs/libplatform/libplatform-177.200.16.tar.gz"
    downloader_file(downloader_url, path=save_path)
    libplatform_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    # libc_path
    downloader_url = base_url + "/tarballs/Libc/Libc-825.40.1.tar.gz"
    downloader_file(downloader_url, path=save_path)
    libc_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    # libpthread_path
    downloader_url = base_url + "/tarballs/libpthread/libpthread-218.1.3.tar.gz"
    downloader_file(downloader_url, path=save_path)
    libpthread_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])

    # libclosure_path
    downloader_url = base_url + "/tarballs/libclosure/libclosure-67.tar.gz"
    downloader_file(downloader_url, path=save_path)
    libclosure_path = un_tar_gz(save_path + downloader_url.rsplit('/', 1)[-1])
 
    # 创建文件夹
    include_path = objc4_path + '/include'
    sys_path = include_path + '/sys/'
    system_path = include_path + '/System'
    system_machine_path = include_path + '/System/machine/'
    os_path = include_path + '/os'
    mach_o_path = include_path + '/mach-o'
    pthread_path = include_path + '/pthread'

    for path in [include_path, system_path, sys_path, system_machine_path, os_path, mach_o_path, pthread_path]:
        execute_cmd("mkdir -p " + path)

    # 复制文件
    execute_cmd("find " + xnu_path + " -name \"reason.h\" | xargs -I{} cp {} " + sys_path)
    execute_cmd("find " + xnu_path + " -name \"cpu_capabilities.h\" | grep machine | xargs -I{} cp {} " +
                system_machine_path)
    execute_cmd("find " + xnu_path + " -name \"tsd.h\" | grep os | xargs -I{} cp {} " + os_path)

    execute_cmd("find " + dyld_path + " -name \"dyld_priv.h\" | xargs -I{} cp {} " + mach_o_path)
    execute_cmd("find " + dyld_path + " -name \"objc-shared-cache.h\" | xargs -I{} cp {} " + include_path)

    execute_cmd("find " + libplatform_path + " -name \"_simple.h\" | xargs -I{} cp {} " + include_path)
    execute_cmd("find " + libplatform_path + " -name \"base_private.h\" | xargs -I{} cp {} " + os_path)
    execute_cmd("find " + libplatform_path + " -name \"lock_private.h\" | xargs -I{} cp {} " + os_path)

    execute_cmd("find " + libc_path + " -name \"CrashReporterClient.h\" | xargs -I{} cp {} " + include_path)
    execute_cmd("find " + libc_path + " -name \"pthread_machdep.h\" | xargs -I{} cp {} " + system_path)

    execute_cmd("find " + libpthread_path + " -name \"tsd_private.h\" | xargs -I{} cp {} " + pthread_path)
    execute_cmd("find " + libpthread_path + " -name \"spinlock_private.h\" | xargs -I{} cp {} " + pthread_path)
  
    execute_cmd("find " + libclosure_path + " -name \"Block_private.h\" | xargs -I{} cp {} " + include_path)

    execute_cmd("sed -i '' 's/#include <objc\/objc-block-trampolines.h>//g' " + objc4_path +"/runtime/objc-block-trampolines.mm")

    execute_cmd("rm -r " + xnu_path)
    execute_cmd("rm -r " + dyld_path)
    execute_cmd("rm -r " + libplatform_path)
    execute_cmd("rm -r " + libc_path)
    execute_cmd("rm -r " + libpthread_path)
    execute_cmd("rm -r " + libclosure_path)

    # 拷贝 /runtime/isa.h 到include
    execute_cmd("find " + objc4_path + " -name \"isa.h\" | xargs -I{} cp {} " + include_path)

    # 删除 #include <objc\/objc-block-trampolines.h>
    execute_cmd("sed -i '' 's/#include <objc\/objc-block-trampolines.h>//g' " + objc4_path +"/runtime/objc-block-trampolines.mm")
    # 配置工程
    execute_cmd("ruby " + save_path + "config_objc4.rb " + objc4_path+"/objc.xcodeproj")

    # 修改源文件
    handle_pthread_machdep_file(system_path + "/pthread_machdep.h")
    handle_dyld_priv_file(mach_o_path + "/dyld_priv.h")


if __name__ == '__main__':
    run_main()
    print "构建完成"