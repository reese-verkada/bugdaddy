#!/bin/sh
set -u -e
source /usr/bin/verkada_logging.sh

updating=/tmp/updating
touch $updating
trap "rm -f $updating && sync" EXIT


MACHINE_EXT=$(echo -n $(cat /etc/machine_type || true))
if [ ! -z "${MACHINE_EXT}" ]; then
    MACHINE_EXT="${MACHINE_EXT}"
fi

if [ -e /etc/default/verkada_upgrade_auto ]; then
    . /etc/default/verkada_upgrade_auto
else
    # Default values to support upgrades from pre-201908 versions
    # REMEMBER manufacturing versions can be very old and we want
    # to support direct upgrades to the latest version.
    case "${MACHINE_EXT}" in
    bouncer-evk)
        KERNEL_A=mtd7
        KERNEL_B=mtd9
        DTB_A=mtd6
        DTB_B=mtd8
        M4CORE_A=mtd17
        M4CORE_B=mtd18
        UBOOT_FIT=mtd1
        UBOOT=mtd0
        ;;
    bouncer)
        KERNEL_A=mtd7
        KERNEL_B=mtd9
        DTB_A=mtd6
        DTB_B=mtd8
        M4CORE_A=mtd17
        M4CORE_B=mtd18
        UBOOT_FIT=mtd1
        UBOOT=mtd0
        ;;
    esac
fi

KERNEL_ONLY="false"
FS_ONLY="false"
APP_ONLY="false"
BOOTLOADER_UPGRADE="false"

case $1 in
    --kernel)
        KERNEL_ONLY="true"
        shift
        ;;
    --rootfs)
        FS_ONLY="true"
        shift
        ;;
    --app)
        APP_ONLY="true"
        shift
        ;;
    --bootloader)
        BOOTLOADER_UPGRADE="true"
        shift
        ;;
esac

if [ "$1" = "" ]; then
    echo "usage: $0 [--kernel|--rootfs] <update-version>"
    exit 1
fi
#TODO Upgrade doesnt exit on fail
#touch /tmp/led_upgrading TODO
ACTIVE=$(mount | grep "on / " | grep -v "rootfs (rw)" | cut -d' ' -f 1 | cut -d_ -f 2)
COMMITTED=$(fw_printenv active | cut -d= -f 2)

if [ "$ACTIVE" != "$COMMITTED" ]; then
    echo "Refusing to upgrade again until previous upgrade is committed."
    exit 1
fi

UPGRADE="/dev/ubi2_0"
DEV_NO=0

if [ -f /mnt/config/verkada_upgrade_auto_source ] && [ "$#" == "0" ]; then
    MIRROR=$(cat /mnt/config/verkada_upgrade_auto_source)
    VERSION=""
    echo "Upgrading to latest dev version"
else
    #default download 
    SERVER="$(jq -er '.vcerberus' /mnt/config/server_override.json 2>/dev/null || echo 'https://vcerberus.command.verkada.com')"
    MIRROR="$(jq -er '."system-config"."sys-firmware-url" | select(. != null)' /mnt/config/config 2>/dev/null || echo "$SERVER/access_controller/firmware")"
    VERSION="${1}"
    echo "Upgrading to version ${1}"
fi

TMPDIR=/mnt/ramdisk/upgrade

rm -rf "$TMPDIR"
mkdir -p "$TMPDIR"

cd "$TMPDIR"

SECURITY_TOKEN=$(cat /mnt/config/security_token)

#Download Upgrade Manifest
curl -k -s -S -o upgrade.manifest -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$MIRROR/${VERSION}-${MACHINE_EXT}.manifest"
jq -e .machine upgrade.manifest
ret_val=$?
if [ "$ret_val" -ne "0" ]; then
    echo "Malformed Upgrade Manifest"
    log_without_reboot "Malformed Upgrade Manifest: $(jq -e .machine upgrade.manifest)"
    exit 1
fi

