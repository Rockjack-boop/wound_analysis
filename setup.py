from setuptools import setup
import subprocess
import platform
import os

# Compile C module during build phase on Vercel
try:
    system = platform.system().lower()
    c_modules_dir = os.path.join(os.path.dirname(__file__), "c_modules")
    source_path = os.path.join(c_modules_dir, "image_processor.c")
    
    if system == "windows":
        lib_name = "libimage_processor.dll"
    elif system == "darwin":
        lib_name = "libimage_processor.dylib"
    else:
        lib_name = "libimage_processor.so"
        
    output_path = os.path.join(c_modules_dir, lib_name)
    
    print(f"[Build Compile] Compiling {source_path} to {output_path}...")
    
    if system == "windows":
        # We already have a pre-compiled DLL on Windows
        pass
    else:
        # On Vercel / Linux, compile using gcc
        cmd = ["gcc", "-shared", "-fPIC", "-o", output_path, "-O3", source_path, "-lm"]
        subprocess.check_call(cmd)
        print(f"[Build Compile] Successfully compiled C module to: {output_path}")
except Exception as e:
    print(f"[Build Compile] Compilation failed: {e}")

setup(
    name="path1",
    version="0.1",
    packages=["c_modules"],
)
