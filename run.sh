#!/bin/bash

# Dispo-Python Application Launcher
# This script activates the virtual environment and runs the application

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if virtual environment exists
check_venv() {
    if [ -d "venv_new" ]; then
        VENV_DIR="venv_new"
    elif [ -d "venv" ]; then
        VENV_DIR="venv"
    else
        print_message "❌ Virtual environment not found!" "$RED"
        print_message "Creating virtual environment..." "$YELLOW"
        python3 -m venv venv_new
        VENV_DIR="venv_new"

        # Activate and install requirements
        source "$VENV_DIR/bin/activate"
        print_message "📦 Installing requirements..." "$YELLOW"
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r requirements.txt
    fi
}

# Function to display the menu
show_menu() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Dispo-Python Document Management      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Select an option:${NC}"
    echo ""
    echo "  1) 🖥️  Run GUI Application"
    echo "  2) 🌐 Run API Server"
    echo "  3) 📊 Show Database Statistics"
    echo "  4) 💾 Backup Database"
    echo "  5) 🔄 Restore Database"
    echo "  6) 👤 User Management"
    echo "  7) 🔧 Initialize Database"
    echo "  8) 📦 Install/Update Requirements"
    echo "  9) 🧪 Run Tests"
    echo "  0) 🚪 Exit"
    echo ""
    echo -n "Enter your choice [0-9]: "
}

# Function to run GUI
run_gui() {
    print_message "🚀 Starting GUI Application..." "$GREEN"
    python src/main.py --mode gui
}

# Function to run API
run_api() {
    echo -n "Enter port (default 5000): "
    read port
    port=${port:-5000}
    print_message "🌐 Starting API Server on port $port..." "$GREEN"
    print_message "📚 API Documentation will be available at: http://localhost:$port/docs" "$BLUE"
    python src/main.py --mode api --port $port
}

# Function to show statistics
show_stats() {
    print_message "📊 Database Statistics:" "$GREEN"
    python src/main.py --mode cli stats
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function to backup database
backup_db() {
    print_message "💾 Creating database backup..." "$YELLOW"
    python src/main.py --mode cli backup
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function to restore database
restore_db() {
    echo -n "Enter backup path: "
    read backup_path
    if [ -n "$backup_path" ]; then
        print_message "🔄 Restoring database from $backup_path..." "$YELLOW"
        python src/main.py --mode cli restore "$backup_path"
    else
        print_message "❌ No backup path provided!" "$RED"
    fi
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function for user management
user_management() {
    clear
    echo -e "${BLUE}User Management${NC}"
    echo "================"
    echo "1) Create User"
    echo "2) List Users"
    echo "0) Back"
    echo ""
    echo -n "Choice: "
    read user_choice

    case $user_choice in
        1)
            echo -n "Username: "
            read username
            echo -n "Email: "
            read email
            echo -n "Password: "
            read -s password
            echo ""
            echo -n "Full Name: "
            read fullname
            echo -n "Role (admin/manager/user/viewer): "
            read role
            echo -n "Department (optional): "
            read department

            python src/main.py --mode cli user create \
                --username "$username" \
                --email "$email" \
                --password "$password" \
                --full-name "$fullname" \
                --role "$role" \
                --department "$department"
            ;;
        2)
            python src/main.py --mode cli user list
            ;;
    esac
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function to initialize database
init_db() {
    print_message "🔧 Initializing database..." "$YELLOW"
    python src/main.py --mode cli init
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function to install/update requirements
install_requirements() {
    print_message "📦 Installing/Updating requirements..." "$YELLOW"
    pip install --upgrade pip
    pip install -r requirements.txt
    print_message "✅ Requirements installed successfully!" "$GREEN"
    echo ""
    echo "Press Enter to continue..."
    read
}

# Function to run tests
run_tests() {
    print_message "🧪 Running tests..." "$YELLOW"
    if command -v pytest &> /dev/null; then
        pytest src/tests/ -v --cov=src
    else
        print_message "pytest not installed. Installing..." "$YELLOW"
        pip install pytest pytest-cov
        pytest src/tests/ -v --cov=src
    fi
    echo ""
    echo "Press Enter to continue..."
    read
}

# Main script execution
main() {
    # Check for virtual environment
    check_venv

    # Activate virtual environment
    print_message "🐍 Activating virtual environment..." "$YELLOW"
    source "$VENV_DIR/bin/activate"

    # Check if running with arguments (direct mode)
    if [ $# -gt 0 ]; then
        case "$1" in
            gui)
                run_gui
                ;;
            api)
                port=${2:-5000}
                python src/main.py --mode api --port $port
                ;;
            stats)
                python src/main.py --mode cli stats
                ;;
            backup)
                python src/main.py --mode cli backup
                ;;
            restore)
                if [ -n "$2" ]; then
                    python src/main.py --mode cli restore "$2"
                else
                    print_message "❌ Please provide backup path!" "$RED"
                fi
                ;;
            init)
                python src/main.py --mode cli init
                ;;
            test)
                run_tests
                ;;
            help|--help|-h)
                echo "Usage: $0 [command] [options]"
                echo ""
                echo "Commands:"
                echo "  gui              Run GUI application"
                echo "  api [port]       Run API server (default port: 5000)"
                echo "  stats            Show database statistics"
                echo "  backup           Backup database"
                echo "  restore <path>   Restore database from backup"
                echo "  init             Initialize database"
                echo "  test             Run tests"
                echo "  help             Show this help message"
                echo ""
                echo "Without arguments, runs interactive menu"
                ;;
            *)
                print_message "❌ Unknown command: $1" "$RED"
                echo "Use '$0 help' for available commands"
                exit 1
                ;;
        esac
    else
        # Interactive menu mode
        while true; do
            show_menu
            read choice

            case $choice in
                1) run_gui ;;
                2) run_api ;;
                3) show_stats ;;
                4) backup_db ;;
                5) restore_db ;;
                6) user_management ;;
                7) init_db ;;
                8) install_requirements ;;
                9) run_tests ;;
                0)
                    print_message "👋 Goodbye!" "$GREEN"
                    deactivate 2>/dev/null
                    exit 0
                    ;;
                *)
                    print_message "❌ Invalid option!" "$RED"
                    sleep 1
                    ;;
            esac
        done
    fi

    # Deactivate virtual environment on exit
    deactivate 2>/dev/null
}

# Trap to ensure cleanup on exit
trap 'deactivate 2>/dev/null' EXIT

# Run main function with all arguments
main "$@"