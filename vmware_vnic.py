#-------------------------------------------------------------------------------
# Name:        vmware_vnic
# Purpose:     Remove VNIC's from VM on VMware
#
# Author:      Mohd Umar Mubeen
#
# Created:     22-05-2018
# Copyright:   (c) umar 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import re
import time
import pyVmomi
from pyVmomi import vim, vmodl
from tools import tasks
from pyVim.connect import SmartConnect, Disconnect
import atexit
import argparse
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.vmware import (find_obj, gather_vm_facts, get_all_objs,
                                         compile_folder_path_for_object, serialize_spec,
                                         vmware_argument_spec, set_vm_power_state, PyVmomi)


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def remove_vnic(si, vm, nic_number):
    nic_prefix_label = 'Network adapter '
    nic_label = nic_prefix_label + str(nic_number)
    virtual_nic_device = None
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard)   \
                and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    if not virtual_nic_device:
        raise RuntimeError('Virtual {} could not be found.'.format(nic_label))

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = \
        vim.vm.device.VirtualDeviceSpec.Operation.remove
    virtual_nic_spec.device = virtual_nic_device

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [virtual_nic_spec]
    task = vm.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])
    return True

def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(hostname=dict(type='str', required=True),
                              username=dict(type='str', required=True),
                              password=dict(type='str', required=True),
                              port=dict(type='int', default='443'),
                              vm_name=dict(type='str', required=True),
                              uuid=dict(type='int', required=True),
                              nic_number=dict(type='int', required=True)))
    module = AnsibleModule(argument_spec=argument_spec)

    # connect this thing
    serviceInstance = SmartConnect(
            host=module.hostname,
            user=module.username,
            pwd=module.password,
            port=module.port)
    # disconnect this thing
    atexit.register(Disconnect, serviceInstance)

    vm = None
    if args.uuid:
        search_index = serviceInstance.content.searchIndex
        vm = search_index.FindByUuid(None, args.uuid, True)
    elif args.vm_name:
        content = serviceInstance.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], args.vm_name)

    if vm:
        remove_vnic(serviceInstance, vm, int(args.nic_number))
    else:
        print ("VM not found")

# start this thing
if __name__ == "__main__":
    main()
