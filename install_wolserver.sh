#!/bin/bash

# --- Script Configuration ---
# Get the current user (even under sudo)
USER=${SUDO_USER:-$(whoami)}
# Base directory where the script and virtual environment will be installed
BASE_DIR="/home/$USER"
# GitHub raw URL for the *new* Python script
# !!! UPDATE THIS URL to point to your hosted version of the Python script above !!!
RAW_PYTHON_URL="https://gist.githubusercontent.com/AlviseMantelli/wol_on_http/blob/main/wol_server.py"


# --- Main Installation Logic ---
echo "🚀 Welcome to the WOL Server Installer"

# --- Get Friendly Name and Set Unique Paths ---
read -rp "Enter a friendly name for this device (e.g., 'My-PC', 'Server-2'): " FRIENDLY_NAME

if [ -z "$FRIENDLY_NAME" ]; then
    echo "❌ Friendly name cannot be empty."
    exit 1
fi

# Sanitize the name for use in filenames and service names
# Converts to lowercase, replaces spaces/punctuation with a hyphen, removes leading/trailing hyphens
SAFE_NAME=$(echo "$FRIENDLY_NAME" | tr '[:upper:]' '[:lower:]' | tr -s '[:punct:][:space:]' '-' | sed 's/^-*//;s/-*$//')

echo "ℹ️  Using sanitized name for resources: '$SAFE_NAME'"

# --- Define Unique Paths based on SAFE_NAME ---
SERVICE_NAME="wolserver-$SAFE_NAME"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TARGET_SCRIPT="$BASE_DIR/wol_server_$SAFE_NAME.py"
VENV_DIR="$BASE_DIR/wolenv_$SAFE_NAME"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"


echo "✅ Installing or updating $SERVICE_NAME for user: $USER"

# Initialize variables to hold MAC, IP, and PORT
TARGET_MAC=""
TARGET_IP=""
BROADCAST_IP=""
PORT=""
KEEP_VARS="no" # Default to 'no' for keeping variables

