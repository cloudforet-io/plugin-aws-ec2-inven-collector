from schematics import Model
from schematics.types import ListType, ModelType, PolyModelType
from spaceone.inventory.model.metadata.metadata_dynamic_layout import BaseLayoutField
from spaceone.inventory.model.metadata.metadata_dynamic_search import BaseDynamicSearch


class MetaDataViewSubData(Model):
    layouts = ListType(PolyModelType(BaseLayoutField))


class MetaDataViewTable(Model):
    layout = PolyModelType(BaseLayoutField)


class MetaDataView(Model):
    table = PolyModelType(MetaDataViewTable, serialize_when_none=False)
    sub_data = PolyModelType(MetaDataViewSubData, serialize_when_none=False)
    search = ListType(PolyModelType(BaseDynamicSearch), serialize_when_none=False)


class BaseMetaData(Model):
    view = ModelType(MetaDataView)


class ServerMetadata(BaseMetaData):
    @classmethod
    def set(cls):
        sub_data = MetaDataViewSubData()
        return cls({'view': MetaDataView({'sub_data': sub_data})})

    @classmethod
    def set_layouts(cls, layouts=[]):
        sub_data = MetaDataViewSubData({'layouts': layouts})
        return cls({'view': MetaDataView({'sub_data': sub_data})})
