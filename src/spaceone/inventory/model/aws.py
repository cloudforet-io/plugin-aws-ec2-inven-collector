from schematics import Model
from schematics.types import ModelType, StringType, BooleanType, DateTimeType, IntType, ListType


class CapacityReservationTarget(Model):
    capacity_reservation_id = StringType(deserialize_from='CapacityReservationId')
    capacity_reservation_resource_group_arn = StringType(deserialize_from='CapacityReservationResourceGroupArn')


class CapacityReservationSpecification(Model):
    capacity_reservation_preference = StringType(choices=('open', 'none'),
                                                 deserialize_from='CapacityReservationPreference')
    capacity_reservation_target = ModelType(CapacityReservationTarget,
                                            deserialize_from='CapacityReservationTarget')


class Placement(Model):
    availability_zone = StringType(deserialize_from='AvailabilityZone')
    affinity = StringType(deserialize_from='Affinity')
    group_name = StringType(deserialize_from='GroupName')
    partition_number = IntType(deserialize_from='PartitionNumber')
    host_id = StringType(deserialize_from='HostId')
    tenancy = StringType(choices=('default', 'dedicated', 'host'), deserialize_from='Tenancy')
    spread_domain = StringType(deserialize_from='SpreadDomain')
    host_resource_group_arn = StringType(deserialize_from='HostResourceGroupArn')
    group_id = StringType(deserialize_from='GroupId')


class ElasticGPUAssociation(Model):
    elastic_gpu_id = StringType(deserialize_from='ElasticGpuId')
    elastic_gpu_association_id = StringType(deserialize_from='ElasticGpuAssociationId')
    elastic_gpu_association_state = StringType(deserialize_from='ElasticGpuAssociationState')
    elastic_gpu_association_time = DateTimeType(deserialize_from='ElasticGpuAssociationTime')


class ElasticInferenceAcceleratorAssociation(Model):
    elastic_inference_accelerator_arn = StringType(deserialize_from='ElasticInferenceAcceleratorArn')
    elastic_inference_accelerator_association_id = StringType(deserialize_from='ElasticInferenceAcceleratorAssociationId')
    elastic_inference_accelerator_association_state = StringType(deserialize_from='ElasticInferenceAcceleratorAssociationState')
    elastic_inference_accelerator_association_time = DateTimeType(deserialize_from='ElasticInferenceAcceleratorAssociationTime')


class AWSIAMInstanceProfile(Model):
    id = StringType(deserialize_from='Id')
    arn = StringType(deserialize_from='Arn')


class AWS(Model):
    ami_id = StringType()
    ami_launch_index = IntType()
    kernel_id = StringType()
    monitoring_state = StringType(choices=('disabled', 'disabling', 'enabled', 'pending'))
    ebs_optimized = BooleanType()
    root_volume_type = StringType()
    ena_support = BooleanType()
    hypervisor = StringType(choices=('ovm', 'xen'))
    placement = ModelType(Placement)
    iam_instance_profile = ModelType(AWSIAMInstanceProfile)
    termination_protection = BooleanType()
    lifecycle = StringType(choices=('spot', 'scheduled'))
    auto_recovery = StringType(choices=('disabled', 'default'))
    boot_mode = StringType(choices=('legacy-bios', 'uefi', 'uefi-preferred'))
    current_instance_boot_mode = StringType(choices=('legacy-bios', 'uefi'))
    tpm_support = StringType()
    platform_details = StringType()
    usage_operation = StringType()
    usage_operation_update_time = DateTimeType()
    enclave_options = BooleanType()
    hibernation_options = BooleanType()
    state_transition_reason = StringType()
    source_desk_check = BooleanType()
    sriov_net_support = StringType()
    elastic_gpu_associations = ListType(ModelType(ElasticGPUAssociation))
    elastic_inference_accelerator_associations = ListType(ModelType(ElasticInferenceAcceleratorAssociation))
    capacity_reservation_id = StringType()
    capacity_reservation_specification = ModelType(CapacityReservationSpecification)

