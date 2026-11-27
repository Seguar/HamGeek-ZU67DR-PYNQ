// LD_PRELOAD fixture for tests only. Redirect /dev/mem to a regular sparse file.
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

int open(const char *path, int flags, ...)
{
    mode_t mode = 0;
    if ((flags & O_CREAT) || (flags & O_TMPFILE) == O_TMPFILE) {
        va_list args;
        va_start(args, flags);
        mode = va_arg(args, mode_t);
        va_end(args);
    }
    if (!strcmp(path, "/dev/mem"))
        path = getenv("DFE_TEST_FILE");
    return openat(AT_FDCWD, path, flags, mode);
}
