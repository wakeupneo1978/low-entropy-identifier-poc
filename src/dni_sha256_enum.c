#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#define _POSIX_C_SOURCE 200809L

#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <openssl/sha.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#ifdef __APPLE__
#include <sys/types.h>
#include <sys/sysctl.h>
#endif

#define DIGEST_LEN SHA256_DIGEST_LENGTH
#define HEX_LEN (DIGEST_LEN * 2)
#define DNI_LEN 9
#define MAX_TARGETS 4096
#define MAX_SALT_LEN 1024
#define MAX_THREADS 256
#define DNI_DOMAIN 100000000ULL

static const char CONTROL_LETTERS[] = "TRWAGMYFPDXBNJZSQVHLCKE";

typedef struct {
    unsigned char digest[DIGEST_LEN];
    char hex[HEX_LEN + 1];
    bool found;
    uint32_t number;
} target_t;

typedef struct {
    const char *targets_path;
    uint64_t limit;
    const char *salt;
    size_t salt_len;
    int threads;
} options_t;

typedef struct {
    uint64_t start;
    uint64_t end;
    const options_t *options;
    target_t *targets;
    size_t target_count;
    pthread_mutex_t *target_mutex;
} worker_context_t;

static void usage(const char *program) {
    fprintf(
        stderr,
        "Usage: %s --targets FILE [--limit N] [--salt ASCII] [--threads N]\n"
        "\n"
        "Enumerates syntactically valid Spanish DNI/NIF candidates in the\n"
        "canonical form 00000000T..99999999R and matches SHA-256 digests.\n"
        "The hashed byte string is either DNI or SALT||DNI.\n",
        program
    );
}

static bool parse_u64(const char *text, uint64_t *value) {
    char *end = NULL;
    errno = 0;
    unsigned long long parsed = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        return false;
    }
    *value = (uint64_t)parsed;
    return true;
}

static bool parse_options(int argc, char **argv, options_t *options) {
    options->targets_path = NULL;
    options->limit = DNI_DOMAIN;
    options->salt = "";
    options->salt_len = 0;
#if defined(__APPLE__)
    int detected_threads = 1;
    size_t detected_threads_size = sizeof(detected_threads);
    if (sysctlbyname(
            "hw.logicalcpu",
            &detected_threads,
            &detected_threads_size,
            NULL,
            0
        ) != 0) {
        detected_threads = 1;
    }
#elif defined(_SC_NPROCESSORS_ONLN)
    long detected_threads = sysconf(_SC_NPROCESSORS_ONLN);
#else
    long detected_threads = 1;
#endif
    options->threads =
        detected_threads > 0 && detected_threads <= MAX_THREADS
            ? (int)detected_threads
            : 1;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--targets") == 0 && i + 1 < argc) {
            options->targets_path = argv[++i];
        } else if (strcmp(argv[i], "--limit") == 0 && i + 1 < argc) {
            if (!parse_u64(argv[++i], &options->limit)) {
                return false;
            }
        } else if (strcmp(argv[i], "--salt") == 0 && i + 1 < argc) {
            options->salt = argv[++i];
            options->salt_len = strlen(options->salt);
            if (options->salt_len > MAX_SALT_LEN) {
                fprintf(stderr, "Salt exceeds %d bytes\n", MAX_SALT_LEN);
                return false;
            }
        } else if (strcmp(argv[i], "--threads") == 0 && i + 1 < argc) {
            uint64_t parsed_threads = 0;
            if (!parse_u64(argv[++i], &parsed_threads) ||
                parsed_threads == 0 ||
                parsed_threads > MAX_THREADS) {
                return false;
            }
            options->threads = (int)parsed_threads;
        } else if (strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            exit(0);
        } else {
            return false;
        }
    }

    if (options->targets_path == NULL || options->limit > DNI_DOMAIN) {
        return false;
    }
    return true;
}

static int hex_nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    c = (char)tolower((unsigned char)c);
    if (c >= 'a' && c <= 'f') return 10 + (c - 'a');
    return -1;
}

