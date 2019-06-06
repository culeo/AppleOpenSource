require 'xcodeproj'

project_path = ARGV[0]
# project_path = File.dirname(__FILE__) + '/objc4-750/objc.xcodeproj'
if project_path.nil?
    raise "未设置工程文件路径"
end

puts project_path
project = Xcodeproj::Project.open(project_path)

# 删除多余targets
project.targets.delete_at(1)
project.targets.delete_at(1)

project.build_configurations.each do |config|
    config.build_settings["VALID_ARCHS"]="x86_64"
end

target = project.targets[0]
target.build_configurations.each do |config|

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

target.shell_script_build_phases.each do |script|
    if script.name == "Run Script (markgc)"
        script.shell_script = script.shell_script.gsub("macosx.internal", "macosx")
    end
end

project.save
