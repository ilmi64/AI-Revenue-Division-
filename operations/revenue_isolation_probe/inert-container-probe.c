#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <ifaddrs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>

static void fail(const char *check) {
    fprintf(stderr, "FAIL %s\n", check);
    exit(1);
}

static void denied(const char *path, int flags, const char *check) {
    int fd = open(path, flags, 0600);
    if (fd >= 0) {
        close(fd);
        fail(check);
    }
    if (errno != EACCES && errno != EPERM && errno != ENOENT && errno != EROFS) fail(check);
}

int main(int argc, char **argv) {
    struct rlimit limit;
    struct ifaddrs *addresses, *entry;
    char c;
    const char *proxies[] = {
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    };
    if ((argc != 2 && argc != 3) || getuid() != 65534 || getgid() != 65534) fail("unprivileged identity");
    for (size_t i = 0; i < sizeof(proxies)/sizeof(proxies[0]); i++) {
        const char *value = getenv(proxies[i]);
        if (value && *value) fail("empty proxies");
    }
    if (getrlimit(RLIMIT_NOFILE, &limit) || limit.rlim_cur != 64) fail("open-file limit");
    if (getrlimit(RLIMIT_FSIZE, &limit) || limit.rlim_cur != 65536) fail("output-size limit");
    if (getrlimit(RLIMIT_CORE, &limit) || limit.rlim_cur != 0) fail("core limit");
    int fd = open("/input", O_RDONLY);
    if (fd < 0 || read(fd, &c, 1) != 1 || c != 'A') fail("exact input mount");
    close(fd);
    denied("/input", O_WRONLY, "read-only input");
    denied("/outside", O_CREAT | O_WRONLY, "read-only root");
    denied(argv[1], O_RDONLY, "host canary unavailable");
    denied("/var/run/docker.sock", O_RDONLY, "daemon socket unavailable");
    denied("/workspace", O_RDONLY, "workspace unavailable");
    fd = open("/tmp/probe-write", O_CREAT | O_WRONLY, 0600);
    if (fd < 0 || write(fd, "ok", 2) != 2) fail("disposable scratch writable");
    close(fd);
    if (getifaddrs(&addresses) != 0) fail("read network interfaces");
    for (entry = addresses; entry; entry = entry->ifa_next) {
        if (strcmp(entry->ifa_name, "lo") != 0) fail("loopback-only interface inventory");
    }
    freeifaddrs(addresses);
    puts("PASS unprivileged identity, read-only input and root, invisible host canary and daemon, writable scratch, loopback only, cleared proxies, bounded files");
    if (argc == 3 && strcmp(argv[2], "test-timeout-cleanup") == 0) {
        int ready[2];
        if (pipe(ready) != 0) fail("child handshake pipe");
        pid_t child = fork();
        if (child < 0) fail("spawn inert child");
        if (child == 0) {
            close(ready[0]);
            if (setsid() == -1 || write(ready[1], "R", 1) != 1) _exit(3);
            for (;;) pause();
        }
        close(ready[1]);
        if (read(ready[0], &c, 1) != 1 || c != 'R') fail("independent child process group");
        puts("PASS inert process tree ready, including child in separate session");
        fflush(stdout);
        for (;;) pause();
    }
    if (argc == 3) {
        const rlim_t six_gib = 6ULL * 1024 * 1024 * 1024;
        struct rlimit memory = {six_gib, six_gib};
        struct rlimit tasks = {4, 4};
        if (strcmp(argv[2], "test-inherited-limits") == 0) {
            if (getrlimit(RLIMIT_AS, &limit) || limit.rlim_cur != six_gib || limit.rlim_max != six_gib)
                fail("inherited address-space limit");
            if (getrlimit(RLIMIT_NPROC, &limit) || limit.rlim_cur != 32 || limit.rlim_max != 32)
                fail("inherited task limit");
            if (getrlimit(RLIMIT_CPU, &limit) || limit.rlim_cur != 240 || limit.rlim_max != 240)
                fail("inherited CPU-time limit");
            puts("PASS trusted prlimit set inherited address-space, task and CPU-time limits across exec");
        } else if (setrlimit(RLIMIT_AS, &memory)) {
            fail("address-space limit setup");
        }
        void *mapping = mmap(NULL, six_gib, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (mapping != MAP_FAILED) {
            munmap(mapping, six_gib);
            fail("address-space limit enforcement");
        }
        if (errno != ENOMEM) fail("address-space refusal reason");
        puts("PASS in-process 6 GiB address-space limit denied over-limit virtual mapping");
        if (setrlimit(RLIMIT_NPROC, &tasks)) fail("task limit setup");
        pid_t children[4];
        int started = 0;
        for (int i = 0; i < 4; i++) {
            pid_t pid = fork();
            if (pid == 0) { pause(); _exit(0); }
            if (pid < 0) {
                if (errno != EAGAIN) fail("task refusal reason");
                break;
            }
            children[started++] = pid;
        }
        for (int i = 0; i < started; i++) {
            kill(children[i], SIGKILL);
            waitpid(children[i], NULL, 0);
        }
        if (started != 3) fail("task limit enforcement");
        puts("PASS task limit blocked the fourth child of a four-task sandbox");
    }
    return 0;
}
