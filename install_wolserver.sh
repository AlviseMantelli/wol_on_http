#!/bin/bash

# Get the current user (even under sudo)
USER=${SUDO_USER:-$(whoami)}
TARGET_DIR="/home/$USER"
SERVICE_NAME="wolserver"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TARGET_SCRIPT="$TARGET_DIR/wol_server.py"
VENV_DIR="$TARGET_DIR/wolenv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# GitHub raw URL (adjust to your actual repo)
RAW_PYTHON_URL="https://raw.githubusercontent.com/AlviseMantelli/wol_on_http/main/wol_server.py"

echo "✅ Installing or updating $SERVICE_NAME for user: $USER"

# Prompt for MAC address
read -rp "📥 Enter the target MAC address for Wake-on-LAN (e.g. A0:B2:C3:D4:E5:F6): " TARGET_MAC
if [[ ! "$TARGET_MAC" =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
    echo "❌ Invalid MAC address format."
    exit 1
fi

# Prompt for IP address
read -rp "🌐 Enter the target IP address (e.g. 192.168.1.123): " TARGET_IP
if ! [[ "$TARGET_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    echo "❌ Invalid IP address format."
    exit 1
fi

# Prompt for port
read -rp "📡 Enter the port number to listen on (default: 8000): " PORT
PORT=${PORT:-8000}
if ! [[ "$PORT" =~ ^[0-9]{1,5}$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "❌ Invalid port number."
    exit 1
fi

# Ensure Python3 and pip are installed
echo "🧰 Checking for Python and pip..."
if ! command -v python3 >/dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

if ! command -v pip3 >/dev/null; then
    echo "🔧 pip3 not found. Installing..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

# Create virtualenv if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Install wakeonlan inside virtualenv
echo "📦 Installing required Python package 'wakeonlan' in virtualenv..."
"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install wakeonlan

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Download the Python script
echo "⬇️  Downloading Python script..."
curl -fsSL "$RAW_PYTHON_URL" -o "$TARGET_SCRIPT" || {
    echo "❌ Failed to download Python script."
    exit 1
}

# Inject MAC address and port into the Python script
echo "🛠️  Customizing script with MAC and port..."
sed -i "s/^TARGET_MAC = .*/TARGET_MAC = '$TARGET_MAC'/" "$TARGET_SCRIPT"
sed -i "s/^PORT = .*/PORT = $PORT/" "$TARGET_SCRIPT"
sed -i "s/^TARGET_IP = .*/TARGET_IP = '$TARGET_IP'/" "$TARGET_SCRIPT"

chmod +x "$TARGET_SCRIPT"
chown "$USER:$USER" "$TARGET_SCRIPT"

# Create the systemd service
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

# Reload, enable and start the service
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo "🔌 Enabling service..."
sudo systemctl enable "$SERVICE_NAME"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "♻️  Restarting $SERVICE_NAME..."
    sudo systemctl restart "$SERVICE_NAME"
else
    echo "▶️  Starting $SERVICE_NAME..."
    sudo systemctl start "$SERVICE_NAME"
fi

echo "✅ Installation complete!"
echo "🌐 Access via: http://<your-ip>:$PORT/wol"
