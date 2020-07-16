from schematics import Model
from schematics.types import ListType, ModelType, PolyModelType
from spaceone.inventory.model.metadata.metadata_dynamic_layout import BaseLayoutField, ItemDynamicLayout, \
    SimpleTableDynamicLayout, TableDynamicLayout


class MetaDataViewSubData(Model):
    layouts = ListType(PolyModelType(BaseLayoutField))


class MetaDataView(Model):
    sub_data = PolyModelType(MetaDataViewSubData, serialize_when_none=False)


class ServerMetadata(Model):
    view = ModelType(MetaDataView)

    @classmethod
    def set_layouts(cls, layouts=[]):
        sub_data = MetaDataViewSubData({'layouts': layouts})
        return cls({'view': MetaDataView({'sub_data': sub_data})})
