#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <hidapi/hidapi.h>
#include <unistd.h>

#define VID 0x194e
#define PID 0x1014
#define REPORT_SIZE 64

void print_hex(unsigned char *buf, int len) {
    for (int i = 0; i < len; i++) {
        if (i > 0 && i % 16 == 0) printf("\n    ");
        printf("%02x ", buf[i]);
    }
    printf("\n");
}

void probe_command(hid_device *handle, unsigned char cmd_id) {
    unsigned char buf[REPORT_SIZE];
    memset(buf, 0, REPORT_SIZE);
    
    // Construct packet: [CMD_ID] [SUB_CMD/DUMMY] [PADDING...]
    buf[0] = cmd_id; 
    buf[1] = 0x00; // Try generic sub-command 0

    printf("[-] Probing Command ID: 0x%02x... ", cmd_id);
    
    if (hid_write(handle, buf, REPORT_SIZE) == -1) {
        printf("Write Error\n");
        return;
    }

    // Wait briefly for a response
    memset(buf, 0, REPORT_SIZE);
    int res = hid_read_timeout(handle, buf, REPORT_SIZE, 200); // 200ms timeout

    if (res > 0) {
        printf("RESPONSE RECEIVED!\n    ");
        print_hex(buf, 16); // Print first 16 bytes
        
        // Check for ASCII strings (firmware version)
        if (cmd_id == 0x01 || cmd_id == 0x02) {
             printf("    ASCII Hint: %c%c%c%c\n", 
                    (buf[2] > 31 && buf[2] < 127) ? buf[2] : '.',
                    (buf[3] > 31 && buf[3] < 127) ? buf[3] : '.',
                    (buf[4] > 31 && buf[4] < 127) ? buf[4] : '.',
                    (buf[5] > 31 && buf[5] < 127) ? buf[5] : '.');
        }
    } else {
        printf("No response.\n");
    }
}

int main() {
    if (hid_init()) return -1;

    hid_device *handle = hid_open(VID, PID, NULL);
    if (!handle) {
        printf("Unable to open device. Try running with 'sudo'.\n");
        printf("Check VID/PID with 'lsusb' if different from %04x:%04x\n", VID, PID);
        return 1;
    }

    printf("Scanning ScioSense PicoProg Protocol...\n");
    printf("---------------------------------------\n");

    // Scan common ScioSense Command IDs
    // 0x01: Usually System/Info
    // 0x02: Usually SPI/I2C Access
    // 0x10: Alternative legacy access
    // 0xA1: Common 'Get Report'
    unsigned char candidates[] = {0x01, 0x02, 0x03, 0x04, 0x10, 0x20, 0xA1, 0xAA};
    
    for (int i = 0; i < 8; i++) {
        probe_command(handle, candidates[i]);
        usleep(100000); // Sleep 100ms between probes
    }

    hid_close(handle);
    hid_exit();
    return 0;
}