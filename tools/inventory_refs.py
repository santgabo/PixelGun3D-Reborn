"""Resolución local y auditable de rutas y referencias; nunca carga dependencias."""

from collections import defaultdict
import posixpath


class FileIndex:
    def __init__(self, files):
        self.by_id = {row["id"]: row for row in files}
        self.suffixes = defaultdict(list)
        for row in files:
            parts = row["logical_path"].replace("\\", "/").split("/")
            for index in range(len(parts)):
                self.suffixes["/".join(parts[index:]).casefold()].append(row["id"])

    def resolve(self, owner_id, reference):
        path = posixpath.normpath(reference.replace("\\", "/")).casefold()
        if path in ("", "."):
            return None, "missing", []
        owner = self.by_id[owner_id]
        sibling = posixpath.normpath(posixpath.join(
            posixpath.dirname(owner["logical_path"]), path)).casefold()
        candidates = self.suffixes.get(sibling, [])
        local = [key for key in candidates if self.by_id[key]["archive"] == owner["archive"]]
        if len(local) == 1:
            return local[0], "owner_relative", local
        candidates = self.suffixes.get(path, [])
        method = "path_suffix"
        if not candidates:
            candidates = self.suffixes.get(posixpath.basename(path), [])
            method = "basename"
        if len(candidates) == 1:
            return candidates[0], method, candidates
        return None, "ambiguous" if candidates else "missing", candidates


def pointers(value, field=""):
    """Recorre solo campos seleccionados del diccionario parseado, sin deref()."""
    if isinstance(value, dict):
        if "m_FileID" in value and "m_PathID" in value:
            yield field, value["m_FileID"], value["m_PathID"]
        else:
            for key, child in value.items():
                yield from pointers(child, f"{field}.{key}" if field else str(key))
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            yield from pointers(child, f"{field}[{index}]")


def stream_descriptors(data):
    """Texture/Mesh StreamingInfo y AudioClip StreamedResource (sin decodificar)."""
    stream = data.get("m_StreamData")
    if stream:
        path = stream.get("path", "")
        size = stream.get("size", 0)
        if path or size:
            yield "m_StreamData", path, stream.get("offset", 0), size
    resource = data.get("m_Resource")
    if resource:
        path = resource.get("m_Source", "")
        size = resource.get("m_Size", 0)
        if path or size:
            yield "m_Resource", path, resource.get("m_Offset", 0), size
