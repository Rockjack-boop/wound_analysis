import os
import time
import ctypes
import numpy as np
from PIL import Image

# Import the compiler helper
from c_modules.compile import compile_c_module

# ----------------------------------------------------
# Global state for tracking compilation / C library
# ----------------------------------------------------
C_LIB = None
COMPILATION_ERROR = None
IS_COMPILED = False

try:
    # Attempt C compilation
    lib_path = compile_c_module()
    if lib_path and os.path.exists(lib_path):
        # Load the shared library
        C_LIB = ctypes.CDLL(lib_path)
        
        # Define C argument and return types
        
        # void convert_to_grayscale(unsigned char* pixels, int width, int height, int channels)
        C_LIB.convert_to_grayscale.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int
        ]
        C_LIB.convert_to_grayscale.restype = None
        
        # void detect_sobel_edges(const unsigned char* src, unsigned char* dst, int width, int height, int channels)
        C_LIB.detect_sobel_edges.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int
        ]
        C_LIB.detect_sobel_edges.restype = None
        
        # int detect_redness_pixels(const unsigned char* pixels, unsigned char* dst_filtered, int width, int height, int channels)
        C_LIB.detect_redness_pixels.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int
        ]
        C_LIB.detect_redness_pixels.restype = ctypes.c_int
        
        IS_COMPILED = True
        print("[C Module] ctypes connection initialized successfully.")
    else:
        COMPILATION_ERROR = "No compatible C compiler found on host machine."
except Exception as e:
    COMPILATION_ERROR = str(e)
    print(f"[C Module] Error loading shared library: {e}")
    print("[C Module] Switching exclusively to high-performance NumPy fallback.")

# ----------------------------------------------------
# Pure-Python / NumPy Fallbacks
# ----------------------------------------------------
def _fallback_grayscale(img_array):
    """NumPy grayscale conversion mimicking the C logic."""
    r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
    gray = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)
    
    # Replicate gray into 3 channels
    gray_3ch = np.stack([gray, gray, gray], axis=-1)
    if img_array.shape[2] == 4:
        # Keep alpha
        alpha = img_array[:, :, 3:4]
        return np.concatenate([gray_3ch, alpha], axis=-1).astype(np.uint8)
    return gray_3ch.astype(np.uint8)

def _fallback_sobel(gray_array):
    """NumPy-accelerated Sobel edge detection mimicking C convolution."""
    h, w, c = gray_array.shape
    # Extract first channel (intensity) for operations
    gray_1ch = gray_array[:, :, 0].astype(np.float32)
    
    # Force destination buffer to be uint8 directly
    dst = np.zeros_like(gray_1ch, dtype=np.uint8)
    
    if h > 2 and w > 2:
        # Extract slices representing 3x3 neighbors
        im00 = gray_1ch[0:-2, 0:-2]
        im01 = gray_1ch[0:-2, 1:-1]
        im02 = gray_1ch[0:-2, 2:]
        im10 = gray_1ch[1:-1, 0:-2]
        im12 = gray_1ch[1:-1, 2:]
        im20 = gray_1ch[2:, 0:-2]
        im21 = gray_1ch[2:, 1:-1]
        im22 = gray_1ch[2:, 2:]
        
        # Calculate gradients in X and Y directions
        gx = (im02 - im00) + 2.0 * (im12 - im10) + (im22 - im20)
        gy = (im20 - im00) + 2.0 * (im21 - im01) + (im22 - im02)
        
        # Gradient Magnitude
        mag = np.sqrt(gx**2 + gy**2)
        mag = np.clip(mag, 0, 255).astype(np.uint8)
        
        # Store in inner portion
        dst[1:-1, 1:-1] = mag
        
    # Replicate into multi-channel output
    edges_3ch = np.stack([dst, dst, dst], axis=-1)
    if c == 4:
        alpha = gray_array[:, :, 3:4]
        return np.concatenate([edges_3ch, alpha], axis=-1).astype(np.uint8)
    return edges_3ch.astype(np.uint8)

def _fallback_redness(img_array):
    """NumPy redness filtering mimicking C inflammation detection."""
    h, w, c = img_array.shape
    r = img_array[:, :, 0].astype(np.float32)
    g = img_array[:, :, 1].astype(np.float32)
    b = img_array[:, :, 2].astype(np.float32)
    
    # Infection criteria: Red is high and 1.25x larger than green and blue
    mask = (r > 120) & (r > (g * 1.25)) & (r > (b * 1.25))
    red_count = int(np.sum(mask))
    
    # Pre-calculate dark gray background
    gray = (0.299 * r + 0.587 * g + 0.114 * b)
    dark_gray = (gray / 3).astype(np.uint8)
    
    # Construct output
    dst = np.stack([dark_gray, dark_gray, dark_gray], axis=-1).astype(np.uint8)
    
    # Highlighting masks
    dst[mask, 0] = img_array[mask, 0] # Keep red channel
    dst[mask, 1] = 0
    dst[mask, 2] = 0
    
    if c == 4:
        alpha = img_array[:, :, 3:4]
        dst = np.concatenate([dst, alpha], axis=-1)
        
    return red_count, dst.astype(np.uint8)

