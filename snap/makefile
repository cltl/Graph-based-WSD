CXX=g++
PYTHON_INC=$(shell pkg-config --cflags python3)
PYTHON_LIBS=$(shell pkg-config --libs python3)
CXX_INC=-Isnap-lib/snap-core -Isnap-lib/glib-core
CXX_LIBS=-Lsnap-lib/snap-core
LIBS=-lsnap
FLAGS=-std=c++11 --shared

all:
	$(CXX) $(FLAGS) $(CXX_INC) $(PYTHON_INC) $(PYTHON_LIBS) $(CXX_LIBS) $(LIBS) ppr.cpp -o ppr.so
