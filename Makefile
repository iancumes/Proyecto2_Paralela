MPICC ?= mpicc
OPENSSL_PREFIX ?= $(shell if command -v brew >/dev/null 2>&1; then brew --prefix openssl@3; else echo /usr; fi)
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Wpedantic
CPPFLAGS += -I$(OPENSSL_PREFIX)/include
LDFLAGS += -L$(OPENSSL_PREFIX)/lib
LDLIBS += -lcrypto

.PHONY: all test clean
all: bin/bruteforce_mpi bin/mpi_probe

bin/mpi_probe: src/mpi_probe.c
	mkdir -p bin
	$(MPICC) $(CFLAGS) $< -o $@

bin/bruteforce_mpi: src/bruteforce_mpi.c
	mkdir -p bin
	$(MPICC) $(CPPFLAGS) $(CFLAGS) $< $(LDFLAGS) $(LDLIBS) -o $@

test: all
	python3 tests/verify.py

clean:
	rm -f bin/bruteforce_mpi bin/mpi_probe