# --- Variable Retention Logic ---
# Check if the Python script *for this specific service* already exists
if [ -f "$TARGET_SCRIPT" ]; then
    echo "⚠️  Existing script found at $TARGET_SCRIPT."
    read -rp "Do you want to keep the current MAC, IP, Broadcast IP, and PORT variables from it? (y/N): " KEEP_VARS_INPUT
    KEEP_VARS_INPUT=${KEEP_VARS_INPUT,,} # Convert input to lowercase

    if [[ "$KEEP_VARS_INPUT" == "y" || "$KEEP_VARS_INPUT" == "yes" ]]; then
        KEEP_VARS="yes"
        echo "ℹ️  Attempting to load variables from the existing script..."
        
        # Read existing variables. Using 'grep' and 'awk' for robustness.
        OLD_MAC_READ=$(grep "TARGET_MAC =" "$TARGET_SCRIPT" | awk -F"'" '{print $2}' | head -1)
        OLD_IP_READ=$(grep "TARGET_IP =" "$TARGET_SCRIPT" | awk -F"'" '{print $2}' | head -1)
        OLD_BROADCAST_READ=$(grep "BROADCAST_IP =" "$TARGET_SCRIPT" | awk -F"'" '{print $2}' | head -1)
        OLD_PORT_READ=$(grep "PORT =" "$TARGET_SCRIPT" | awk -F"=" '{print $2}' | tr -d ' ' | head -1)

        # Assign read values if they are not empty
        TARGET_MAC=${OLD_MAC_READ:-$TARGET_MAC}
        TARGET_IP=${OLD_IP_READ:-$TARGET_IP}
        BROADCAST_IP=${OLD_BROADCAST_READ:-$BROADCAST_IP}
        PORT=${OLD_PORT_READ:-$PORT}

        if [ -n "$TARGET_MAC" ] && [ -n "$TARGET_IP" ] && [ -n "$PORT" ] && [ -n "$BROADCAST_IP" ]; then
            echo "✅ Successfully loaded existing variables:"
            echo "   - MAC: $TARGET_MAC"
            echo "   - IP: $TARGET_IP"
            echo "   - Broadcast: $BROADCAST_IP"
            echo "   - PORT: $PORT"
        else
            echo "❌ Could not fully load all existing variables. Please provide them manually."
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
        read -rp "📥 Enter the target MAC address (e.g., A0:B2:C3:D4:E5:F6): " TARGET_MAC
        if [[ "$TARGET_MAC" =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
            break
        else
            echo "❌ Invalid MAC address format. Please try again."
        fi
    done

    # Prompt for IP address (for pinging)
    while true; do
        read -rp "🌐 Enter the target IP address for ping status (e.g., 192.168.1.123): " TARGET_IP
        if [[ "$TARGET_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
            break
        else
            echo "❌ Invalid IP address format. Please try again."
        fi
    done
    
    # Prompt for Broadcast IP address (for sending WOL)
    while true; do
        read -rp "📡 Enter the Broadcast IP address for WOL (e.g., 192.168.88.255): " BROADCAST_IP
        if [[ "$BROADCAST_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
            break
        else
            echo "❌ Invalid Broadcast IP address format. Please try again."
        fi
    done

    # Prompt for port
    while true; do
        read -rp "🔌 Enter the port number for this server (default: 8000): " USER_PORT_INPUT
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

# Install wakeonlan inside virtualenv
echo "📦 Installing or updating required Python package 'wakeonlan' in $VENV_DIR..."
"$PIP_BIN" install --upgrade pip || { echo "❌ Failed to upgrade pip."; exit 1; }
"$PIP_BIN" install wakeonlan || { echo "❌ Failed to install wakeonlan."; exit 1; }

# --- Script Download and Configuration ---
# Ensure base directory exists
mkdir -p "$BASE_DIR" || { echo "❌ Failed to create base directory."; exit 1; }

# Download the Python script (always overwrite to get the latest code)
echo "⬇️  Downloading the latest Python script to $TARGET_SCRIPT..."
curl -fsSL "$RAW_PYTHON_URL" -o "$TARGET_SCRIPT" || {
    echo "❌ Failed to download Python script from $RAW_PYTHON_URL."
    echo "   Please make sure you updated the RAW_PYTHON_URL variable in this installer script."
    exit 1
}

# Inject variables into the downloaded Python script
echo "🛠️  Injecting variables into the Python script..."
# Using single quotes for strings in Python
sed -i "s/^TARGET_MAC = .*/TARGET_MAC = '$TARGET_MAC'/" "$TARGET_SCRIPT" || { echo "❌ Failed to update TARGET_MAC."; exit 1; }
sed -i "s/^TARGET_IP = .*/TARGET_IP = '$TARGET_IP'/" "$TARGET_SCRIPT" || { echo "❌ Failed to update TARGET_IP."; exit 1; }
sed -i "s/^BROADCAST_IP = .*/BROADCAST_IP = '$BROADCAST_IP'/" "$TARGET_SCRIPT" || { echo "❌ Failed to update BROADCAST_IP."; exit 1; }

# Use | as delimiter for sed since FRIENDLY_NAME might contain slashes or other special chars
sed -i "s|^FRIENDLY_NAME = .*|FRIENDLY_NAME = '$FRIENDLY_NAME'|" "$TARGET_SCRIPT" || { echo "❌ Failed to update FRIENDLY_NAME."; exit 1; }

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
Description=WOL HTTP Listener for $FRIENDLY_NAME
After=network.target

[Service]
ExecStart=$PYTHON_BIN $TARGET_SCRIPT
WorkingDirectory=$BASE_DIR
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
echo "   Friendly Name: $FRIENDLY_NAME"
echo "   Service File: $SERVICE_FILE"
echo "   Script File: $TARGET_SCRIPT"
echo "   Venv Directory: $VENV_DIR"
echo "🌐 Access your Wake-on-LAN server via: http://<your-server-ip>:$PORT/"