[app]
# 基础配置
title = Comic Reader
package.name = comicreader
package.domain = org.kivy
version = 1.0.0

# 关键修复：必须包含 source.dir
source.dir = .
source.main = main.py  # 指定入口文件

# 构建配置
requirements = 
    python3==3.10.5,
    kivy==2.3.0,
    pillow==10.1.0,
    pyjnius==1.5.0,
    android

# Android 配置
android.api = 34
android.minapi = 21
android.ndk_version = 25b
android.archs = arm64-v8a

# 权限
android.permissions = 
    INTERNET,
    READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2