/*
 * setuid_exec.c — Execute a command as a different UID
 * Usage: setuid_exec <uid> <gid> <command> [args...]
 * Must run as root to setuid/setgid.
 *
 * Cross-compile: aarch64-linux-gnu-gcc -static -o setuid_exec setuid_exec.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <uid> <gid> <command> [args...]\n", argv[0]);
        return 1;
    }

    uid_t uid = (uid_t)atoi(argv[1]);
    gid_t gid = (gid_t)atoi(argv[2]);

    if (setgid(gid) != 0) {
        perror("setgid");
        return 1;
    }
    if (setuid(uid) != 0) {
        perror("setuid");
        return 1;
    }

    /* Execute the command */
    execvp(argv[3], &argv[3]);
    perror("execvp");
    return 1;
}
