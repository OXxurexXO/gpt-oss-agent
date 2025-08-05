#!/bin/bash

# GPT-OSS Agent Installation Script
# Comprehensive setup for the GPT-OSS Agent system
# Compatible with macOS (Apple Silicon recommended)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_warning "This script is optimized for macOS. Other systems may work but are not officially supported."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."

    # Check available memory (at least 16GB recommended)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        TOTAL_MEM_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
        log_info "Total system memory: ${TOTAL_MEM_GB}GB"

        if [ "$TOTAL_MEM_GB" -lt 16 ]; then
            log_warning "Less than 16GB RAM detected. GPT-OSS models may run slowly or fail."
        elif [ "$TOTAL_MEM_GB" -ge 64 ]; then
            log_success "Excellent! ${TOTAL_MEM_GB}GB RAM is perfect for GPT-OSS-120B model."
        else
            log_info "Good! ${TOTAL_MEM_GB}GB RAM should work well with GPT-OSS-20B model."
        fi
    fi

    # Check available disk space (at least 50GB recommended)
    log_info "Available disk space: $(df -h . | awk 'NR==2 {print $4}')"
}

# Install Homebrew if not present
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            # shellcheck disable=SC2016
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi

        log_success "Homebrew installed successfully"
    else
        log_info "Homebrew already installed"
    fi
}

# Install Python 3.10+ if not present
install_python() {
    if ! command -v python3 &> /dev/null; then
        log_info "Installing Python..."
        brew install python@3.11
        log_success "Python installed successfully"
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        log_info "Python ${PYTHON_VERSION} already installed"
    fi
}

# Install Ollama
install_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_info "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        log_success "Ollama installed successfully"
    else
        log_info "Ollama already installed"
        ollama --version
    fi
}

# Start Ollama service
start_ollama() {
    log_info "Starting Ollama service..."

    # Check if Ollama is already running
    if pgrep -x "ollama" > /dev/null; then
        log_info "Ollama is already running"
    else
        # Start Ollama in the background
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3  # Give it time to start

        if pgrep -x "ollama" > /dev/null; then
            log_success "Ollama service started successfully"
        else
            log_error "Failed to start Ollama service"
            exit 1
        fi
    fi
}

# Pull GPT-OSS models
pull_gpt_models() {
    log_info "Pulling GPT-OSS models (this may take a while)..."

    # Determine which model to pull based on available memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
        TOTAL_MEM_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')

        if [ "$TOTAL_MEM_GB" -ge 64 ]; then
            log_info "Pulling GPT-OSS-120B model (recommended for your system)..."
            ollama pull gpt-oss:120b
            log_success "GPT-OSS-120B model downloaded"
        fi
    fi

    # Always pull the 20B model as a fallback
    log_info "Pulling GPT-OSS-20B model..."
    ollama pull gpt-oss:20b
    log_success "GPT-OSS-20B model downloaded"

    # List available models
    log_info "Available models:"
    ollama list
}

# Set up Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    # Activate virtual environment
    # shellcheck source=/dev/null
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    mkdir -p knowledge_base
    mkdir -p logs
    mkdir -p temp

    log_success "Directories created"
}

# Run initial setup
run_initial_setup() {
    log_info "Running initial setup..."

    # Activate virtual environment
    # shellcheck source=/dev/null
    source venv/bin/activate

    # Run the initialization script if it exists
    if [ -f "init_gpt_oss_agent.py" ]; then
        python init_gpt_oss_agent.py
        log_success "Initial setup completed"
    else
        log_warning "init_gpt_oss_agent.py not found, skipping initial setup"
    fi
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."

    cat > start_agent.sh << 'EOF'
#!/bin/bash

# GPT-OSS Agent Startup Script

# Activate virtual environment
source venv/bin/activate

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start the GPT-OSS Agent
python gpt_oss_agent.py
EOF

    chmod +x start_agent.sh
    log_success "Startup script created (start_agent.sh)"
}

# Create uninstall script
create_uninstall_script() {
    log_info "Creating uninstall script..."

    cat > uninstall.sh << 'EOF'
#!/bin/bash

# GPT-OSS Agent Uninstall Script

echo "This will remove the GPT-OSS Agent and its components."
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing virtual environment..."
    rm -rf venv

    echo "Removing knowledge base..."
    rm -rf knowledge_base

    echo "Removing logs..."
    rm -rf logs

    echo "Removing temp files..."
    rm -rf temp

    echo "Removing startup script..."
    rm -f start_agent.sh

    echo "Stopping Ollama (if running)..."
    pkill ollama

    echo "GPT-OSS Agent uninstalled."
    echo "Note: Ollama and models are still installed. Remove manually if desired:"
    echo "  ollama rm gpt-oss:20b"
    echo "  ollama rm gpt-oss:120b"
    echo "  brew uninstall ollama"
else
    echo "Uninstall cancelled."
fi
EOF

    chmod +x uninstall.sh
    log_success "Uninstall script created (uninstall.sh)"
}

# Display final instructions
show_final_instructions() {
    log_success "Installation completed successfully!"
    echo
    echo -e "${GREEN}🎉 GPT-OSS Agent is ready to use!${NC}"
    echo
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  ./start_agent.sh                  # Start the agent"
    echo "  source venv/bin/activate          # Activate Python environment"
    echo "  python gpt_oss_agent.py           # Run main agent"
    echo "  python knowledge_agent.py         # Run knowledge assistant"
    echo "  python file_agent.py 'list files' # Run file operations"
    echo
    echo -e "${BLUE}Available Models:${NC}"
    ollama list | grep gpt-oss || echo "  Run 'ollama list' to see available models"
    echo
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Index your documents: python knowledge_agent.py"
    echo "  2. Start chatting with your data!"
    echo "  3. Check README.md for detailed usage instructions"
    echo
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  - If models don't load, check available RAM"
    echo "  - Run './uninstall.sh' to remove everything"
    echo "  - Check logs/ directory for error details"
    echo
}

# Main installation function
main() {
    echo -e "${GREEN}"
    echo "=================================================="
    echo "      GPT-OSS Agent Installation Script"
    echo "=================================================="
    echo -e "${NC}"

    check_macos
    check_system_requirements

    install_homebrew
    install_python
    install_ollama
    start_ollama
    pull_gpt_models
    setup_python_env
    create_directories
    run_initial_setup
    create_startup_script
    create_uninstall_script

    show_final_instructions
}

# Run main function
main "$@"
