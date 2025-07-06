#!/bin/bash -x

VENV_DIR = "/opt/virtualenv/temp_logger"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -e .

pip install gunicorn

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

cp ./logger_display.service /etc/systemd/system/logger_display.service

systemctl daemon-reload
systemctl enable logger_display.service
systemctl start logger_display.service
