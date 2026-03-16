def build_list_key(model, filters: dict):
    model_name = model.__name__

    # sort for consistency
    parts = [f"{k}={v}" for k, v in sorted(filters.items())]
    filter_str = "&".join(parts) if parts else "all"

    return f"list:{model_name}:{filter_str}"
