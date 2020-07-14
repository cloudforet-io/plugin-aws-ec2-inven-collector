from schematics import Model
from schematics.types import ModelType, PolyModelType, StringType, ListType
from spaceone.inventory.model.metadata_dynamic_field import *


class LayoutOptions(Model):
    class Options:
        serialize_when_none = False

    root_path = StringType(serialize_when_none=False)


class BaseLayoutField(Model):
    @staticmethod
    def _set_fields(fields=[], **kwargs):
        _options = {'fields': fields}
        for k, v in kwargs.items():
            if v is not None:
                _options[k] = v
        return _options

    name = StringType(default='')
    type = StringType(default="item",
                      choices=("item", "table", "query-search-table", "simple-table", "list", "raw", "markdown"))
    options = PolyModelType(LayoutOptions, serialize_when_none=False)


class ItemLayoutOption(LayoutOptions):
    fields = ListType(PolyModelType(BaseDynamicField))


class SimpleTableLayoutOption(LayoutOptions):
    fields = ListType(PolyModelType(BaseDynamicField))


class TableLayoutOption(LayoutOptions):
    fields = ListType(PolyModelType(BaseDynamicField))


class QuerySearchTableLayoutOption(LayoutOptions):
    fields = ListType(PolyModelType(BaseDynamicField))


class RawLayoutOption(LayoutOptions):
    class Options:
        serialize_when_none = False


class ListLayoutOption(LayoutOptions):
    layouts = ListType(PolyModelType(BaseLayoutField))


class MetaDataViewSubData(Model):
    layouts = ListType(PolyModelType(BaseLayoutField))


class MetaDataView(Model):
    sub_data = PolyModelType(MetaDataViewSubData, serialize_when_none=False)


class ServerMetadata(Model):
    view = ModelType(MetaDataView)
