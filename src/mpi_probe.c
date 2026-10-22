#define _DEFAULT_SOURCE
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ifaddrs.h>
#include <arpa/inet.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size, n;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    char host[MPI_MAX_PROCESSOR_NAME], line[1024] = {0};
    MPI_Get_processor_name(host, &n);
    snprintf(line, sizeof(line), "rank=%d host=%s ipv4=", rank, host);
    struct ifaddrs *list = NULL;
    if (getifaddrs(&list) == 0) {
        for (struct ifaddrs *p = list; p; p = p->ifa_next) {
            if (!p->ifa_addr || p->ifa_addr->sa_family != AF_INET) continue;
            char ip[INET_ADDRSTRLEN];
            struct sockaddr_in *a = (struct sockaddr_in *)p->ifa_addr;
            if (!inet_ntop(AF_INET, &a->sin_addr, ip, sizeof(ip))) continue;
            size_t used = strlen(line);
            snprintf(line+used, sizeof(line)-used, "%s:%s;", p->ifa_name, ip);
        }
        freeifaddrs(list);
    }
    char *all = rank == 0 ? calloc((size_t)size, sizeof(line)) : NULL;
    if (rank == 0 && !all) MPI_Abort(MPI_COMM_WORLD, 1);
    MPI_Gather(line, sizeof(line), MPI_CHAR, all, sizeof(line), MPI_CHAR, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        for (int i=0; i<size; ++i) puts(all+(size_t)i*sizeof(line));
        free(all);
    }
    MPI_Finalize();
    return 0;
}
