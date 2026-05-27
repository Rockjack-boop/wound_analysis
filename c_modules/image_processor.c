// Forward declaration to clear linter warnings when math.h headers are missing on local includes path.
// The linker will automatically bind this to the standard math library at compile time.
float sqrtf(float x);

/**
 * Grayscale Conversion
 * Converts a multi-channel RGB/RGBA image to grayscale in-place.
 * 
 * @param pixels   Pointer to the image pixel array.
 * @param width    Width of the image in pixels.
 * @param height   Height of the image in pixels.
 * @param channels Number of channels (3 for RGB, 4 for RGBA).
 */
void convert_to_grayscale(unsigned char* pixels, int width, int height, int channels) {
    if (!pixels || width <= 0 || height <= 0 || channels < 3) return;

    int total_pixels = width * height;
    for (int i = 0; i < total_pixels; i++) {
        int idx = i * channels;
        unsigned char r = pixels[idx];
        unsigned char g = pixels[idx + 1];
        unsigned char b = pixels[idx + 2];
        
        // Standard NTSC/PAL luminance weighting
        unsigned char gray = (unsigned char)(0.299f * r + 0.587f * g + 0.114f * b);
        
        pixels[idx] = gray;
        pixels[idx + 1] = gray;
        pixels[idx + 2] = gray;
        // Keep the alpha channel (index idx + 3) unmodified if RGBA
    }
}

/**
 * Sobel Edge Detection
 * Computes image gradients in x and y directions to find edges.
 * Requires src buffer to be grayscale first, and dst buffer to be pre-allocated.
 * 
 * @param src      Pointer to source grayscale image pixel array.
 * @param dst      Pointer to destination buffer to store the edge map.
 * @param width    Width of the image.
 * @param height   Height of the image.
 * @param channels Number of channels (3 or 4).
 */
void detect_sobel_edges(const unsigned char* src, unsigned char* dst, int width, int height, int channels) {
    if (!src || !dst || width <= 2 || height <= 2 || channels < 3) return;

    // Zero out the margins of dst
    int bytes_per_row = width * channels;
    for (int x = 0; x < width; x++) {
        // Top and bottom rows
        int top_idx = x * channels;
        int bot_idx = (height - 1) * bytes_per_row + x * channels;
        for (int c = 0; c < channels; c++) {
            dst[top_idx + c] = 0;
            dst[bot_idx + c] = 0;
        }
    }
    for (int y = 0; y < height; y++) {
        // Left and right columns
        int left_idx = y * bytes_per_row;
        int right_idx = y * bytes_per_row + (width - 1) * channels;
        for (int c = 0; c < channels; c++) {
            dst[left_idx + c] = 0;
            dst[right_idx + c] = 0;
        }
    }

    // Process internal pixels
    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            float gx = 0;
            float gy = 0;

            // Convolution using 3x3 Sobel kernels:
            // Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
            // Gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
            for (int ky = -1; ky <= 1; ky++) {
                for (int kx = -1; kx <= 1; kx++) {
                    int pixel_x = x + kx;
                    int pixel_y = y + ky;
                    int src_idx = (pixel_y * width + pixel_x) * channels;
                    
                    // Since it is a grayscale image, red/green/blue are identical.
                    // We extract the intensity value from the red channel.
                    int intensity = src[src_idx];

                    // Compute weights using simple logical checks instead of stdlib abs()
                    // Since ky and kx are bounded in [-1, 1], abs(k) == 1 is identical to k != 0.
                    int weight_x = kx * (ky != 0 ? 1 : 2);
                    int weight_y = ky * (kx != 0 ? 1 : 2);

                    gx += intensity * weight_x;
                    gy += intensity * weight_y;
                }
            }

            // Compute gradient magnitude
            float mag = sqrtf(gx * gx + gy * gy);
            unsigned char edge_value = (mag > 255.0f) ? 255 : (unsigned char)mag;

            int dst_idx = (y * width + x) * channels;
            dst[dst_idx] = edge_value;
            dst[dst_idx + 1] = edge_value;
            dst[dst_idx + 2] = edge_value;
            if (channels == 4) {
                dst[dst_idx + 3] = src[dst_idx + 3]; // Preserve alpha channel
            }
        }
    }
}

/**
 * Redness Detection (Infection/Inflammation Profiler)
 * Filters pixels, highlighting those with severe redness, while converting
 * other parts to a dark grayscale backdrop for clear medical visual mapping.
 * Returns the total count of highly inflamed pixels.
 * 
 * @param pixels       Pointer to the original RGB/RGBA image pixel array.
 * @param dst_filtered Pointer to pre-allocated buffer for saving the redness visualization.
 * @param width        Width of the image.
 * @param height       Height of the image.
 * @param channels     Number of channels (3 or 4).
 * @return             Count of pixels identified as highly red/inflamed.
 */
int detect_redness_pixels(const unsigned char* pixels, unsigned char* dst_filtered, int width, int height, int channels) {
    if (!pixels || !dst_filtered || width <= 0 || height <= 0 || channels < 3) return 0;

    int red_pixel_count = 0;
    int total_pixels = width * height;

    for (int i = 0; i < total_pixels; i++) {
        int idx = i * channels;
        unsigned char r = pixels[idx];
        unsigned char g = pixels[idx + 1];
        unsigned char b = pixels[idx + 2];

        // An inflammation pixel is defined as:
        // 1. Minimum Red component of 120 (prominent color)
        // 2. Red channel is at least 1.25x larger than Green channel
        // 3. Red channel is at least 1.25x larger than Blue channel
        if (r > 120 && r > (unsigned char)(g * 1.25f) && r > (unsigned char)(b * 1.25f)) {
            red_pixel_count++;
            
            // Highlight with vivid red in the visual output map
            dst_filtered[idx] = r;
            dst_filtered[idx + 1] = 0;
            dst_filtered[idx + 2] = 0;
        } else {
            // Convert background/non-inflamed pixels to low-contrast dark grayscale
            unsigned char gray = (unsigned char)(0.299f * r + 0.587f * g + 0.114f * b);
            unsigned char dark_gray = gray / 3; // Muted grayscale background
            dst_filtered[idx] = dark_gray;
            dst_filtered[idx + 1] = dark_gray;
            dst_filtered[idx + 2] = dark_gray;
        }

        if (channels == 4) {
            dst_filtered[idx + 3] = pixels[idx + 3]; // Preserve alpha channel
        }
    }

    return red_pixel_count;
}
