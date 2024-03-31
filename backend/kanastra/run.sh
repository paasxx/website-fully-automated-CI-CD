#!/bin/bash

# Set execute permission for the script
chmod +x run.sh

# Function to display styled text
print_styled() {
    printf "\e[1;36m$1\e[0m\n"  # Cyan text
}

# Function to display separator
print_separator() {
    printf "========================================\n"
}

# Function to display loading animation
print_loading() {
    local delay=1
    local spinner="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"  # Spinner characters
    while true; do
        printf "\e[1;32m%s\e[0m\b" "${spinner}"  # Green text
        spinner="${spinner:1}${spinner:0:1}"  # Rotate spinner
        sleep "${delay}"
    done
}

# Run migrations
print_separator
print_styled "Running Migrations:"
print_loading &
loading_pid=$!
python manage.py makemigrations
python manage.py migrate
kill ${loading_pid}  # Stop the loading animation
print_separator

# Display styled text for testing step
print_styled "Running Tests:"
print_loading &
loading_pid=$!
python manage.py test cobrancas/tests > /dev/null  # Suppress test output
kill ${loading_pid}  # Stop the loading animation
print_separator

# Start the development server
print_styled "Starting Development Server:"
print_loading &
loading_pid=$!
kill ${loading_pid}  # Stop the loading animation
python manage.py runserver 0.0.0.0:8000
