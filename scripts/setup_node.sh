#!/bin/bash

# Setup script for Hyperliquid node with --serve-info
# This script sets up a non-validator node for the CopyTrade bot

set -e

echo "🚀 Setting up Hyperliquid node for CopyTrade bot..."

# Configuration
CHAIN=${1:-"Mainnet"}
NODE_DIR="$HOME/hl"
VISOR_BIN="$HOME/hl-visor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Darwin" ]]; then
    PLATFORM="macos"
    if [[ "$ARCH" == "arm64" ]]; then
        ARCH_TYPE="arm64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        ARCH_TYPE="x86_64"
    else
        print_error "Unsupported architecture: $ARCH"
        exit 1
    fi
elif [[ "$OS" == "Linux" ]]; then
    PLATFORM="linux"
    if [[ "$ARCH" == "aarch64" ]]; then
        ARCH_TYPE="arm64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        ARCH_TYPE="x86_64"
    else
        print_error "Unsupported architecture: $ARCH"
        exit 1
    fi
else
    print_error "Unsupported operating system: $OS"
    exit 1
fi

print_status "Detected platform: $PLATFORM ($ARCH_TYPE)"

# Check if ARM64 architecture
if [[ "$ARCH_TYPE" == "arm64" ]]; then
    print_warning "ARM64 architecture detected!"
    echo ""
    echo "⚠️  IMPORTANT: Hyperliquid binaries may not be available for ARM64 architecture."
    echo "   The bot will work with the public API, but you won't have the low-latency"
    echo "   benefits of a local node."
    echo ""
    echo "   Options:"
    echo "   1. Continue with public API only (recommended for ARM64)"
    echo "   2. Use Docker with x86_64 emulation (slower)"
    echo "   3. Use a Linux VM or cloud instance"
    echo ""
    read -p "Do you want to continue with public API only? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Setup cancelled. You can run the bot with public API only."
        exit 0
    fi
    
    # Create minimal setup for public API only
    print_status "Setting up for public API only..."
    
    # Create node directory
    mkdir -p "$NODE_DIR"
    cd "$NODE_DIR"
    
    # Create configuration
    echo "{\"chain\": \"$CHAIN\"}" > ~/visor.json
    
    # Create status script for public API
    cat > "$NODE_DIR/status.sh" <<EOF
#!/bin/bash
# Check public API status

echo "=== Hyperliquid Public API Status ==="
echo "Chain: $CHAIN"

if [[ "$CHAIN" == "Testnet" ]]; then
    API_URL="https://api.hyperliquid-testnet.xyz"
else
    API_URL="https://api.hyperliquid.xyz"
fi

echo "API URL: \$API_URL"
echo ""

echo "Testing API connection..."
curl -s "\$API_URL/info" -X POST -H "Content-Type: application/json" -d '{"type": "exchangeStatus"}' | jq . 2>/dev/null || echo "API not responding"

echo ""
echo "Note: Using public API (no local node)"
echo "The bot will work but with higher latency than a local node."
EOF

    chmod +x "$NODE_DIR/status.sh"
    
    print_status "Setup completed for public API only!"
    echo ""
    echo "📁 Node directory: $NODE_DIR"
    echo "🔧 Configuration: ~/visor.json"
    echo "🌐 API endpoint: https://api.hyperliquid-testnet.xyz (Testnet)"
    echo ""
    echo "📈 To check API status:"
    echo "   $NODE_DIR/status.sh"
    echo ""
    echo "✅ You can now run the bot with public API only."
    exit 0
fi

# Create node directory
print_status "Creating node directory..."
mkdir -p "$NODE_DIR"
cd "$NODE_DIR"

# Configure chain
print_status "Configuring chain: $CHAIN"
echo "{\"chain\": \"$CHAIN\"}" > ~/visor.json

# Download visor binary
print_status "Downloading visor binary..."
if [[ "$CHAIN" == "Testnet" ]]; then
    curl -L https://binaries.hyperliquid-testnet.xyz/Testnet/hl-visor > "$VISOR_BIN"
else
    curl -L https://binaries.hyperliquid.xyz/Mainnet/hl-visor > "$VISOR_BIN"