# ----------------------------------------------------
# Main Public APIs
# ----------------------------------------------------
def get_library_status():
    """Returns details about C module compilation state."""
    return {
        "compiled": IS_COMPILED,
        "mode": "C-Shared-Library" if IS_COMPILED else "Python-NumPy-Fallback",
        "error": COMPILATION_ERROR
    }

def process_grayscale(image_path, save_path):
    """Converts image to grayscale."""
    t0 = time.perf_counter()
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    img_array = np.array(img)
    channels = img_array.shape[2]
    
    mode = "C-Library"
    if IS_COMPILED and C_LIB:
        try:
            # Flatten array and cast to ctypes pointer
            flat_data = img_array.ravel()
            c_array = flat_data.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            
            # Call C function
            C_LIB.convert_to_grayscale(c_array, width, height, channels)
            
            # Reconstruct image array
            processed_array = flat_data.reshape((height, width, channels))
        except Exception as e:
            print(f"[C Grayscale Error] {e}. Falling back to NumPy.")
            processed_array = _fallback_grayscale(img_array)
            mode = "Python-Fallback (NumPy)"
    else:
        processed_array = _fallback_grayscale(img_array)
        mode = "Python-Fallback (NumPy)"
        
    processed_img = Image.fromarray(processed_array)
    processed_img.save(save_path)
    
    duration = (time.perf_counter() - t0) * 1000
    return {
        "mode": mode,
        "time_ms": round(duration, 2)
    }

def process_sobel_edges(image_path, save_path):
    """Extracts image edges using Sobel filters."""
    t0 = time.perf_counter()
    
    # 1. Convert to grayscale first (as Sobel requires a grayscale base)
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    img_array = np.array(img)
    channels = img_array.shape[2]
    
    # Ensure source is grayscale
    gray_array = _fallback_grayscale(img_array)
    
    mode = "C-Library"
    if IS_COMPILED and C_LIB:
        try:
            # Prepare buffers
            src_flat = gray_array.ravel()
            dst_flat = np.zeros_like(src_flat)
            
            c_src = src_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            c_dst = dst_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            
            # Call C Sobel Edge detector
            C_LIB.detect_sobel_edges(c_src, c_dst, width, height, channels)
            
            processed_array = dst_flat.reshape((height, width, channels))
        except Exception as e:
            print(f"[C Sobel Error] {e}. Falling back to NumPy.")
            processed_array = _fallback_sobel(gray_array)
            mode = "Python-Fallback (NumPy)"
    else:
        processed_array = _fallback_sobel(gray_array)
        mode = "Python-Fallback (NumPy)"
        
    processed_img = Image.fromarray(processed_array)
    processed_img.save(save_path)
    
    duration = (time.perf_counter() - t0) * 1000
    return {
        "mode": mode,
        "time_ms": round(duration, 2)
    }

def process_redness_detection(image_path, save_path):
    """Isolates inflamed wound tissues and outputs red index counts."""
    t0 = time.perf_counter()
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    img_array = np.array(img)
    channels = img_array.shape[2]
    
    mode = "C-Library"
    red_count = 0
    
    if IS_COMPILED and C_LIB:
        try:
            src_flat = img_array.ravel()
            dst_flat = np.zeros_like(src_flat)
            
            c_src = src_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            c_dst = dst_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            
            # Call C redness profiling function
            red_count = C_LIB.detect_redness_pixels(c_src, c_dst, width, height, channels)
            
            processed_array = dst_flat.reshape((height, width, channels))
        except Exception as e:
            print(f"[C Redness Error] {e}. Falling back to NumPy.")
            red_count, processed_array = _fallback_redness(img_array)
            mode = "Python-Fallback (NumPy)"
    else:
        red_count, processed_array = _fallback_redness(img_array)
        mode = "Python-Fallback (NumPy)"
        
    processed_img = Image.fromarray(processed_array)
    processed_img.save(save_path)
    
    total_pixels = width * height
    redness_ratio = (red_count / total_pixels) * 100
    
    duration = (time.perf_counter() - t0) * 1000
    return {
        "red_pixel_count": red_count,
        "redness_ratio": round(redness_ratio, 2),
        "mode": mode,
        "time_ms": round(duration, 2)
    }
