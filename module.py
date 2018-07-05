"""
Deploy ceph-osd on remote hosts
"""

from mgr_module import MgrModule
import devices

try:
    from remoto import Connection
except ImportError:
    Connection = None

class Module(MgrModule):
    COMMANDS = [
        {
            "cmd": "deployer scan name=host,type=CephString,req=true",
            "desc": "Scans and save the host drives",
            "perm": "r"
        },
        {
            "cmd": "deployer tag name=host,type=CephString,req=true "
                   "name=devices,type=CephString,req=true "
                   "name=type,type=CephChoices,strings=data|db|wal,req=true",
            "desc": "Tag OSDs for deployment",
            "perm": "r"
        },
        {
            "cmd": "deployer prepare name=host,type=CephString,req=true",
            "desc": "Prepare tagged OSDs",
            "perm": "r"
        },
        {
            "cmd": "deployer activate name=host,type=CephString,req=true "
                   "name=concurrency,type=CephInt,req=false",
            "desc": "Activate <concurrency> times prepared OSDs at a time",
            "perm": "r"

        },
        {
            "cmd": "deployer status",
            "desc": "Display status of deployment",
            "perm": "r"

        }
    ]

    @staticmethod
    def can_run():
        if Connection is not None:
            return True, ""
        else:
            return False, "python-remoto missing"


    #XXX add OPTIONS for vg_prefix and lv_prefix?

    def handle_deployer_scan(self, host):
        conn = Connection(host)
        remote_devices = conn.import_module(devices)
        host_drives_infos = remote_devices.list()
        #XXX store host_drives_infos in K/V store

        return 0, str(host_drives_infos), ""

    def handle_deployer_tag(self, host, devices, type):
        #XXX check if host was scan and compare to used drives if not -> return error

        if devices.startswith('sd'):
            device_list = []
            #is partion?
            if devices[-1:].isdigit():
                return 134, "", "Error: Partitions are not supported."
            #range or single dev?
            if devices[-1:] is ']':
                device_prefix, devices_tail = devices.split('[')
                devices_tail = devices_tail[:-1]
                #expand range
                begin, end = devices_tail.split(':')
                for device in [chr(i) for i in range(ord(begin), ord(end)+1)]:
                    device_list.append(device_prefix + device)
            else:
                device_list.append(devices)
        else:
            return 134, "", "Error: Only sd* devices are supported."

        #tag the devices
        device_tag = {}
        device_tag[host] = {}
        for dev in device_list:
            device_tag[host][dev] = { 'status': 'tagged', 'type': type }

        #XXX need to merge jsons if get_store_json('tags')[host] returns something
        self.set_store_json('tags', device_tag)

        #XXX copy bootstrap-osd keyring && ceph.conf

        return 0, str(device_tag), ""

    def handle_deployer_prepare(self, host):
        #XXX couple of things that need to happen
        # get the tags
        # based of the tags distribute db, wal evenly
        # accross data drives or using whatever best rec. we have
        # Run ceph-volume. Ideally we want to run the lvm stuff
        # ourselves to have better names than defaults
        # checks are sync. Commands over SSH should be switched to async
        # with stdout,stderr logged. A `ceph deployer status`
        # ought to be provided to check on the status of prepare

        #Check if host was scanned. If not error.
        #XXX Implement - need to store out. from scan 1st.
        #try:
        #    drive_info = self.get_store_json(host)[drive]
        #except:
        #    return 2, "", "Error: drive doesn't exist. Did you scan this host?"

        #XXX - not implemented in scan
        # if drive_info['used']:
        #     return 1, "" "Error: Drive is already used"



        #XXX do pv/vg/lv creation manually

        try:
            devices_to_prepare = self.get_store_json('tags')[host]
        except:
            return 2, "", "Error: couldnt' retrieve tags for this host"

        data_devices = []
        wal_devices = []
        db_devices = []
        for device in devices_to_prepare:
            dev_type = devices_to_prepare[device]['type']
            if dev_type == 'data':
                data_devices.append(device)
            if dev_type == 'wal':
                wal_devices.append(device)
            if dev_type == 'db':
                db_devices.append(device)

        #XXX do some magic with ^^^that^^^
        # Figure out data/wal/db auto distribution

        #only data works for now
        conn = Connection(host)
        remote_devices = conn.import_module(devices)

        deployer = {}
        deployer[host] = {}
        for dev in data_devices:
            deployer[host][dev] = {'type': 'data', 'wal': 'collocated', 'db': 'collocated'}
            returncode, stderr = remote_devices.run_ceph_volume_prepare(dev)
            if returncode != 0:
                deployer[host][dev]['status'] = "prepare_error"
                deployer[host][dev]['error'] = stderr
            else:
                deployer[host][dev]['status'] = "prepared"

            self.log.debug(deployer[host][dev])

        return 0, "Run ceph deployer status for errors (not implemented)", ""

    def handle_deployer_activate(self, cmd):
        concurrency = 2
        if concurrency in cmd:
            concurrency = cmd['concurrency']
        host = cmd['host']

        return 134, "", "Error: Not implemented"

    def handle_deployer_status(self):
        return 134, "", "Error: Not implemented"

    def handle_command(self, cmd):
        if cmd['prefix'] == "deployer scan":
            return self.handle_deployer_scan(cmd['host'])
        if cmd['prefix'] == "deployer tag":
            return self.handle_deployer_tag(cmd['host'], cmd['devices'], cmd['type'])
        if cmd['prefix'] == "deployer prepare":
            return self.handle_deployer_prepare(cmd['host'])
        if cmd['prefix'] == "deployer activate":
            return self.handle_deployer_activate(cmd)
        if cmd['prefix'] == "deployer status":
            return self.handle_deployer_status()
