import json
from django.forms.models import model_to_dict


def serialize_queryset(queryset):
    data = [model_to_dict(obj) for obj in queryset]
    return json.dumps(data)


def deserialize_list(json_str):
    if not json_str:
        return []

    return json.loads(json_str)
