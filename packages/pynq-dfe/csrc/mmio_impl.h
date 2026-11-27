// Shared implementation instantiated by each driver's shim translation unit.
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <metal/device.h>

struct mapping {
    DRIVER instance;  // First member so close can recover the owning allocation.
    struct metal_device device;
    void *mapped_pages;
    size_t mapped_size;
};

static int valid_args(const char *name, uint64_t base, uint64_t size)
{
    if (!name || !*name || strlen(name) >= sizeof(((DRIVER *)0)->NodeName) ||
        base % 4 || size < MIN_SIZE || size > SIZE_MAX ||
        base > INT64_MAX || size - 1 > INT64_MAX - base) {
        errno = EINVAL;
        return 0;
    }
    return 1;
}

static DRIVER *attach(const char *name, uint64_t base, size_t size, void *address,
                      void *pages, size_t mapped_size)
{
    struct mapping *map = calloc(1, sizeof(*map));
    if (!map)
        return NULL;
    DRIVER *inst = &map->instance;
    strcpy(inst->NodeName, name);
    map->device.name = inst->NodeName;
    map->device.num_regions = 1;
    inst->Config.BaseAddr = base;
    inst->Device = &map->device;
    inst->Io = &map->device.regions[0];
    metal_io_init(inst->Io, address, &inst->Config.BaseAddr, size, UINT_MAX, 0, NULL);
    map->mapped_pages = pages;
    map->mapped_size = mapped_size;
    load_config(inst);
    inst->StateId = READY;
    return inst;
}

DRIVER *OPEN(const char *name, uint64_t phys_base, uint64_t size)
{
    if (!valid_args(name, phys_base, size))
        return NULL;
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0)
        return NULL;
    size_t offset = phys_base % (unsigned long)page_size;
    size_t length = size + offset;
    int fd = open("/dev/mem", O_RDWR | O_SYNC | O_CLOEXEC);
    if (fd < 0)
        return NULL;
    void *pages = mmap(NULL, length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, phys_base - offset);
    int saved = errno;
    close(fd);
    if (pages == MAP_FAILED) {
        errno = saved;
        return NULL;
    }
    DRIVER *inst = attach(name, phys_base, size, (char *)pages + offset, pages, length);
    if (!inst) {
        saved = errno;
        munmap(pages, length);
        errno = saved;
    }
    return inst;
}

DRIVER *OPEN_BUFFER(const char *name, void *buffer, uint64_t size)
{
    if (!buffer || (uintptr_t)buffer % 4) {
        errno = EINVAL;
        return NULL;
    }
    if (!valid_args(name, 0, size))
        return NULL;
    return attach(name, 0, size, buffer, NULL, 0);
}

void CLOSE(DRIVER *inst)
{
    if (!inst)
        return;
    struct mapping *map = (struct mapping *)inst;
    metal_io_finish(inst->Io);
    if (map->mapped_size)
        munmap(map->mapped_pages, map->mapped_size);
    free(map);
}
