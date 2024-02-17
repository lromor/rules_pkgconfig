#include <png.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#define PNG_SUCCESS            0
#define PNG_ERR_INVALID_HEADER 1
#define PNG_ERR_INIT           2

int read_png(FILE * fp) {
  char header[8];
  fread(header, 1, 8, fp);

  // File header check
  if (png_sig_cmp((png_const_bytep)header, 0, 8) != 0) { return PNG_ERR_INVALID_HEADER; }

  png_structp png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  png_infop info_ptr = png_create_info_struct(png_ptr);

  // Library-internal safeguards
  if (!info_ptr) { png_destroy_read_struct(&png_ptr, NULL, NULL); return PNG_ERR_INIT; }
  if (setjmp(png_jmpbuf(png_ptr))) { png_destroy_read_struct(&png_ptr, &info_ptr, NULL); return PNG_ERR_INIT; }

  png_init_io(png_ptr, fp);

  png_set_sig_bytes(png_ptr, 8);

  png_read_png(png_ptr, info_ptr, PNG_TRANSFORM_IDENTITY, NULL);


  unsigned int h, w, i, j, k, bpc, nc;
  fprintf(stdout, "PNG Image: width = %u, height = %u, %u b/channel in %u channels. Dumping data.\n",
          w   = png_get_image_width(png_ptr, info_ptr),
          h   = png_get_image_height(png_ptr, info_ptr),
          bpc = png_get_bit_depth(png_ptr, info_ptr),
          nc  = png_get_channels(png_ptr, info_ptr)
          );

  png_bytep * row_pointers = png_get_rows(png_ptr, info_ptr);

  // ASCII or hex dump; ASCII if 3 or more channels, hex dump otherwise.
  // Only applicable for 8 bit per channel, otherwise we skip this step.
  if (bpc == 8) for (i = 0; i < h; ++i)
                {
                  fprintf(stdout, "Row %3u:", i);

                  for (j = 0; j < w; ++j)
                  {

                    if (nc >= 3)
                    {
                      unsigned int av = row_pointers[i][nc * j] + row_pointers[i][nc * j + 1] + row_pointers[i][nc * j + 2];
                      char x;
                      if      (av < 100) x = ' ';
                      else if (av < 300) x = '.';
                      else if (av < 550) x = '*';
                      else               x = '#';
                      fputc(x, stdout);
                    }
                    else
                    {
                      fputs(" [", stdout);
                      for (k = 0; k < nc; ++k)
                      {
                        if (k != 0) fputc(' ', stdout);
                        fprintf(stdout, "%02X", row_pointers[i][nc * j + k]);
                      }
                      fputc(']', stdout);
                    }
                  }

                  fputc('\n', stdout);
                }

  png_destroy_read_struct(&png_ptr, &info_ptr, NULL);

  return 0;
}

int main(int argc, char * argv[])
{
  if (argc != 2)
  {
    fputs("Usage: p filename.png\n", stderr);
    return 1;
  }

  FILE * fp = fopen(argv[1], "rb");

  if (!fp)
  {
    fprintf(stderr, "Error opening file '%s' (error %u: %s).\n", argv[1], errno, strerror(errno));
    return 1;
  }

  int pr = read_png(fp);

  fclose(fp);

  if (pr != PNG_SUCCESS)
  {
    fprintf(stderr, "Error while processing file (error %d).\n", pr);
    return 1;
  }

  return 0;
}
