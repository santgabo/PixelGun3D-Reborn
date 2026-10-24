"""Comprobaciones de archivos de muestra; no dependen de Unity ni Blender."""

from array import array
import io
import math
import sys
import wave


def inspect_obj(text):
    vertices, uv, normals, faces = [], [], [], []
    materials, libraries = [], []
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        tag, values = parts[0], parts[1:]
        if tag in {"v", "vt", "vn"}:
            expected = 2 if tag == "vt" else 3
            vector = tuple(map(float, values))
            if len(vector) != expected or not all(math.isfinite(v) for v in vector):
                raise ValueError(f"Coordenadas OBJ inválidas: {line}")
            {"v": vertices, "vt": uv, "vn": normals}[tag].append(vector)
        elif tag == "f":
            if len(values) != 3:
                raise ValueError("La muestra debe contener triángulos")
            faces.append([tuple(map(int, value.split("/"))) for value in values])
        elif tag == "usemtl":
            materials.append(" ".join(values))
        elif tag == "mtllib":
            libraries.append(" ".join(values))
    if not vertices or not faces:
        raise ValueError("OBJ sin geometría")
    for face in faces:
        for indices in face:
            if len(indices) != 3 or any(not 1 <= index <= count for index, count in
                                       zip(indices, (len(vertices), len(uv), len(normals)))):
                raise ValueError("Índice OBJ fuera de rango o sin UV/normal")
    return {"vertices": vertices, "uv": uv, "normals": normals, "faces": faces,
            "materials": materials, "libraries": libraries}


def inspect_wav(data):
    with wave.open(io.BytesIO(data), "rb") as audio:
        channels, width, rate, frames = (audio.getnchannels(), audio.getsampwidth(),
                                         audio.getframerate(), audio.getnframes())
        pcm = audio.readframes(frames)
        if audio.getcomptype() != "NONE" or width != 2:
            raise ValueError("Esta prueba espera WAV PCM de 16 bits")
    if not frames or len(pcm) != frames * channels * width:
        raise ValueError("WAV vacío o truncado")
    values = array("h", pcm)
    if sys.byteorder != "little":
        values.byteswap()
    peak = max(abs(value) for value in values)
    if peak == 0:
        raise ValueError("La muestra WAV está en silencio completo")
    return {"channels": channels, "sample_width_bytes": width, "sample_rate": rate,
            "frames": frames, "duration_seconds": frames / rate,
            "peak_normalized": peak / 32768,
            "rms_normalized": math.sqrt(sum(v * v for v in values) / len(values)) / 32768,
            "clipped_sample_fraction": sum(v in (-32768, 32767) for v in values) / len(values)}