#upgrade bootloader proceed with caution
if [ "${BOOTLOADER_UPGRADE}" != "true" ]; then
    echo "Leaving bootloader as is ( No bootloader update for this upgrade)"
else

     
    echo "Upgrading bootloader, this is could be potentially fatal"
    echo  "Downloading bootloader..."
    BOOTLOADERIMAGE=$(jq -r .bootloader_version upgrade.manifest)
    curl -k -s -S -o "$BOOTLOADERIMAGE" -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$(echo "$MIRROR/$BOOTLOADERIMAGE" | sed 's/+/%2B/g')"
    #TODO: check checksum before proceeding

    if [ -z "$BOOTLOADERIMAGE" ]; then
        echo "Error, bootloader version not found"
        exit 1
    else
        flash_erase "/dev/$UBOOT" 0 0
        kobs-ng init -x -v --chip_0_device_path=/dev/${UBOOT} ${BOOTLOADERIMAGE}
        flash_erase "/dev/$UBOOT_FIT" 0 0
        nandwrite -p "/dev/$UBOOT_FIT" "$BOOTLOADERIMAGE"
    fi

fi



if [ "${FS_ONLY}" != "true" ] && [ "${APP_ONLY}" != "true" ];  then
    
    echo  "Downloading kernel..."
    KERNEL=$(jq -r .kernel_version upgrade.manifest)
    DTB=$(jq -r .dtb_version upgrade.manifest)
    M4IMAGE=$(jq -r .m4image_version upgrade.manifest)
    
    if [ -n "$KERNEL" ]; then
        curl -k -s -S -o "$KERNEL" -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$(echo "$MIRROR/$KERNEL" | sed 's/+/%2B/g')"
        dwnld_chksum=$(sha1sum $KERNEL | awk '{ print $1 }')
        manifest_chksum=$(jq -r .kernel_chksum upgrade.manifest)

        if [ "$dwnld_chksum" != "$manifest_chksum" ]; then

            echo "Kernel Checksum Mismatch $dwnld_chksum != $manifest_chksum"
            exit 1
        fi
    fi
    
    if [ -n "$DTB" ]; then
        curl -k -s -S -o "$DTB" -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$(echo "$MIRROR/$DTB" | sed 's/+/%2B/g')"
        dwnld_chksum=$(sha1sum $DTB | awk '{ print $1 }')
        manifest_chksum=$(jq -r .dtb_chksum upgrade.manifest)

        if [ "$dwnld_chksum" != "$manifest_chksum" ]; then

            echo "DTB Checksum Mismatch $dwnld_chksum != $manifest_chksum"
            exit 1
        fi
    fi

    if [ -n "$M4IMAGE" ]; then
        curl -k -s -S -o "$M4IMAGE" -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$(echo "$MIRROR/$M4IMAGE" | sed 's/+/%2B/g')"
        dwnld_chksum=$(sha1sum $M4IMAGE | awk '{ print $1 }')
        manifest_chksum=$(jq -r .m4image_chksum upgrade.manifest)

        if [ "$dwnld_chksum" != "$manifest_chksum" ]; then

            echo "M4Image Checksum Mismatch $dwnld_chksum != $manifest_chksum"
            exit 1
        fi
    fi
    
    #TODO: checksum before proceeding
    if [ "$ACTIVE" == "b" ]; then
  
        if [ -z "$KERNEL" ]; then
            echo "Not upgrading kernel"
        else

           flash_erase "/dev/$KERNEL_A" 0 0
           nandwrite -p "/dev/$KERNEL_A" "$KERNEL"
        fi

        if [ -z "$DTB" ]; then
            echo "Not upgrading dtb"
        else
            
            flash_erase "/dev/$DTB_A" 0 0
            nandwrite -p "/dev/$DTB_A" "$DTB"
        fi

        if [ -z "$M4IMAGE" ]; then
            echo "Not upgrading m4core_a"
        else
            
            flash_erase "/dev/$M4CORE_A"  0 0
            nandwrite -p "/dev/$M4CORE_A" "$M4IMAGE"
        fi

    else

        if [ -z "$KERNEL" ]; then
            echo "Not upgrading kernel"
        else
           flash_erase "/dev/$KERNEL_B" 0 0
           nandwrite -p "/dev/$KERNEL_B" "$KERNEL"
        fi

        if [ -z "$DTB" ]; then
            echo "Not upgrading dtb"
        else
            flash_erase "/dev/$DTB_B" 0 0
            nandwrite -p "/dev/$DTB_B" "$DTB"
        fi

        if [ -z "$M4IMAGE" ]; then
            echo "Not upgrading m4core_b"
        else
            flash_erase "/dev/$M4CORE_B"  0 0
            nandwrite -p "/dev/$M4CORE_B" "$M4IMAGE"
        fi

    fi

    if [ "${KERNEL_ONLY}" = "true" ]; then
        fw_setenv trialboot 1
        exit 0
    fi
