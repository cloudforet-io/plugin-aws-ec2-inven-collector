from schematics import Model
from schematics.types import ListType, ModelType, PolyModelType
from spaceone.inventory.model.metadata.metadata_dynamic_layout import BaseLayoutField, QuerySearchTableDynamicLayout
from spaceone.inventory.model.metadata.metadata_dynamic_search import BaseDynamicSearch, BaseDynamicSearchItem
from spaceone.inventory.model.metadata.metadata_dynamic_widget import BaseDynamicWidget


class MetaDataViewTable(Model):
    layout = PolyModelType(BaseLayoutField)


class MetaDataViewSubData(Model):
    layouts = ListType(PolyModelType(BaseLayoutField))


class MetaDataView(Model):
    table = PolyModelType(MetaDataViewTable, serialize_when_none=False)
    sub_data = PolyModelType(MetaDataViewSubData, serialize_when_none=False)
    search = ListType(PolyModelType(BaseDynamicSearchItem), serialize_when_none=False)
    widget = ListType(PolyModelType(BaseDynamicWidget), serialize_when_none=False)


class ServerMetadata(Model):
    view = ModelType(MetaDataView)

    @classmethod
    def set_layouts(cls, layouts=[]):
        sub_data = MetaDataViewSubData({'layouts': layouts})
        return cls({'view': MetaDataView({'sub_data': sub_data})})


class CloudServiceTypeMetadata(Model):
    view = ModelType(MetaDataView)

    @classmethod
    def set_fields(cls, name='', fields=[]):
        _table = MetaDataViewTable({'layout': QuerySearchTableDynamicLayout.set_fields(name, fields)})
        return cls({'view': MetaDataView({'table': _table})})

    @classmethod
    def set_meta(cls, name='', fields=[], search=[], widget=[]):
        table_meta = MetaDataViewTable({'layout': QuerySearchTableDynamicLayout.set_fields(name, fields)})

        if search and isinstance(search[0], dict):
            search_meta = [BaseDynamicSearchItem(_search) for _search in search]
        else:
            search_meta = [BaseDynamicSearchItem({'items': search})]

        return cls({'view': MetaDataView({'table': table_meta, 'search': search_meta, 'widget': widget})})