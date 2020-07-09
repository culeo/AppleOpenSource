require 'xcodeproj'
require 'fileutils'

project_path = ARGV[0]
# project_path = File.dirname(__FILE__) + '/objc4-750/objc.xcodeproj'
if project_path.nil?
    raise "未设置工程文件路径"
end

puts project_path
project = Xcodeproj::Project.open(project_path)

project.build_configurations.each do |config|
    config.build_settings["VALID_ARCHS"]="x86_64"
end


objc_target = project.targets.select { |target| target.name == 'objc' }.first
objc_trampolines_target = project.targets.select { |target| target.name == 'objc-trampolines' }.first

project.targets.clear
project.targets << objc_target

if !objc_trampolines_target.nil?
   project.targets << objc_trampolines_target
end

objc_target.build_configurations.each do |config|

    # 修改 SDKROOT
    config.build_settings["SDKROOT"] = "macosx"
    # 修改 MACOSX_DEPLOYMENT_TARGET
    config.build_settings["MACOSX_DEPLOYMENT_TARGET"] = "10.14"

    # 导入include头文件
    config.build_settings["SYSTEM_HEADER_SEARCH_PATHS"] = "${SRCROOT}/include"

    # Preprocessor Macros 添加 LIBC_NO_LIBCRASHREPORTERCLIENT
    macros = Array.new
    macros<<"OS_OBJECT_USE_OBJC=0"
    macros<<"LIBC_NO_LIBCRASHREPORTERCLIENT"
    if config.name == "Release"
        macros<<"NDEBUG=1"
    end
    config.build_settings["GCC_PREPROCESSOR_DEFINITIONS"] = macros

    # Other Linker Flags 中删除 -lCrashReporterClient
    ldflags = config.build_settings["OTHER_LDFLAGS[sdk=macosx*]"]
    if ldflags.kind_of? String
        ldflags = ldflags.split()
    end
    ldflags.delete("-lCrashReporterClient")
    config.build_settings["OTHER_LDFLAGS[sdk=macosx*]"] = ldflags

    # Order File 修改为 $(SRCROOT)/libobjc.order
    config.build_settings["ORDER_FILE"] = "${SRCROOT}/libobjc.order";

    # Text-Based InstallAPI Verification Model 改为 Errors Only
    config.build_settings["TAPI_VERIFY_MODE"]="ErrorsOnly";

    # Other Text-Based InstallAPI Flags 内容全部删除
    config.build_settings["OTHER_TAPI_FLAGS"]="";
end

objc_target.shell_script_build_phases.each do |script|
    if script.name == "Run Script (markgc)"
        script.shell_script = script.shell_script.gsub("macosx.internal", "macosx")
    end
end

# objc-trampolines
if !objc_trampolines_target.nil?
    objc_trampolines_target.build_configurations.each do |config|
        # 修改 SDKROOT
        config.build_settings["SDKROOT"] = "macosx"
        # 修改 MACOSX_DEPLOYMENT_TARGET
        config.build_settings["MACOSX_DEPLOYMENT_TARGET"] = "10.14"
    end
end

debug_objc_name = "debug-objc"
debug_objc_path = File.join(project.project_dir, debug_objc_name)
main_file_path = File.join(debug_objc_path, 'main.m')

# 创建 target
debug_objc_target = project.new_target(:command_line_tool, debug_objc_name, :osx, '10.14')
debug_objc_target.build_configurations.each do |config|
    # 修改 PRODUCT_NAME
    config.build_settings["PRODUCT_NAME"] = "$(TARGET_NAME)"
end   

# 创建目录
FileUtils.mkdir_p(debug_objc_path)

# 创建 main 文件
File.open(main_file_path, 'w') do |out|
    content = <<-DOC
//
//  main.m
//  debug-objc
//
//  Created by Leo on 2018/6/27.
//

#import <Foundation/Foundation.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        // insert code here...
        NSLog(@"Hello, World! %@", [NSObject class]);
    }
    return 0;
}
DOC
    out << content
end

# 创建 group
group = project.main_group.new_group(debug_objc_name, path=debug_objc_name)
# 调整 group 目录位置
project.main_group.children.delete(group)
project.main_group.children.insert(1, group)

# group 引用 main 文件
ref = group.new_reference(main_file_path)
debug_objc_target.add_file_references([ref])

# 依赖 objc
debug_objc_target.add_dependency(objc_target)

project.save