static bool parse_digest(const char *hex, unsigned char digest[DIGEST_LEN]) {
    if (strlen(hex) != HEX_LEN) return false;
    for (size_t i = 0; i < DIGEST_LEN; ++i) {
        int high = hex_nibble(hex[i * 2]);
        int low = hex_nibble(hex[i * 2 + 1]);
        if (high < 0 || low < 0) return false;
        digest[i] = (unsigned char)((high << 4) | low);
    }
    return true;
}

static size_t load_targets(const char *path, target_t targets[MAX_TARGETS]) {
    FILE *stream = fopen(path, "r");
    if (stream == NULL) {
        perror("Unable to open target file");
        exit(2);
    }

    size_t count = 0;
    char line[256];
    size_t line_no = 0;
    while (fgets(line, sizeof(line), stream) != NULL) {
        ++line_no;
        char *start = line;
        while (isspace((unsigned char)*start)) ++start;
        char *end = start + strlen(start);
        while (end > start && isspace((unsigned char)end[-1])) --end;
        *end = '\0';
        if (*start == '\0' || *start == '#') continue;
        if (count >= MAX_TARGETS) {
            fprintf(stderr, "Too many targets; maximum is %d\n", MAX_TARGETS);
            fclose(stream);
            exit(2);
        }
        if (!parse_digest(start, targets[count].digest)) {
            fprintf(stderr, "Invalid SHA-256 digest on line %zu\n", line_no);
            fclose(stream);
            exit(2);
        }
        memcpy(targets[count].hex, start, HEX_LEN);
        targets[count].hex[HEX_LEN] = '\0';
        targets[count].found = false;
        targets[count].number = 0;
        ++count;
    }
    fclose(stream);
    if (count == 0) {
        fprintf(stderr, "No target hashes found\n");
        exit(2);
    }
    return count;
}

static inline void format_dni(uint32_t number, unsigned char output[DNI_LEN]) {
    uint32_t remaining = number;
    for (int position = 7; position >= 0; --position) {
        output[position] = (unsigned char)('0' + (remaining % 10U));
        remaining /= 10U;
    }
    output[8] = (unsigned char)CONTROL_LETTERS[number % 23U];
}

static double elapsed_seconds(struct timespec start, struct timespec end) {
    return (double)(end.tv_sec - start.tv_sec) +
           (double)(end.tv_nsec - start.tv_nsec) / 1000000000.0;
}

static void print_json_string(const char *text) {
    putchar('"');
    for (const unsigned char *p = (const unsigned char *)text; *p; ++p) {
        if (*p == '"' || *p == '\\') {
            putchar('\\');
            putchar((int)*p);
        } else if (*p >= 0x20) {
            putchar((int)*p);
        }
    }
    putchar('"');
}

