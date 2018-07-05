# Deployer module for ceph-mgr

Really you shouldn't use that at all. Just an experiment to learn about ceph-mgr module development.
It also requires to run ceph-mgr daemons as root

Deps: `python-remoto`

## Concept

1. Scan your host
2. Tag the OSDs you want to deploy with data, the WAL and DB devices with wal and db
3. When running prepare we automatically distribute WAL and DB devices amongst data tagged OSDs

The neat thing is that tagging accepts ranges (i.e. sd[a:z]) or just a single device

## Gaps
Too many to list.

## Commands

```
[root@cephdev ~]# ceph deployer -h | tail -n 7
 Monitor commands:
 =================
deployer activate <host> {<int>}                                                  Activate <concurrency> times prepared OSDs at a time
deployer prepare <host>                                                           Prepare tagged OSDs
deployer scan <host>                                                              Scans and save the host drives
deployer status                                                                   Display status of deployment
deployer tag <host> <devices> data|db|wal                                         Tag OSDs for deployment
```

```
[root@cephdev ~]# ceph deployer scan cephdev2
{'sdd': {'rotational': '1', 'vendor': 'ATA', 'size_byte': 54811164672, 'used': 'N/A', 'model': 'VBOX HARDDISK', 'ceph_used': 'N/A'}, 'sda': {'rotational': '1', 'vendor': 'ATA', 'size_byte': 10737418240, 'used': 'N/A', 'model': 'VBOX HARDDISK', 'ceph_used': 'N/A'}, 'sdb': {'rotational': '0', 'vendor': 'ATA', 'size_byte': 53687091200, 'used': 'N/A', 'model': 'VBOX HARDDISK', 'ceph_used': 'N/A'}, 'sdc': {'rotational': '1', 'vendor': 'ATA', 'size_byte': 53687091200, 'used': 'N/A', 'model': 'VBOX HARDDISK', 'ceph_used': 'N/A'}}
```

```
[root@cephdev ~]# ceph deployer tag cephdev2 sd[b:d] data
{'cephdev2': {'sdd': {'status': 'tagged', 'type': 'data'}, 'sdb': {'status': 'tagged', 'type': 'data'}, 'sdc': {'status': 'tagged', 'type': 'data'}}}
```

```
[root@cephdev ~]# ceph deployer prepare cephdev2
Run ceph deployer status for errors (not implemented)
```

```
[root@cephdev ~]# ceph osd stat
3 osds: 0 up, 0 in; epoch: e18
```

```
[root@cephdev ~]# ssh cephdev2 lsblk
NAME                                                                                                  MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda                                                                                                     8:0    0   10G  0 disk
├─sda1                                                                                                  8:1    0    1G  0 part /boot
└─sda2                                                                                                  8:2    0    9G  0 part
  ├─centos_cephdev2-root                                                                              253:0    0    8G  0 lvm  /
  └─centos_cephdev2-swap                                                                              253:1    0    1G  0 lvm  [SWAP]
sdb                                                                                                     8:16   0   50G  0 disk
└─ceph--19bd0228--fc77--4aa4--8018--f5e936b21892-osd--block--9c45f9c0--7ce6--4a2c--893b--d7658d6fdb37 253:3    0   50G  0 lvm
sdc                                                                                                     8:32   0   50G  0 disk
└─ceph--85b9ffa7--01b2--485d--94af--4c5d3db14069-osd--block--c989ece1--d6b6--472f--8f91--0ff5d5f8c09f 253:4    0   50G  0 lvm
sdd                                                                                                     8:48   0   51G  0 disk
└─ceph--da43cae8--d588--466b--a65e--ae36ae7766c2-osd--block--96790c65--55e1--49b4--b757--d1bc608c1eeb 253:2    0   51G  0 lvm
```
