import os
import sys
import subprocess
import platform
import shutil

def compile_c_module():
    """
    Attempts to compile the image_processor.c file into a shared library.
    Detects the operating system and searches for cl.exe, gcc, or clang.
    Returns the absolute path to the compiled library if successful, or None if failed.
    """
    c_modules_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(c_modules_dir, "image_processor.c")
    
    # Define shared library names depending on the OS
    system = platform.system().lower()
    if system == "windows":
        lib_name = "image_processor.dll"
    elif system == "darwin":
        lib_name = "image_processor.dylib"
    else:
        lib_name = "image_processor.so"
        
    output_path = os.path.join(c_modules_dir, lib_name)
    
    # If the library is already compiled, return its path
    if os.path.exists(output_path):
        print(f"[C Module] Found existing shared library at: {output_path}")
        return output_path
        
    print(f"[C Module] Attempting to compile '{source_path}'...")
    
    # 1. Search for available compilers
    gcc_path = shutil.which("gcc")
    clang_path = shutil.which("clang")
    cl_path = shutil.which("cl")
    
    compiled = False
    
    try:
        if system == "windows":
            # On Windows, try gcc (MinGW), clang, or MSVC cl.exe
            if gcc_path:
                print("[C Module] Compiling with GCC...")
                cmd = ["gcc", "-shared", "-o", output_path, "-O3", source_path]
                subprocess.check_call(cmd)
                compiled = True
            elif clang_path:
                print("[C Module] Compiling with Clang...")
                cmd = ["clang", "-shared", "-o", output_path, "-O3", source_path]
                subprocess.check_call(cmd)
                compiled = True
            elif cl_path:
                print("[C Module] Compiling with MSVC cl...")
                # MSVC syntax for dll: cl /LD /O2 image_processor.c /Fe:image_processor.dll
                cmd = ["cl", "/LD", "/O2", source_path, f"/Fe:{output_path}"]
                subprocess.check_call(cmd)
                compiled = True
                # Clean up temporary build files created by MSVC (.obj, .lib, .exp)
                for ext in [".obj", ".lib", ".exp"]:
                    temp_file = os.path.join(c_modules_dir, "image_processor" + ext)
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            else:
                # Try searching in common MSYS64 or MinGW locations
                fallback_compilers = [
                    r"C:\msys64\mingw64\bin\gcc.exe",
                    r"C:\msys64\ucrt64\bin\gcc.exe",
                    r"C:\MinGW\bin\gcc.exe"
                ]
                for fb in fallback_compilers:
                    if os.path.exists(fb):
                        print(f"[C Module] Compiling using fallback GCC at: {fb}")
                        cmd = [fb, "-shared", "-o", output_path, "-O3", source_path]
                        subprocess.check_call(cmd)
                        compiled = True
                        break
        else:
            # Unix-like systems (Linux, macOS)
            compiler = "gcc" if gcc_path else ("clang" if clang_path else None)
            if compiler:
                print(f"[C Module] Compiling with {compiler}...")
                cmd = [compiler, "-shared", "-fPIC", "-o", output_path, "-O3", source_path, "-lm"]
                subprocess.check_call(cmd)
                compiled = True
            else:
                print("[C Module] Error: No C compiler (gcc or clang) found on system PATH.")
                
    except Exception as e:
        print(f"[C Module] Compilation failed: {e}")
        compiled = False
        
    if compiled and os.path.exists(output_path):
        print(f"[C Module] Successfully compiled shared library to: {output_path}")
        return output_path
    else:
        print("[C Module] Warning: Shared library compilation could not be completed.")
        print("[C Module] Pure-Python fallback will be utilized seamlessly.")
        return None

if __name__ == "__main__":
    compile_c_module()