static void *enumerate_range(void *raw_context) {
    worker_context_t *context = (worker_context_t *)raw_context;
    unsigned char candidate[DNI_LEN];
    unsigned char input[MAX_SALT_LEN + DNI_LEN];
    unsigned char digest[DIGEST_LEN];
    if (context->options->salt_len > 0) {
        memcpy(
            input,
            context->options->salt,
            context->options->salt_len
        );
    }

    for (uint64_t raw = context->start; raw < context->end; ++raw) {
        uint32_t number = (uint32_t)raw;
        format_dni(number, candidate);
        const unsigned char *message = candidate;
        size_t message_len = DNI_LEN;
        if (context->options->salt_len > 0) {
            memcpy(
                input + context->options->salt_len,
                candidate,
                DNI_LEN
            );
            message = input;
            message_len = context->options->salt_len + DNI_LEN;
        }
        SHA256(message, message_len, digest);

        for (size_t i = 0; i < context->target_count; ++i) {
            if (memcmp(
                    digest,
                    context->targets[i].digest,
                    DIGEST_LEN
                ) == 0) {
                pthread_mutex_lock(context->target_mutex);
                if (!context->targets[i].found) {
                    context->targets[i].found = true;
                    context->targets[i].number = number;
                }
                pthread_mutex_unlock(context->target_mutex);
            }
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    options_t options;
    if (!parse_options(argc, argv, &options)) {
        usage(argv[0]);
        return 2;
    }

    target_t targets[MAX_TARGETS];
    size_t target_count = load_targets(options.targets_path, targets);

    int threads = options.threads;

    struct timespec started;
    struct timespec finished;
    clock_gettime(CLOCK_MONOTONIC, &started);

    pthread_mutex_t target_mutex;
    if (pthread_mutex_init(&target_mutex, NULL) != 0) {
        fprintf(stderr, "Unable to initialize mutex\n");
        return 2;
    }

    pthread_t *thread_ids = calloc((size_t)threads, sizeof(*thread_ids));
    worker_context_t *contexts = calloc((size_t)threads, sizeof(*contexts));
    if (thread_ids == NULL || contexts == NULL) {
        fprintf(stderr, "Unable to allocate thread state\n");
        free(thread_ids);
        free(contexts);
        pthread_mutex_destroy(&target_mutex);
        return 2;
    }

    int created_threads = 0;
    for (int i = 0; i < threads; ++i) {
        contexts[i].start = options.limit * (uint64_t)i / (uint64_t)threads;
        contexts[i].end =
            options.limit * (uint64_t)(i + 1) / (uint64_t)threads;
        contexts[i].options = &options;
        contexts[i].targets = targets;
        contexts[i].target_count = target_count;
        contexts[i].target_mutex = &target_mutex;
        int status = pthread_create(
            &thread_ids[i],
            NULL,
            enumerate_range,
            &contexts[i]
        );
        if (status != 0) {
            fprintf(stderr, "Unable to create worker thread %d\n", i);
            for (int j = 0; j < created_threads; ++j) {
                pthread_join(thread_ids[j], NULL);
            }
            free(thread_ids);
            free(contexts);
            pthread_mutex_destroy(&target_mutex);
            return 2;
        }
        ++created_threads;
    }
    for (int i = 0; i < created_threads; ++i) {
        pthread_join(thread_ids[i], NULL);
    }
    free(thread_ids);
    free(contexts);
    pthread_mutex_destroy(&target_mutex);

    clock_gettime(CLOCK_MONOTONIC, &finished);
    double seconds = elapsed_seconds(started, finished);
    double rate = seconds > 0.0 ? (double)options.limit / seconds : 0.0;

    size_t found_count = 0;
    for (size_t i = 0; i < target_count; ++i) {
        if (targets[i].found) ++found_count;
    }

    printf("{\n");
    printf("  \"candidate_format\": \"eight_digits_plus_mod23_letter\",\n");
    printf("  \"hash_input\": ");
    print_json_string(options.salt_len > 0 ? "salt_ascii_concatenated_with_dni" : "dni");
    printf(",\n");
    printf("  \"salt_length_bytes\": %zu,\n", options.salt_len);
    printf("  \"candidate_limit\": %" PRIu64 ",\n", options.limit);
    printf("  \"target_count\": %zu,\n", target_count);
    printf("  \"found_count\": %zu,\n", found_count);
    printf("  \"threads\": %d,\n", threads);
    printf("  \"elapsed_seconds\": %.9f,\n", seconds);
    printf("  \"hashes_per_second\": %.3f,\n", rate);
    printf("  \"matches\": [\n");

    bool first = true;
    for (size_t i = 0; i < target_count; ++i) {
        if (!targets[i].found) continue;
        unsigned char dni[DNI_LEN];
        char dni_text[DNI_LEN + 1];
        format_dni(targets[i].number, dni);
        memcpy(dni_text, dni, DNI_LEN);
        dni_text[DNI_LEN] = '\0';
        if (!first) printf(",\n");
        printf("    {\"sha256\": \"%s\", \"dni\": \"%s\"}", targets[i].hex, dni_text);
        first = false;
    }
    if (!first) printf("\n");
    printf("  ]\n");
    printf("}\n");

    return 0;
}
