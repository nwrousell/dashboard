from abc import ABC, abstractmethod
import importlib
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


from database import Database
from sources.registry import source_registry


class Source(ABC):
    id: str
    schema: List[str]

    @abstractmethod
    def fetch(cls, last_queried: Optional[datetime]) -> List[Dict]:
        pass

    @classmethod
    def register(cls):
        # print(f"Registering: {cls.__name__}")
        source_registry.append(cls)


def load_all_sources():
    sources_dir = os.path.join(os.path.dirname(__file__), "sources")
    for fname in os.listdir(sources_dir):
        if fname.endswith(".py") and fname != "__init__.py":
            module_name = "sources." + fname[:-3]
            importlib.import_module(module_name)


def fetch_all():
    load_all_sources()

    with open("./sources/last_queried.json", "rt") as f:
        last_queried = json.load(f)

    with Database() as db:
        for source in source_registry:
            source_last_fetched = (
                datetime.fromisoformat(last_queried[source.id])
                if source.id in last_queried
                else None
            )
            if source_last_fetched is None:
                db.create_table(
                    source.id,
                    source.schema,
                )
            rows = source.fetch(last_queried=source_last_fetched)
            col_names = [s.split(" ")[0] for s in source.schema]
            db.insert(source.id, columns=col_names, rows=rows)

            print(f"[SOURCES] inserted {len(rows)} into {source.id} table")

            last_queried[source.id] = datetime.now().isoformat()

    with open("./sources/last_queried.json", "wt") as f:
        json.dump(last_queried, f)


if __name__ == "__main__":
    fetch_all()