fi

chmod +x "$VISOR_BIN"

# Test binary compatibility
print_status "Testing binary compatibility..."
if ! "$VISOR_BIN" --help > /dev/null 2>&1; then
    print_error "Binary is not compatible with this system"
    print_error "This usually happens on ARM64 systems (Apple Silicon, ARM Linux)"
    echo ""
    echo "Solutions:"
    echo "1. Use Docker with x86_64 emulation"
    echo "2. Use a Linux VM or cloud instance"
    echo "3. Run the bot with public API only"
    echo ""
    echo "For now, the bot will work with public API only."
    
    # Create minimal setup
    cat > "$NODE_DIR/status.sh" <<EOF
#!/bin/bash
echo "=== Hyperliquid Status ==="
echo "Local node: Not available (binary incompatibility)"
echo "Public API: Available"
echo ""
echo "The bot will use public API only."
EOF
    chmod +x "$NODE_DIR/status.sh"
    
    print_status "Setup completed with public API fallback!"
    exit 0
fi

# Verify binary (optional)
print_status "Verifying binary signature..."
if command -v gpg &> /dev/null; then
    # Download public key
    curl -L https://raw.githubusercontent.com/hyperliquid-dex/hyperliquid/main/node/pub_key.asc > pub_key.asc
    gpg --import pub_key.asc 2>/dev/null || true
    
    # Download signature
    if [[ "$CHAIN" == "Testnet" ]]; then
        curl -L https://binaries.hyperliquid-testnet.xyz/Testnet/hl-visor.asc > hl-visor.asc
    else
        curl -L https://binaries.hyperliquid.xyz/Mainnet/hl-visor.asc > hl-visor.asc
    fi
    
    # Verify signature
    if gpg --verify hl-visor.asc "$VISOR_BIN" 2>/dev/null; then
        print_status "Binary signature verified successfully"
    else
        print_warning "Could not verify binary signature (this is normal if gpg key is not trusted)"
    fi
else
    print_warning "gpg not found, skipping signature verification"
fi

# Create service based on platform
if [[ "$PLATFORM" == "linux" ]]; then
    print_status "Creating systemd service..."
    
    # Check if systemd is available
    if command -v systemctl &> /dev/null; then
        sudo tee /etc/systemd/system/hyperliquid-node.service > /dev/null <<EOF
[Unit]
Description=Hyperliquid Node
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
ExecStart=$VISOR_BIN run-non-validator --serve-info --write-fills --write-order-statuses
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768

# Environment
Environment=HOME=$HOME

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd and enable service
        print_status "Enabling systemd service..."
        sudo systemctl daemon-reload
        sudo systemctl enable hyperliquid-node.service
        
        print_status "Systemd service created and enabled"
    else
        print_warning "systemd not found, skipping service creation"
    fi
    
elif [[ "$PLATFORM" == "macos" ]]; then
    print_status "Creating launchd service..."
    
    # Create launchd plist file
    PLIST_FILE="$HOME/Library/LaunchAgents/com.hyperliquid.node.plist"
    
    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hyperliquid.node</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VISOR_BIN</string>
        <string>run-non-validator</string>
        <string>--serve-info</string>
        <string>--write-fills</string>
        <string>--write-order-statuses</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$HOME</string>
    <key>StandardOutPath</key>
    <string>$NODE_DIR/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$NODE_DIR/logs/stderr.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

    # Create logs directory
    mkdir -p "$NODE_DIR/logs"
    
    # Load the service
    print_status "Loading launchd service..."
    launchctl load "$PLIST_FILE" 2>/dev/null || true
    
    print_status "Launchd service created and loaded"
fi

# Create data directory
print_status "Creating data directory..."
mkdir -p "$NODE_DIR/data"

# Set permissions
print_status "Setting permissions..."
chmod 755 "$NODE_DIR"
chmod 755 "$NODE_DIR/data"

# Create startup script
print_status "Creating startup script..."
cat > "$NODE_DIR/start_node.sh" <<EOF
#!/bin/bash
# Start Hyperliquid node manually

