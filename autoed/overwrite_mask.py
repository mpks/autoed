#!/usr/bin/env python3
import h5py
import hdf5plugin
import numpy as np
import matplotlib.pyplot as plt


file_path = '20231011_1006_nav34_-24.-250.211.__master.h5'


def copy_h5py(name, source, dest):
    if isinstance(source, h5py.Dataset):
        dest.create_dataset(name, data=source[()], dtype=source.dtype)
        for attr_name, attr_value in source.attrs.items():
            dest[name].attrs[attr_name] = attr_value
    elif isinstance(source, h5py.Group):
        dest.create_group(name)


with h5py.File(file_path, 'r') as source:
    with h5py.File('master.h5', 'w') as dest:
        source.visititems(lambda name, obj: copy_h5py(name, obj,
                          dest))
        src = '/entry/instrument/detector/detectorSpecific/pixel_mask'
        dataset = dest[src]
        print(dataset.shape, dataset.dtype)
        data = np.load('mask.npz')
        mask = data['mask']
        print(mask.shape)
        dataset[...] = mask.astype(dataset.dtype)

#        entry_attr = source['/entry/data/data'].attrs
#        dentry_attr = dest['/entry/data/data'].attrs
#        for attr_name, attr_value in entry_attr.items():
#            if attr_name is not 'image_nr_high':
#                dentry_attr[attr_name] = attr_value
#            else:
#                dentry_attr['image_nr_high'] = 1
