CC = gcc
CXX = g++
CFLAGS = -std=c11 -Wall -Wextra -Wvla -pedantic -O2
CXXFLAGS = -std=c++14 -Wall -Wextra -pedantic -O2

PRGS = test_eput_utils.exe

test_eput_utils.exe: test_eput_utils.o eput_utils.o
	$(CXX) $(CXXFLAGS) $^ -pthread -lgtest -lgtest_main -o $@

EPUT_PATH = ../src/eputgen/c/
eput_utils.o: $(EPUT_PATH)eput_utils.c $(EPUT_PATH)eput_utils.h
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	-/bin/rm -f *.o $(PRGS)

.PHONY: clean

.SUFFIXES: .o .c .cpp .h

%.o : %.c %.h
	$(CC) -c $(CFLAGS) $< -o $@

%.o : %.c
	$(CC) -c $(CFLAGS) $< -o $@

%.o : %.cpp
	$(CXX) -c $(CXXFLAGS) $< -o $@
