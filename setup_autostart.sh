#!/bin/bash
# Setup script to enable Cat Butt Oracle auto-start on boot

set -e

echo "Setting up Cat Butt Oracle for auto-start on boot..."

# Check if running as root (needed for systemd setup)
if [[ $EUID -eq 0 ]]; then
   echo "Please run this script as a regular user (not sudo)"
   echo "The script will ask for sudo when needed"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "main_controller.py" ]]; then
    echo "Error: Please run this script from the cat-butt-oracle directory"
    exit 1
fi

# Copy service file to systemd directory
echo "Installing systemd service..."
sudo cp cat-butt-oracle.service /etc/systemd/system/

# Reload systemd to recognize the new service
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling Cat Butt Oracle service..."
sudo systemctl enable cat-butt-oracle.service

# Start the service now (optional)
echo "Starting Cat Butt Oracle service..."
sudo systemctl start cat-butt-oracle.service

echo ""
echo "✅ Setup complete! Cat Butt Oracle will now start automatically on boot."
echo ""
echo "Useful commands:"
echo "  sudo systemctl status cat-butt-oracle    # Check service status"
echo "  sudo systemctl stop cat-butt-oracle      # Stop the service"
echo "  sudo systemctl start cat-butt-oracle     # Start the service"
echo "  sudo systemctl restart cat-butt-oracle   # Restart the service"
echo "  sudo journalctl -u cat-butt-oracle -f    # View live logs"
echo "  sudo systemctl disable cat-butt-oracle   # Disable auto-start"
echo ""
echo "The service is now running! Check status with:"
echo "  sudo systemctl status cat-butt-oracle"