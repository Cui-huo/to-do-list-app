[app]

# 应用基础信息
title = 便签应用
package.name = notesapp
package.domain = com.github.cuihuo

# 入口文件
source.dir = .
main.py = main.py

# 版本
version = 1.2.0
version.code = 3

# Android 要求
android.minapi = 26
android.ndk = 25b
android.sdk = 34
android.api = 34
android.build_tools = 34.0.0

# 权限
android.permissions = INTERNET, VIBRATE, RECEIVE_BOOT_COMPLETED, POST_NOTIFICATIONS

# 应用架构（全部支持）
android.archs = arm64-v8a, armeabi-v7a

# Python 依赖（Android 构建时安装）
requirements = python3,kivy==2.3.1,kivymd==1.2.0,markdown,plyer,webdavclient3

# 源码排除
source.exclude_dirs = .git,.github,.pytest_cache,.qwen,.continue,__pycache__,tests,characterization,docs,.python312,.vscode,build,dist
source.exclude_exts = .pyc,.pyo,.log,.md~,.swp,.spec~

# 自定义字体（包含在 APK 中）
source.include_exts = py,png,jpg,kv,atlas,ttf,otf

# 全屏 + 方向
orientation = portrait
fullscreen = 1

# 窗口大小（桌面调试用，Android 忽略）
window.size = 420x740

# 启动画面
presplash.color = #1A237E
presplash.filename = %(source.dir)s/app_tool/res/presplash.png

# 应用图标
icon.filename = %(source.dir)s/app_tool/res/icon.png

# 日志
log_level = 2

# Android 特定
android.allow_backup = True
android.presplash_color = #1A237E

# WebDAV 同步需要网络
android.gradle_dependencies = androidx.core:core:1.9.0

# Kivy 启动参数
p4a.branch = v2024.01.21

# Buildozer 固定版本
buildozer.version = 1.5.0
