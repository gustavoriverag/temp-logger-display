#!/bin/bash -x
[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

VENV_DIR="/opt/virtualenv/temp_logger"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -e .

"$VENV_DIR/bin/pip" install gunicorn


cp ./logger_display.service /etc/systemd/system/logger_display.service

systemctl daemon-reload
systemctl enable logger_display.service
systemctl start logger_display.service
