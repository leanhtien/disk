#!/usr/bin/env python3

import sys
import pyudev
import os, fcntl, struct

BYTES_IN_GiB = 2 ** 30

def main():

    if os.getuid() < 0:
        print('You must run as root')
        sys.exit()

    context = pyudev.Context()
    for dev in get_device_list(context):
        print_device(dev)
        return

def get_device_list(context):
    devices = []
    for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
        if device.get('ID_TYPE', None) != 'disk':
            continue
        if device.get('UDISKS_PRESENTATION_NOPOLICY', '0') == '1':
            continue
        devices.append(device)

    return devices

def get_mount_points(sys_name):
    """Returns mount points for device 'sys_name'."""
    mount_points = []
    with open('/etc/mtab') as f:
        for line in f.readlines():
            if line.find(sys_name) != -1:
                _, path, _ = line.split(' ', 2)
                mount_points.append(path.replace('\\040', ' '))
    return mount_points


def get_free_space(sys_name):
    free_space = 0
    for mount_point in get_mount_points(sys_name):
        stat = os.statvfs(mount_point)
        free_space += stat.f_bsize * stat.f_bfree
    return free_space


def print_device(device):
    device_info = decode_device_info(device)
    print('--- Device: /dev/' + device.sys_name + ' ---')
    print_space_inforamtion(device.sys_name)
    for key in device_info.keys():
        if(device_info[key]):
            print('%s: %s' % (key.capitalize().replace('_', ' '),
                              device_info[key]))
    #print(get_drive_modes(device))
    print('------ \n')

def print_modes(drive_fields):
    serial_no = drive_fields[10].strip()
    model = drive_fields[15].strip()

    capabilities = drive_fields[20]
    capabilities = decode_compatibility(drive_fields[20] & 0xB)

   # dma_modes = decode_dma(drive_fields[36])
   # pio_modes = decode_pio(drive_fields[37])
    #interface_version = decode_interface(drive_fields[54])

    print('Device capabilities: {}'.format(capabilities))
    #print('DMA modes : {}'.format(dma_modes))
    #print('PIO modes : {}'.format(pio_modes))
    #print('Primary interface : {}'.format(interface_version))

def decode_compatibility(word):
    modes = {0x1: 'DMA' , 0x2: 'LBA', 0x8: 'IORDYsup'}

    result = ''
    for i in [0x1, 0x2, 0x8]:
        if i & word == i:
            result += '{} '.format(modes[i])

    return result

def decode_dma(word):
    modes = {0x1: 'mdma0' , 0x2: 'mdma1', 0x4: 'mdma2'}

    result = ''
    for i in [0x1, 0x2, 0x4]:
        if i & word == i:
            result += '{} '.format(modes[i])

    return result

def decode_pio(word):
    modes = {0x1: 'pio3' , 0x2: 'pio4'}

    result = 'pio0 pio1 pio2 '
    for i in [0x1, 0x2]:
        if i & word == i:
            result += '{} '.format(modes[i])

    return result

def decode_interface(word):

    if word & 0xFC != 0x0:
        version = 'ATA-4/ATAPI+'
    else:
        version = 'ATA-4'

    result = '{} '.format(version)
    return result

def print_space_inforamtion(sys_name):
    os.chdir('/sys/block/' + sys_name)

    with open('size') as size_file:
        drive_cluster_size = int(size_file.readline())

    size_in_bytes = drive_cluster_size * 512
    free_space = get_free_space(sys_name)
    used_space = size_in_bytes - free_space

    print('Drive size: ' + str(size_in_bytes) +
          ' B [' + str(size_in_bytes / BYTES_IN_GiB) + ' GiB]')
    print('Used space: ' + str(used_space) +
          ' B [' + str(used_space / BYTES_IN_GiB) + ' GiB]')
    print('Free space: ' + str(free_space) +
          ' B [' + str(free_space / BYTES_IN_GiB) + ' GiB]')

def get_drive_modes(device):
    with open('/dev/' + device.sys_name, "r") as fd:
        hd_driveid_format_str = "@ 10H 20s 3H 8s 40s 2B H 2B H 4B 6H 2B I 36H I Q 152H"
        HDIO_GET_IDENTITY = 0x030d
        sizeof_hd_driveid = struct.calcsize(hd_driveid_format_str)

        assert sizeof_hd_driveid == 512

        buf = fcntl.ioctl(fd, HDIO_GET_IDENTITY, " " * sizeof_hd_driveid)
        fields = struct.unpack(hd_driveid_format_str, buf)

        return fields


def replace_underscores(string):
    if string:
        return string.replace('_', ' ')

def capitalize(string):
    if string:
        return string.upper()

def decode_device_info(device):
    serial = device.get('ID_SERIAL_SHORT')
    if not serial:
        serial = device.get('ID_SERIAL')
    return({'vendor': replace_underscores(device.get('ID_VENDOR')),
            'model': (device.get('ID_MODEL')),
            'serial': serial,
            'bus': capitalize(device.get('ID_BUS')),
            'firmware_version': capitalize(device.get('ID_REVISION')),
            'table_type': capitalize(device.get('ID_PART_TABLE_TYPE'))})

if __name__ == '__main__':
    sys.exit(main())
