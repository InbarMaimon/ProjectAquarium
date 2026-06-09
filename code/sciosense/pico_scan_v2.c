/*
 * pico_scan.c — Instrumented HID probe for ScioSense PicoProg
 * VID: 0x194e  PID: 0x1014
 *
 * Compile:
 *   gcc pico_scan.c -o pico_scan -lhidapi-hidraw
 *   (or -lhidapi-libusb if you prefer the libusb backend)
 *
 * Run:
 *   sudo ./pico_scan 2>&1 | tee pico_scan.log
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <hidapi/hidapi.h>
#include <unistd.h>

#define VID         0x194e
#define PID         0x1014
#define PAYLOAD     64      /* descriptor-declared report size */
#define BUFSIZE     65      /* +1 for the report-ID prefix byte */
#define CHARSIZE    256

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static void print_hex(const char *label, unsigned char *buf, int len) {
    printf("  %s (%d bytes):\n    ", label, len);
    for (int i = 0; i < len; i++) {
        if (i > 0 && i % 16 == 0) printf("\n    ");
        printf("%02x ", buf[i]);
    }
    printf("\n");

    /* ASCII side-channel — shows printable chars inline */
    printf("  ASCII: [");
    for (int i = 0; i < len && i < 32; i++)
        printf("%c", (buf[i] >= 0x20 && buf[i] < 0x7f) ? buf[i] : '.');
    printf("]\n");
}

/* ------------------------------------------------------------------ */
/* Single probe: tries one command ID with a given report-ID offset    */
/* ------------------------------------------------------------------ */

static void probe(hid_device *handle,
                  unsigned char report_id,   /* usually 0x00          */
                  unsigned char cmd,
                  unsigned char sub,
                  int timeout_ms)
{
    unsigned char buf[BUFSIZE];
    memset(buf, 0, BUFSIZE);

    buf[0] = report_id;   /* hidraw prepends this; firmware never sees it */
    buf[1] = cmd;
    buf[2] = sub;
    /* bytes 3..64 stay 0 */

    printf("\n[>] CMD=0x%02x SUB=0x%02x  (report_id=0x%02x)\n",
           cmd, sub, report_id);

    int w = hid_write(handle, buf, BUFSIZE);
    printf("    hid_write  => %d", w);
    if (w < 0) {
        printf("  ERROR: %ls\n", hid_error(handle));
        return;
    }
    printf("  (ok)\n");

    memset(buf, 0, BUFSIZE);
    int r = hid_read_timeout(handle, buf, BUFSIZE, timeout_ms);
    printf("    hid_read   => %d", r);
    if (r < 0) {
        printf("  ERROR: %ls\n", hid_error(handle));
        return;
    }
    if (r == 0) {
        printf("  (timeout — no data)\n");
        return;
    }

    printf("  *** RESPONSE ***\n");
    print_hex("RX", buf, r);

    /*
     * Heuristic checks on the response:
     *  - byte 0 or 1 echoing the command → framing confirmed
     *  - all zeros → device acknowledged but returned empty frame
     *  - non-zero status at fixed offset → look for error codes
     */
    if (buf[0] == cmd || buf[1] == cmd)
        printf("  [!] Command byte echoed — framing likely correct\n");
    if (buf[0] == 0x00 && buf[1] == 0x00)
        printf("  [?] First two bytes are 0 — may be empty ACK\n");
}

/* ------------------------------------------------------------------ */
/* Ascending-pattern frame — helps detect echo / offset misalignment  */
/* ------------------------------------------------------------------ */

static void pattern_test(hid_device *handle) {
    unsigned char buf[BUFSIZE];
    printf("\n[>] Pattern test (0x00..0x3f ascending)\n");
    buf[0] = 0x00;   /* report ID */
    for (int i = 1; i < BUFSIZE; i++)
        buf[i] = (unsigned char)(i - 1);   /* payload: 0x00 0x01 ... 0x3f */

    int w = hid_write(handle, buf, BUFSIZE);
    printf("    hid_write  => %d\n", w);

    memset(buf, 0, BUFSIZE);
    int r = hid_read_timeout(handle, buf, BUFSIZE, 500);
    printf("    hid_read   => %d\n", r);
    if (r > 0) print_hex("RX", buf, r);
}

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */

int main(void) {
    if (hid_init()) {
        fprintf(stderr, "hid_init() failed\n");
        return 1;
    }

    printf("=== ScioSense PicoProg HID probe  VID=%04x PID=%04x ===\n\n",
           VID, PID);

    hid_device *handle = hid_open(VID, PID, NULL);
    if (!handle) {
        fprintf(
            stderr,
            "Cannot open device.\n"
        );
        hid_exit();
        return 1;
    }

    /* Print manufacturer / product strings for sanity-check */
    wchar_t wbuf[256];
    if (hid_get_manufacturer_string(handle, wbuf, 256) == 0)
        printf("Manufacturer : %ls\n", wbuf);
    if (hid_get_product_string(handle, wbuf, 256) == 0)
        printf("Product      : %ls\n", wbuf);
    if (hid_get_serial_number_string(handle, wbuf, 256) == 0)
        printf("Serial       : %ls\n", wbuf);

    printf("\n--- Phase 1: 65-byte probes (report-ID prefix = 0x00) ---");

    for (int i = 0; i < CHARSIZE; i++) {
        probe(handle, 0x00, i, 0x00, 500);
        usleep(150000);
    }

    // printf("\n--- Phase 2: Ascending-pattern frame ---\n");
    // pattern_test(handle);

    // printf("\n--- Phase 3: Sub-command sweep for CMD=0x01 ---\n");
    // /*
    //  * If 0x01 is the info/system command, sub-commands 0x00–0x07
    //  * may select firmware version, hardware rev, serial, etc.
    //  */
    // for (unsigned char sub = 0x00; sub <= 0x07; sub++) {
    //     probe(handle, 0x00, 0x01, sub, 400);
    //     usleep(100000);
    // }

    // printf("\n=== Scan complete ===\n");
    // printf("Save this output and look for:\n");
    // printf("  • Any read => > 0   (proof of response)\n");
    // printf("  • Echoed command bytes in RX\n");
    // printf("  • Non-zero bytes at consistent offsets across responses\n");
    // printf("  • ASCII strings (firmware version, 'OK', 'ACK', etc.)\n\n");

    // hid_close(handle);
    // hid_exit();
    return 0;
}