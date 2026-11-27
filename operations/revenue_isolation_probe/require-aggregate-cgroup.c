#include <stdio.h>
#include <string.h>
#include <unistd.h>

static int matches(const char *path, const char *expected) {
    char value[80];
    FILE *file = fopen(path, "r");
    if (!file) return 0;
    int match = fgets(value, sizeof(value), file) && !strcmp(value, expected);
    if (fclose(file)) return 0;
    return match;
}

int main(int argc, char **argv) {
    if (argc < 2 ||
        !matches("/proc/self/cgroup", "0::/\n") ||
        !matches("/sys/fs/cgroup/cpu.max", "200000 100000\n") ||
        !matches("/sys/fs/cgroup/memory.max", "6442450944\n") ||
        !matches("/sys/fs/cgroup/memory.swap.max", "0\n") ||
        !matches("/sys/fs/cgroup/pids.max", "32\n")) {
        fputs("Aggregate pilot controls unavailable, refusing workload\n", stderr);
        return 125;
    }
    fputs("Aggregate pilot controls read back before workload\n", stderr);
    execv(argv[1], &argv[1]);
    perror("Cannot exec the approved pilot entrypoint");
    return 125;
}
