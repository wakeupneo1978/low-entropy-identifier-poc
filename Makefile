CC ?= cc
CFLAGS ?= -O3 -Wall -Wextra -Wpedantic
OPENSSL_CFLAGS := $(shell pkg-config --cflags openssl 2>/dev/null)
OPENSSL_LIBS := $(shell pkg-config --libs openssl 2>/dev/null)
CPPFLAGS += $(OPENSSL_CFLAGS)
LDLIBS += $(if $(OPENSSL_LIBS),$(OPENSSL_LIBS),-lcrypto) -pthread

BUILD_DIR := build
TARGET := $(BUILD_DIR)/dni_sha256_enum
SOURCE := src/dni_sha256_enum.c

.PHONY: all clean test smoke

all: $(TARGET)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TARGET): $(SOURCE) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCE) -o $(TARGET) $(LDLIBS)
	@echo "Built $(TARGET) with POSIX threads"

test: $(TARGET)
	python3 -m unittest discover -s tests -v

smoke: $(TARGET)
	python3 src/generate_lab.py --output lab/synthetic_identity.db
	python3 src/run_reconstruction.py \
		--database lab/synthetic_identity.db \
		--cracker $(TARGET) \
		--output results/reconstruction_smoke.json \
		--limit 1000000 \
		--threads 2

clean:
	rm -f $(TARGET)
