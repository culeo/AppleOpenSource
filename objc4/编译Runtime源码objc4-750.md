# 编译Runtime源码objc4-750

#### 环境
MacOS Mojave 10.14.4
Xcode10.2

#### 步骤
##### 1. 下载objc4-750
 [https://opensource.apple.com/release/macos-1014.html](https://opensource.apple.com/release/macos-1014.html)

##### 2. 下载依赖库

1. [xnu-4570.1.46.tar.gz](https://opensource.apple.com/tarballs/xnu/xnu-4570.1.46.tar.gz)
2. [dyld-519.2.1.tar.gz](https://opensource.apple.com/tarballs/dyld/dyld-519.2.1.tar.gz)
3. [libplatform-177.200.16.tar.gz](https://opensource.apple.com/tarballs/libplatform/libplatform-177.200.16.tar.gz)
4. [libpthread-218.1.3.tar.gz](https://opensource.apple.com/tarballs/Libc/Libc-825.40.1.tar.gz)
5. [libpthread-218.1.3.tar.gz](https://opensource.apple.com/tarballs/libpthread/libpthread-218.1.3.tar.gz)
6. [libclosure-67.tar.gz](https://opensource.apple.com/tarballs/libclosure/libclosure-67.tar.gz)

##### 3. 复制依赖头文件
在 objc4-750 目录下创建 include 文件夹，然后复制以下文件到对应位置
1. /xnu-4570.1.46/bsd/sys/reason.h -> /include/sys/reason.h
2. /xnu-4570.1.46/osfmk/machine/cpu_capabilities.h -> /include/System/machine/cpu_capabilities.h
3. /xnu-4570.1.46/libsyscall/os/tsd.h -> /include/os/tsd.h
4. /dyld-519.2.1/include/mach-o/dyld_priv.h -> /include/mach-o/dyld_priv.h
5. /dyld-519.2.1/include/objc-shared-cache.h -> /include/objc-shared-cache.h
6. /libplatform-177.200.16/private/_simple.h -> /include/_simple.h
7. /libplatform-177.200.16/private/os/base_private.h -> /include/os/base_private.h
8. /libplatform-177.200.16/private/os/lock_private.h -> /include/os/lock_private.h
9. /Libc-825.40.1/include/CrashReporterClient.h -> /include/CrashReporterClient.h
10. /Libc-825.40.1/pthreads/pthread_machdep.h -> /include/System/CrashReporterClient.h
11. /libpthread-218.1.3/private/tsd_private.h -> /include/pthread/tsd_private.h
12. /libpthread-218.1.3/private/spinlock_private.h -> /include/pthread/spinlock_private.h
13. /libclosure-67/Block_private.h -> /include/Block_private.h

##### 4. 修改Build Settings
1. Valid Architectures 删除 i386 架构
2. objc-simulator, objc-trampolines target 删除
3. 导入include头文件
4. 修改 System Header Search Paths ${SRCROOT}/include
5. Preprocessor Macros 添加 LIBC_NO_LIBCRASHREPORTERCLIENT
6. Other Linker Flags 中删除 -lCrashReporterClient
7. Order File 修改为 $(SRCROOT)/libobjc.order
8. Text-Based InstallAPI Verification Model 改为 Errors Only
9. Other Text-Based InstallAPI Flags 内容全部删除

##### 5. 修改 Build Phases
RunScript(markgc) 中macosx.internal 改为 macosx

##### 6.修改源文件
1. 删除 objc-block-trampolines.mm 文件中 #include <objc/objc-block-trampolines.h>

2. 删除 pthread_machdep.h 文件中 <br>typedef int pthread_lock_t 声明 <br> _pthread_has_direct_tsd(void) <br> _pthread_getspecific_direct(unsigned long slot) <br> _pthread_setspecific_direct(unsigned long slot, void * val)方法

3. dyld_priv.h 文件中加入 
```
#define DYLD_MACOSX_VERSION_10_11 0x000A0B00 
#define DYLD_MACOSX_VERSION_10_12 0x000A0C00
#define DYLD_MACOSX_VERSION_10_13 0x000A0D00
#define DYLD_MACOSX_VERSION_10_14 0x000A0E00
```

#### 附
可以编译 objc4 工程: 