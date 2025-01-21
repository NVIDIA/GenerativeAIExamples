#!/bin/bash

set -euo pipefail
echo "Starting NGC download script. Note: only glibc-based Linux works with NGC CLI -- NOT busybox or alpine"

if [ "$DOWNLOAD_NGC_CLI" = "true" ]; then
  NGC_WD="${DOWNLOAD_NGC_CLI_PATH:-/tmp}"
  if [ ! -x "$(which wget)" ]; then
    echo "To install ngc in the download image, wget is required"
    exit 1
  fi
  wget "https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/${NGC_CLI_VERSION}/files/ngccli_linux.zip" -O "$NGC_WD/ngccli_linux.zip"
  cd "$NGC_WD" && unzip ngccli_linux.zip
  chmod u+x ngc-cli/ngc
  NGC_EXE=$NGC_WD/ngc-cli/ngc
  export PATH=$PATH:$NGC_WD/ngc-cli
fi

# To ensure we actually have an NGC binary, switch to full path if default is used
if [ "$NGC_EXE" = "ngc" ]; then
  NGC_EXE=$(which ngc)
fi

# check if ngc cli is truly available at this point
if [ ! -x "$NGC_EXE" ]; then
  echo "ngc cli is not installed or available!"
  exit 1
fi

# download the model
directory="${STORE_MOUNT_PATH}/${NGC_MODEL_NAME}_v${NGC_MODEL_VERSION}"
echo "Directory is $directory"
ready_file="$directory/.ready"
lockdir="$directory/.lock"
mkdir -p "$directory"
set -o noclobber &&
if { mkdir "$lockdir"; }; then
  trap 'rm -f $lockdir' EXIT
  if [ ! -e "$ready_file" ]; then
    $NGC_EXE registry model download-version --dest "$STORE_MOUNT_PATH" "${NGC_CLI_ORG}/${NGC_CLI_TEAM}/${NGC_MODEL_NAME}:${NGC_MODEL_VERSION}"
    # decrypt the model - if needed (conditions met)
    if [ -n "${NGC_DECRYPT_KEY:+''}" ] && [ -f "$directory/${MODEL_NAME}.enc" ]; then
      echo "Decrypting $directory/${MODEL_NAME}.enc"
      # untar if necessary
      if [ -n "${TARFILE:+''}" ]; then
        echo "TARFILE enabled, unarchiving..."
        openssl enc -aes-256-cbc -d -pbkdf2 -in "$directory/${MODEL_NAME}.enc" -out "$directory/${MODEL_NAME}.tar" -k "${NGC_DECRYPT_KEY}"
        tar -xvf "$directory/${MODEL_NAME}.tar" -C "$STORE_MOUNT_PATH"
        rm "$directory/${MODEL_NAME}.tar"
      else
        openssl enc -aes-256-cbc -d -pbkdf2 -in "$directory/${MODEL_NAME}.enc" -out "$directory/${MODEL_NAME}" -k "${NGC_DECRYPT_KEY}"
      fi
      rm "$directory/${MODEL_NAME}.enc"
    else
      echo "No decryption key provided, or encrypted file found. Skipping decryption.";
      if [ -n "${TARFILE:+''}" ]; then
        echo "TARFILE enabled, unarchiving..."
        tar -xvf "$directory/${NGC_MODEL_VERSION}.tar.gz" -C "$STORE_MOUNT_PATH"
        rm "$directory/${NGC_MODEL_VERSION}.tar.gz"
      fi
    fi
    touch "$ready_file"
    echo "Done dowloading"
    rmdir "$lockdir"
  else
    echo "Download was already complete"
  fi;
else
  while [ ! -e "$ready_file" ]
  do
    echo "Did not get the download lock. Waiting for the pod holding the lock to download the files."
    sleep 1
  done;
  echo "Done waiting"
fi
set +o noclobber;
ls -la "$directory"
