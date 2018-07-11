import os
from subprocess import Popen, PIPE

def read_all(f):
  fd = open(f, 'r')
  data = fd.read()
  fd.close()
  return data

def list():
    host_drives_infos = {}

    #list /sys/block. For each sd*, nvme*
    #check: infos, used, used_by_ceph,
    for device in os.listdir('/sys/block'):
        if device.startswith('sd') or device.startswith('nvme'):
            host_drives_infos[device] = {}
            path_prefix = '/sys/block/' + device + '/'
            host_drives_infos[device]['size_byte'] = int(read_all(path_prefix + 'size')) * int(read_all(path_prefix + 'queue/hw_sector_size'))
            host_drives_infos[device]['model'] = read_all(path_prefix + 'device/model').strip()
            host_drives_infos[device]['vendor'] = read_all(path_prefix + 'device/vendor').strip()
            host_drives_infos[device]['rotational'] = read_all(path_prefix + 'queue/rotational').strip()
            #XXX implement below; check if mounted and if OSD -> whoami
            host_drives_infos[device]['used'] = 'N/A'
            host_drives_infos[device]['ceph_used'] = 'N/A'

    return host_drives_infos

def run_ceph_volume_prepare(data, wal=None, db=None):

    command = ['/usr/sbin/ceph-volume',
               'lvm', 'prepare',
               '--data', '/dev/' + str(data)]

    if wal is not None:
        command.extend(('--block.wal', '/dev/'+str(wal)))
    if db is not None:
        command.extend(('--block.db', '/dev/'+str(db)))

    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    _, stderr = p.communicate()

    return p.returncode, stderr

if __name__ == '__channelexec__':
    for item in channel:
        channel.send(eval(item))
