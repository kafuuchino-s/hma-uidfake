/* SPDX-License-Identifier: GPL-2.0 */
/* Single normal kernel load attempt; no ELF, symbol or metadata modification. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    struct stat info;
    int fd, saved_errno;
    long result;
    if (argc != 2) {
        fprintf(stderr, "usage: load-ko MODULE.ko\n");
        return 2;
    }
    if (geteuid() != 0) {
        fprintf(stderr, "load-ko requires the owner's existing root shell\n");
        return 1;
    }
    fd = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) { perror("open module"); return 1; }
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode)) {
        fprintf(stderr, "module must be a readable regular file\n");
        close(fd);
        return 1;
    }
    result = syscall(__NR_finit_module, fd, "", 0);
    saved_errno = errno;
    close(fd);
    if (result != 0) {
        fprintf(stderr, "finit_module flags=0: %s (errno=%d)\n",
                strerror(saved_errno), saved_errno);
        return 1;
    }
    puts("finit_module flags=0 succeeded; inspect KAUX_STATUS before applying rules");
    return 0;
}
