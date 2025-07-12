#!/usr/bin/env python3
"""
سكريبت رفع المشروع على GitHub
"""

import subprocess
import sys
import os

def run_command(command):
    """تشغيل أمر في الطرفية"""
    print(f"🔄 تنفيذ: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ نجح: {result.stdout}")
        return True
    else:
        print(f"❌ فشل: {result.stderr}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء رفع المشروع على GitHub...")
    print("=" * 50)
    
    # الأوامر المطلوبة
    commands = [
        'git config credential.helper store',
        'git remote set-url origin https://elashrafy69:600600@Mm12@github.com/elashrafy69/alaa-academy.git',
        'git push -u origin main'
    ]
    
    for command in commands:
        if not run_command(command):
            print("❌ فشل في رفع المشروع")
            return False
    
    print("=" * 50)
    print("🎉 تم رفع المشروع بنجاح!")
    print("🌐 رابط المشروع: https://github.com/elashrafy69/alaa-academy")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
