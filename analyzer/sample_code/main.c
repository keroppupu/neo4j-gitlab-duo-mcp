#include <stdio.h>
#include "db_utils.h"
#include "calculator.h"

int process_data(int input) {
    init_db();
    int result = add(input, 100);
    close_db();
    return result;
}

int main() {
    printf("Starting application...\n");
    int val = process_data(10);
    return 0;
}
