#!/bin/bash
#
# install.sh — installs this repo into Klipper or Kalico
#
# Kalico uses klippy/plugins/
# Klipper uses klippy/extras/
# This script auto-detects which one is present and symlinks accordingly.
set -euo pipefail

# --- config

PLUGIN_NAME="statechange_gcode"
PLUGIN_ROOT_DIR=${PLUGIN_ROOT_DIR:-"${HOME}"}
PLUGIN_GIT="https://github.com/yell3D/statechange_gcode.git"

PLUGIN_INST_CMD() {
    ln -sf "${PLUGIN_ROOT_DIR}/${PLUGIN_NAME}/${PLUGIN_NAME}.py" "$1/${PLUGIN_NAME}.py"
}

# --- static content
if [ "$EUID" -eq 0 ]; then
    echo "[ERROR] This script must not be run as root!"
    exit 1
fi

KALICO_PATH="${HOME}/kalico"
KLIPPER_PATH_DEFAULT="${HOME}/klipper"

CHECK_PLUGINS="no"

if [ -n "${KLIPPER_PATH_OVERRIDE:-}" ]; then
    KLIPPER_PATH="${KLIPPER_PATH_OVERRIDE}"
    if [ ! -d "${KLIPPER_PATH}" ]; then
        echo "[ERROR] KLIPPER_PATH_OVERRIDE set to '${KLIPPER_PATH}' but that directory does not exist."
        exit 1
    fi
    CHECK_PLUGINS="yes"
elif [ -d "${KALICO_PATH}" ]; then
    KLIPPER_PATH="${KALICO_PATH}"
    CHECK_PLUGINS="yes"
elif [ -d "${KLIPPER_PATH_DEFAULT}" ]; then
    KLIPPER_PATH="${KLIPPER_PATH_DEFAULT}"
else
    echo "[ERROR] Could not find a Klipper or Kalico install at ${KALICO_PATH} or ${KLIPPER_PATH_DEFAULT}"
    echo "        If installed elsewhere, set KLIPPER_PATH_OVERRIDE and re-run, e.g.:"
    echo "           KLIPPER_PATH_OVERRIDE=/custom/path ./install.sh"
    exit 1
fi

TARGET_DIR=""
if [ "${CHECK_PLUGINS}" = "yes" ] && [ -d "${KLIPPER_PATH}/klippy/plugins" ]; then
    TARGET_DIR="${KLIPPER_PATH}/klippy/plugins"
elif [ -d "${KLIPPER_PATH}/klippy/extras" ]; then
    TARGET_DIR="${KLIPPER_PATH}/klippy/extras"
fi

if [ -z "${TARGET_DIR}" ]; then
    echo "[ERROR] Neither klippy/plugins nor klippy/extras found under ${KLIPPER_PATH}"
    exit 1
fi

PLUGIN_DEST="${TARGET_DIR}"

# FIXED: Check if the folder already exists before cloning to prevent errors
if [ -d "${PLUGIN_ROOT_DIR}/${PLUGIN_NAME}" ]; then
    echo "[WARN] Directory ${PLUGIN_ROOT_DIR}/${PLUGIN_NAME} already exists. resetting."
    git -C "${PLUGIN_ROOT_DIR}/${PLUGIN_NAME}" reset --hard
    git -C "${PLUGIN_ROOT_DIR}/${PLUGIN_NAME}" clean -fd
    if git -C "${PLUGIN_ROOT_DIR}/${PLUGIN_NAME}" pull; then
        echo "[INFO] Update complete!"
    else
        echo "[ERROR] Failed to update repository!"
        exit 1
    fi
else
    echo "[INFO] Downloading statechange_gcode repository..."
    if git -C "${PLUGIN_ROOT_DIR}" clone "${PLUGIN_GIT}" "${PLUGIN_NAME}"; then
        echo "[INFO] Download complete!"
    else
        echo "[ERROR] Download from git repository failed!"
        exit 1
    fi
fi

PLUGIN_INST_CMD "${PLUGIN_DEST}"

echo "Detected install: ${KLIPPER_PATH}"
echo "Linked ${PLUGIN_NAME} to ${PLUGIN_DEST}"
echo "Restart Klipper/Kalico (firmware restart) to load the plugin."
