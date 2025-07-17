#!/bin/bash

# --- Script Configuration ---
# Get the current user (even under sudo)
USER=${SUDO_USER:-$(whoami)}
# Directory where the script and virtual environment will be installed
TARGET_DIR="/home/$USER"
# Name of the systemd service
SERVICE_NAME="wolserver"
# Full path to the systemd service file
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
# Full path where the Python script will reside
TARGET_SCRIPT="$TARGET_DIR/wol_server.py"
# Directory for the Python virtual environment
VENV_DIR="$TARGET_DIR/wolenv"
# Path to the Python executable inside the virtual environment
PYTHON_BIN="$VENV_DIR/bin/python"
# Path to the pip executable inside the virtual environment
PIP_BIN="$VENV_DIR/bin/pip"
# GitHub raw URL for the Python script
RAW_PYTHON_URL="https://raw.githubusercontent.com/AlviseMantelli/wol_on_http/main/wol_server.py"

# --- Main Installation Logic ---

echo "✅ Installing or updating $SERVICE_NAME for user: $USER"

# Initialize variables to hold MAC, IP, and PORT
TARGET_MAC=""
TARGET_IP=""
PORT=""
KEEP_VARS="no" # Default to 'no' for keeping variables

# --- Variable Retention Logic ---
# Check if the Python script already exists to offer variable retention
if [ -f "$TARGET_SCRIPT" ]; then
    echo "⚠️  Existing script found at $TARGET_SCRIPT."
    read -rp "Do you want to keep the current MAC, IP, and PORT variables from it? (y/N): " KEEP_VARS_INPUT
    KEEP_VARS_INPUT=${KEEP_VARS_INPUT,,} # Convert input to lowercase

    if [[ "$KEEP_VARS_INPUT" == "y" || "$KEEP_VARS_INPUT" == "yes" ]]; then
        KEEP_VARS="yes"
        echo "ℹ️  Attempting to load variables from the existing script..."
        
        # Read existing variables. Using 'grep' and 'awk' for robustness.
        # This assumes variables are on lines like: TARGET_MAC = 'AA:BB:CC:DD:EE:FF' or PORT = 8000
        OLD_MAC_READ=$(grep "TARGET_MAC =" "$TARGET_SCRIPT" | awk -F"'" '{print $2}' | head -1)
        OLD_IP_READ=$(grep "TARGET_IP =" "$TARGET_SCRIPT" | awk -F"'" '{print $2}' | head -1)
        OLD_PORT_READ=$(grep "PORT =" "$TARGET_SCRIPT" | awk -F"=" '{print $2}' | tr -d ' ' | head -1)

        # Assign read values if they are not empty
        TARGET_MAC=${OLD_MAC_READ:-$TARGET_MAC}
        TARGET_IP=${OLD_IP_READ:-$TARGET_IP}
        PORT=${OLD_PORT_READ:-$PORT}

        if [ -n "$TARGET_MAC" ] && [ -n "$TARGET_IP" ] && [ -n "$PORT" ]; then
            echo "✅ Successfully loaded existing variables:"
            echo "   - MAC: $TARGET_MAC"
            echo "   - IP: $TARGET_IP"
            echo "   - PORT: $PORT"
        else
            echo "❌ Could not fully load existing variables. Please provide them manually."
            KEEP_VARS="no" # Fallback to manual input if load fails
        fi
    else
        echo "ℹ️  Existing variables will not be kept. You'll be prompted for new ones."
    fi
fi

