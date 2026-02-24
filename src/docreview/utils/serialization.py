from __future__ import annotations

import json

from pydantic import BaseModel


def dump_model_json(model: BaseModel) -> str:
    return json.dumps(
        model.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
    )
