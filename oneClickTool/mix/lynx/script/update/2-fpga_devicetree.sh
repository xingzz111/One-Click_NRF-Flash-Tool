#!/bin/bash

# device tree update script
PACKAGE_FILES=("devicetree.dtb" "fpga.bit")
PACKAGE_SOURCE_PATH=

set +e

Usage()
{
cat <<EOF
Usage:
$0 <fw_update_temp_folder_path>
EOF
}

if [ "$#" -lt 1 ] ;then
    Usage
    exit 0
fi

PACKAGE_SOURCE_PATH=$1

do_exit(){
    umount /mnt 2>/dev/null
    umount /mnt 2>/dev/null
    umount /mnt 2>/dev/null
}

# Function to update a package
update_package() {
    local PACKAGE_FILE_NAME=$1

    echo "update package is '$PACKAGE_FILE_NAME'"
    # Check if package file exists
    if [ ! -f $PACKAGE_SOURCE_PATH/$PACKAGE_FILE_NAME ]; then
        echo "$PACKAGE_FILE_NAME does not exist."
        return 1
    fi

    echo "'$PACKAGE_FILE_NAME' updating..."

    echo "mount emmc device"
    do_exit
    mount /dev/mmcblk0p1 /mnt
    if [ $? -ne 0 ]; then
        echo "mount EMMC device failed."
        do_exit
        return 2
    fi

    echo "updating ..."
    rm -rf /mnt/$PACKAGE_FILE_NAME
    cp $PACKAGE_SOURCE_PATH/$PACKAGE_FILE_NAME /mnt/
    if [ $? -ne 0 ]; then
        echo "Update failed"
        do_exit
        return 3
    fi
    echo "Update '$PACKAGE_FILE_NAME' finished"
    return 0
}

# Loop through each package file
for PACKAGE_FILE_NAME in "${PACKAGE_FILES[@]}"; do
    if update_package "$PACKAGE_FILE_NAME"; then
        continue
    else
        exit_code=$?
        if [ $exit_code -eq 1 ]; then
            echo "No files to update."
            continue
        else
            exit $exit_code
        fi
    fi
done

sync 
sleep 1
do_exit

exit 0