# Prompt for new variables if not keeping old ones or if load failed
if [[ "$KEEP_VARS" != "yes" ]]; then
    # Prompt for MAC address
    while true; do
        read -rp "📥 Enter the target MAC address for Wake-on-LAN (e.g., A0:B2:C3:D4:E5:F6): " TARGET_MAC
        if [[ "$TARGET_MAC" =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
            break
        else
            echo "❌ Invalid MAC address format. Please try again."
        fi
    done

    # Prompt for IP address
    while true; do
        read -rp "🌐 Enter the target IP address (e.g., 192.168.1.123): " TARGET_IP
        # Simple IP validation, could be more robust
        if [[ "$TARGET_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
            break
        else
            echo "❌ Invalid IP address format. Please try again."
        fi
    done

    # Prompt for port
    while true; do
        read -rp "📡 Enter the port number to listen on (default: 8000): " USER_PORT_INPUT
        PORT=${USER_PORT_INPUT:-8000} # Use default if empty
        if [[ "$PORT" =~ ^[0-9]{1,5}$ ]] && [ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ]; then
            break
        else
            echo "❌ Invalid port number. Must be between 1 and 65535. Please try again."
        fi
    done
fi

# --- System Prerequisites Check ---
echo "🧰 Checking for Python and pip..."
if ! command -v python3 >/dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install pip3 if not found
if ! command -v pip3 >/dev/null; then
    echo "🔧 pip3 not found. Installing..."
    sudo apt-get update && sudo apt-get install -y python3-pip || {
        echo "❌ Failed to install python3-pip. Please install it manually."
        exit 1
    }
fi

# Install python3-venv if not found
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "❌ python3-venv is not installed. Installing..."
    sudo apt-get install -y python3-venv || {
        echo "❌ Failed to install python3-venv. Please install it manually."
        exit 1
    }
fi

# --- Virtual Environment Setup ---
# Create virtualenv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || {
        echo "❌ Failed to create virtual environment."
        exit 1
    }
fi

# Activate virtual environment (for the current shell only, not strictly needed for direct python calls)
# source "$VENV_DIR/bin/activate" 

# Install wakeonlan inside virtualenv
echo "📦 Installing or updating required Python package 'wakeonlan' in virtualenv..."
"$PIP_BIN" install --upgrade pip || { echo "❌ Failed to upgrade pip."; exit 1; }
"$PIP_BIN" install wakeonlan || { echo "❌ Failed to install wakeonlan."; exit 1; }

# --- Script Download and Configuration ---
# Ensure target directory exists for the Python script
mkdir -p "$TARGET_DIR" || { echo "❌ Failed to create target directory."; exit 1; }

# Download the Python script (always overwrite to get the latest code)
echo "⬇️  Downloading the latest Python script to $TARGET_SCRIPT..."
curl -fsSL "$RAW_PYTHON_URL" -o "$TARGET_SCRIPT" || {
    echo "❌ Failed to download Python script from $RAW_PYTHON_URL."
    exit 1
}

# Inject variables into the downloaded Python script
echo "🛠️  Injecting MAC, IP, and PORT into the Python script..."
# Using single quotes for MAC/IP as they are strings in Python
sed -i "s/^TARGET_MAC = .*/TARGET_MAC = '$TARGET_MAC'/" "$TARGET_SCRIPT" || { echo "❌ Failed to update TARGET_MAC."; exit 1; }
sed -i "s/^TARGET_IP = .*/TARGET_IP = '$TARGET_IP'/" "$TARGET_SCRIPT" || { echo "❌ Failed to update TARGET_IP."; exit 1; }
# PORT is an integer in Python, so no quotes
sed -i "s/^PORT = .*/PORT = $PORT/" "$TARGET_SCRIPT" || { echo "❌ Failed to update PORT."; exit 1; }

# Set appropriate permissions and ownership for the Python script
chmod +x "$TARGET_SCRIPT" || { echo "❌ Failed to set script executable permissions."; exit 1; }
chown "$USER:$USER" "$TARGET_SCRIPT" || { echo "❌ Failed to set script ownership."; exit 1; }
echo "Python script configured and permissions set."

# --- Systemd Service Setup ---
# Create the systemd service file
echo "⚙️  Writing systemd service to $SERVICE_FILE..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Wake-on-LAN HTTP Listener
After=network.target

[Service]
ExecStart=$PYTHON_BIN $TARGET_SCRIPT
WorkingDirectory=$TARGET_DIR
Restart=always
User=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload, enable, and start the service
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "🔌 Enabling $SERVICE_NAME service..."
sudo systemctl enable "$SERVICE_NAME"

# Check if the service is active to determine if it should be restarted or started
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "♻️  Restarting $SERVICE_NAME..."
    sudo systemctl restart "$SERVICE_NAME"
else
    echo "▶️  Starting $SERVICE_NAME..."
    sudo systemctl start "$SERVICE_NAME"
fi

# --- Final Output ---
echo "✅ Installation and configuration of $SERVICE_NAME complete!"
echo "🌐 Access your Wake-on-LAN server via: http://<your-server-ip>:$PORT/wol"