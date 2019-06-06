# 编译libmalloc-166.220.60源码

#### 环境
MacOS Mojave 10.14.4
Xcode10.2

#### 步骤

##### 1. 下载 libmalloc-166.220.60
[https://opensource.apple.com/tarballs/libmalloc/libmalloc-166.200.60.tar.gz](https://opensource.apple.com/tarballs/libmalloc/libmalloc-166.200.60.tar.gz)

##### 2. 下载依赖库
[libplatform-177.200.16](https://opensource.apple.com/tarballs/libplatform/libplatform-177.200.16.tar.gz)
[xnu-4570.1.46](https://opensource.apple.com/tarballs/xnu/xnu-4570.1.46.tar.gz)
[dyld-519.2.1.tar.gz](https://opensource.apple.com/tarballs/dyld/dyld-519.2.1.tar.gz)

##### 3. 复制依赖头文件
复制下列文件到libmalloc/include/对应位置
libplatform/private/_simple.h -> include/_simple.h
libplatform/private/platform/compat.h -> include/platform/compat.h
libplatform/private/platform/string.h -> include/platform/string.h
libplatform/private/os/base_private.h -> include/os/base_private.h
libplatform/private/os/lock_private.h -> include/os/lock_private.h
libplatform/private/os/once_private.h -> include/os/once_private.h
libplatform/private/os/internal/atomic.h -> include/os/internal/atomic.h
libplatform/private/os/internal/crashlog.h -> include/os/internal/crashlog.h
libplatform/private/os/internal/internal_shared.h -> include/os/internal/internal_shared.h
xnu/osfmk/machine/cpu_capabilities.h -> include/os/machine/cpu_capabilities.h
xnu/libsyscall/os/tsd.h -> include/os/tsd.h
dyld/include/mach-o/dyld_priv.h -> include/mach-o/dyld_priv.h

##### 4. 修改Build Settings
1. 删掉除 libsystem_malloc 以外的所有 target
2. 删掉除 libsystem_malloc 以外的所有 scheme
3. 修改 libsystem_malloc target 中 System Header Search Paths ${SRCROOT}/include

##### 5.修改源文件
1. 删掉 resolver，tests，xcodeconfig，tools 目录

2. 删除 radix_tree.c, radix_tree.h, nanov2_malloc.c, nanov2_malloc.h, nanov2_zone.h 文件
 
3. 删除 #include "nanov2_malloc.h", #include "nanov2_zone.h", #include "radix_tree.h" 引用

4. 删除 handle_msl_memory_event, malloc_memory_event_handler 方法
 
6. nanov2_create_zone, nanov2_forked_zone, nanov2_init, nanov2_configure 调用这些方法的地方，把方法名中的v2去掉
```
nanov2_create_zone -> nano_create_zone
nanov2_forked_zone -> nano_forked_zone
nanov2_init -> nano_init
nanov2_configure -> nano_configure
```

1. 在 magazine_inline.h 头部加入
```
#define _COMM_PAGE64_BASE_ADDRESS      ( 0x00007fffffe00000ULL ) 
#define _COMM_PAGE_START_ADDRESS		_COMM_PAGE64_BASE_ADDRESS 
#define	_COMM_PAGE_MEMORY_SIZE			(_COMM_PAGE_START_ADDRESS+0x038)
#define _COMM_PAGE_NCPUS  				(_COMM_PAGE_START_ADDRESS+0x022) 
#define	_COMM_PAGE_PHYSICAL_CPUS		(_COMM_PAGE_START_ADDRESS+0x035)
#define	_COMM_PAGE_LOGICAL_CPUS			(_COMM_PAGE_START_ADDRESS+0x036)
```

8. 删除 create_scalable_szone 方法中以下代码
```
#if defined(__i386__) || defined(__x86_64__)
if (_COMM_PAGE_VERSION_REQD > (*((uint16_t *)_COMM_PAGE_VERSION))) {
    MALLOC_REPORT_FATAL_ERROR((*((uint16_t *)_COMM_PAGE_VERSION)), "comm page version mismatch");
	}
#endif
```