cd "$NODE_DIR"
$VISOR_BIN run-non-validator --serve-info --write-fills --write-order-statuses
EOF

chmod +x "$NODE_DIR/start_node.sh"

# Create status script
print_status "Creating status script..."
cat > "$NODE_DIR/status.sh" <<EOF
#!/bin/bash
# Check node status

echo "=== Hyperliquid Node Status ==="

if [[ "$PLATFORM" == "linux" ]]; then
    echo "Service status:"
    sudo systemctl status hyperliquid-node.service --no-pager -l 2>/dev/null || echo "Service not found"
elif [[ "$PLATFORM" == "macos" ]]; then
    echo "Service status:"
    launchctl list | grep hyperliquid || echo "Service not found"
fi

echo ""
echo "Node info endpoint:"
curl -s http://localhost:3001/info -X POST -H "Content-Type: application/json" -d '{"type": "exchangeStatus"}' | jq . 2>/dev/null || echo "Node not responding"

echo ""
echo "Data directory size:"
du -sh "$NODE_DIR/data" 2>/dev/null || echo "Data directory not found"

if [[ "$PLATFORM" == "linux" ]]; then
    echo ""
    echo "Recent logs:"
    sudo journalctl -u hyperliquid-node.service -n 20 --no-pager 2>/dev/null || echo "No logs found"
elif [[ "$PLATFORM" == "macos" ]]; then
    echo ""
    echo "Recent logs:"
    tail -n 20 "$NODE_DIR/logs/stdout.log" 2>/dev/null || echo "No logs found"
fi
EOF

chmod +x "$NODE_DIR/status.sh"

# Create stop script
print_status "Creating stop script..."
cat > "$NODE_DIR/stop_node.sh" <<EOF
#!/bin/bash
# Stop Hyperliquid node

if [[ "$PLATFORM" == "linux" ]]; then
    sudo systemctl stop hyperliquid-node.service
elif [[ "$PLATFORM" == "macos" ]]; then
    launchctl unload "$HOME/Library/LaunchAgents/com.hyperliquid.node.plist" 2>/dev/null || true
fi
echo "Node stopped"
EOF

chmod +x "$NODE_DIR/stop_node.sh"

# Print completion message
echo ""
print_status "Setup completed successfully!"
echo ""
echo "📁 Node directory: $NODE_DIR"
echo "🔧 Configuration: ~/visor.json"
echo "📊 Data directory: $NODE_DIR/data"
echo "🌐 Info endpoint: http://localhost:3001/info"
echo ""

if [[ "$PLATFORM" == "linux" ]]; then
    echo "🚀 To start the node:"
    echo "   sudo systemctl start hyperliquid-node.service"
    echo "   # or manually: $NODE_DIR/start_node.sh"
    echo ""
    echo "📈 To check status:"
    echo "   $NODE_DIR/status.sh"
    echo ""
    echo "⏹️  To stop the node:"
    echo "   $NODE_DIR/stop_node.sh"
    echo ""
    echo "📋 Useful commands:"
    echo "   sudo systemctl status hyperliquid-node.service"
    echo "   sudo journalctl -u hyperliquid-node.service -f"
    echo "   curl http://localhost:3001/info -X POST -H 'Content-Type: application/json' -d '{\"type\": \"exchangeStatus\"}'"
elif [[ "$PLATFORM" == "macos" ]]; then
    echo "🚀 To start the node:"
    echo "   launchctl load $HOME/Library/LaunchAgents/com.hyperliquid.node.plist"
    echo "   # or manually: $NODE_DIR/start_node.sh"
    echo ""
    echo "📈 To check status:"
    echo "   $NODE_DIR/status.sh"
    echo ""
    echo "⏹️  To stop the node:"
    echo "   $NODE_DIR/stop_node.sh"
    echo ""
    echo "📋 Useful commands:"
    echo "   launchctl list | grep hyperliquid"
    echo "   tail -f $NODE_DIR/logs/stdout.log"
    echo "   curl http://localhost:3001/info -X POST -H 'Content-Type: application/json' -d '{\"type\": \"exchangeStatus\"}'"
fi

echo ""
print_warning "The node may take several minutes to sync initially. Check status with the status script."