fi


if [ "${APP_ONLY}" != "true" ];  then
    # upgrade rootfs
    ROOTFS=$(jq -r .rootfs_version upgrade.manifest)

    if [ -z "$ROOTFS" ]; then
        echo "Not upgrading rootfs"
    else
        ROOTSIZE=$(curl -k -s -S -I -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$MIRROR/$ROOTFS" | grep -i 'Content-Length' | tail -n 1 | awk '{print $2}')
        CUR_ROOTSIZE=$( ubinfo -d 2 -n 0 | grep Size | awk '{print $4}' | tr -d \( )
        if [ ${CUR_ROOTSIZE} -lt ${ROOTSIZE} ] ; then
            echo resizing volume to ${ROOTSIZE}
            ubirsvol /dev/ubi2 -n 0 -s ${ROOTSIZE}
        fi

        echo "Streaming new rootfs to $UPGRADE..."
        curl -k -s -S -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$MIRROR/$ROOTFS" | ubiupdatevol "$UPGRADE" -s "$ROOTSIZE" -

        fw_setenv trialboot 1
        
    fi
fi


# upgrade app partition
APP_PARTITION=$(jq -r .verkada_app_version upgrade.manifest)
TRIAL_FILE=/mnt/config/trial

if [ -z "$APP_PARTITION" ] ||  test -f "$TRIAL_FILE" ; then

    echo "Refusing to upgrade, check if trial file exists or app version exists"
    exit 1
else
        APP_ACTIVE="a"
        APP_ACTIVE_FILE=/mnt/config/active

        if test -f "$APP_ACTIVE_FILE"; then
            APP_ACTIVE="$(cat ${APP_ACTIVE_FILE})"
        else 
            echo ${APP_ACTIVE} > ${APP_ACTIVE_FILE}
        fi
        APP_UBI_PART=4
        if [ "$APP_ACTIVE" != "a" ]; then
            APP_UBI_PART=3
        fi

        APP_UPGRADE="/dev/ubi${APP_UBI_PART}_0"
        RUNNING_VERKADA=$(cat /mnt/config/active)
        APPSIZE=$(curl -k -s -S -I -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$MIRROR/$APP_PARTITION" | grep -i 'Content-Length' | tail -n 1 | awk '{print $2}')
        CURR_APP_SIZE=$( ubinfo -d ${APP_UBI_PART} -n 0 | grep Size | awk '{print $4}' | tr -d \( )
        if [ ${CURR_APP_SIZE} -lt ${APPSIZE} ] ; then
            echo resizing volume to ${APPSIZE}
            ubirsvol /dev/ubi${APP_UBI_PART} -n 0 -s ${APPSIZE}
        fi

        echo "Streaming new app partition to $APP_UPGRADE..."
        curl -k -s -S -L -H "X-Verkada-Auth: ${SECURITY_TOKEN}" "$MIRROR/$APP_PARTITION" | ubiupdatevol "$APP_UPGRADE" -s "$APPSIZE" -

        unmount_active_app
        touch $TRIAL_FILE
        sync
        mount_active_app

fi



rm -rf "$TMPDIR"
