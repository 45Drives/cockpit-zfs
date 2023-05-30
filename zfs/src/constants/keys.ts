export const injectionKeys = {
  pool : {
    name: 'pool_name',
    vDevs: 'pool_vdevs',
    sector: 'pool_sector_size',
    record: 'pool_record_size',
    compression: 'pool_compression',
    refreservation: 'pool_refreservation',
    autoExpand: 'pool_auto_expand',
    autoReplace: 'pool_auto_replace',
    autoTrim: 'pool_auto_trim',
    forceCreate: 'pool_force_create',
    fileSystem: 'pool_file_system',
    totalSize: 'pool_total_size',
    storageUsed: 'pool_storage_used',
    storageFree: 'pool_storage_free',
    usagePercent: 'pool_usage_percent',
  },
  vDevs : {
    type: 'vdev_type',
    disks: 'vdev_disks',
    isPrimary: 'vdev_is_primary',
    forceAdd: 'vdev_force_add',
  },
  disk : {
    name: 'disk_name',
    type: 'disk_type',
    totalSize: 'disk_total_size',
    storageUsed: 'disk_storage_used',
    storageFree: 'disk_storage_free',
    usagePercent: 'disk_usage_percent',
  },
  fileSystem : {
    name: 'filesystem_name',
    encryption: 'filesystem_encryption',
    passphrase: 'filesystem_passphrase',
    inherit: 'filesystem_inheirit',
    accessTime: 'filesystem_access_time',
    caseSensitivity: 'filesystem_case_sensitivity',
    compression: 'filesystem_compression',
    deduplication: 'filesystem_deduplication',
    dNodeSize: 'filesystem_d_node_size',
    extendedAttributes: 'filesystem_external_attributes',
    recordSize: 'filesystem_record_size',
    quota: 'filesystem_quota',
    readOnly: 'filesystem_read_only',
  }
}