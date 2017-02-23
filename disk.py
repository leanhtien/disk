import sys, os, fcntl, struct
import subprocess

with open(sys.argv[1], "rb") as fd:
    # tediously derived from the monster struct defined in <hdreg.h>
    # see comment at end of file to verify
    hd_driveid_format_str = "@ 10H 20s 3H 8s 40s 2B H 2B H 4B 6H 2B I 36H I Q 152H"
    # Also from <hdreg.h>
    HDIO_GET_IDENTITY = 0x030d
    # How big a buffer do we need?
    sizeof_hd_driveid = struct.calcsize(hd_driveid_format_str)

    # ensure our format string is the correct size
    # 512 is extracted using sizeof(struct hd_id) in the c code
    assert sizeof_hd_driveid == 512



    # Call native function
    buf = fcntl.ioctl(fd, HDIO_GET_IDENTITY, " " * sizeof_hd_driveid)
    #print buf
    fields = struct.unpack(hd_driveid_format_str, buf)
    serial_no = fields[10].strip()
    model = fields[15].strip()
    capability = buf[10].strip()

print("Hard Disk Model: %s" % model)
print("Serial Number: %s" % serial_no)
# print fields

pathMount = ""
# Get value mount point and compare
def _parse_proc_partitions():
    res = {}
    mount = ""
    for line in file("/proc/mounts"):
        fields = line.split()
        # print("line:", fields)
        try:
            if (fields[0] == sys.argv[1]):
                print("OK---", fields[1])
                pathMount = fields[1]
                disk = os.statvfs(pathMount)
                # Information is recieved in numbers of blocks free
                capacity = (disk.f_bsize * disk.f_blocks) / 1.073741824e9
                available = (disk.f_bsize * disk.f_bavail) / 1.073741824e9
                used = (disk.f_bsize * (disk.f_blocks - disk.f_bavail)) / 1.073741824e9
                # test = disk.f_flag
                print("Used: %sG" % round(used, 1))
                print("Available: %sG" % round(available, 1))
                print("Capacity: %sG" % round(capacity, 1))
        except:
            # just ignore parse errors in header/separator lines
            pass
    return res


print _parse_proc_partitions()
