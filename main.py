from typing import Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Evaluador de cadenas AFD y AFN")


# ---------- Modelos de entrada ----------
class AFDRequest(BaseModel):
    alfabeto: List[str]
    estado_inicial: str
    estados_finales: List[str]
    tabla_transicion: Dict[str, Dict[str, str]]
    cadenas: List[str]


class AFNRequest(BaseModel):
    alfabeto: List[str]
    estado_inicial: str
    estados_finales: List[str]
    tabla_transicion: Dict[str, Dict[str, List[str]]]
    cadenas: List[str]


# ---------- Utilidades ----------
def fmt(restante: str) -> str:
    return restante if restante else "ε"

def estados_afd(tabla):
    estados = set(tabla.keys())
    for trans in tabla.values():
        estados.update(trans.values())
    return sorted(estados)


def estados_afn(tabla):
    estados = set(tabla.keys())
    for trans in tabla.values():
        for destinos in trans.values():
            estados.update(destinos)
    return sorted(estados)


# ---------- AFD ----------
@app.post("/afd/evaluar")
def evaluar_afd(req: AFDRequest):
    estados = estados_afd(req.tabla_transicion)
    if req.estado_inicial not in estados:
        raise HTTPException(400, "El estado inicial no está en la tabla")
    if not set(req.estados_finales) <= set(estados):
        raise HTTPException(400, "Hay estados finales que no están en la tabla")

    resultados = []
    for cadena in req.cadenas:
        q = req.estado_inicial
        pasos = [f"({q}, {fmt(cadena)})"]
        valida = True
        for i, simbolo in enumerate(cadena):
            if simbolo not in req.alfabeto:
                valida = False
                pasos.append(f"símbolo '{simbolo}' no pertenece al alfabeto")
                break
            q = req.tabla_transicion.get(q, {}).get(simbolo)
            if q is None:
                valida = False
                pasos.append("transición no definida")
                break
            pasos.append(f"({q}, {fmt(cadena[i + 1:])})")
        aceptada = valida and q in req.estados_finales
        resultados.append({
            "cadena": cadena,
            "resultado": "ACEPTADA" if aceptada else "RECHAZADA",
            "notacion_transicion": " ⊢ ".join(pasos),
        })

    return {
        "tipo": "AFD",
        "estados_totales": estados,
        "alfabeto": req.alfabeto,
        "estado_inicial": req.estado_inicial,
        "estados_finales": req.estados_finales,
        "resultados": resultados,
    }


# ---------- AFN ----------
@app.post("/afn/evaluar")
def evaluar_afn(req: AFNRequest):
    estados = estados_afn(req.tabla_transicion)
    if req.estado_inicial not in estados:
        raise HTTPException(400, "El estado inicial no está en la tabla")
    if not set(req.estados_finales) <= set(estados):
        raise HTTPException(400, "Hay estados finales que no están en la tabla")

    def conjunto(s):
        return "{" + ", ".join(sorted(s)) + "}"

    resultados = []
    for cadena in req.cadenas:
        actuales = {req.estado_inicial}
        pasos = [f"({conjunto(actuales)}, {fmt(cadena)})"]
        valida = True
        for i, simbolo in enumerate(cadena):
            if simbolo not in req.alfabeto:
                valida = False
                pasos.append(f"símbolo '{simbolo}' no pertenece al alfabeto")
                break
            siguientes = set()
            for q in actuales:
                siguientes.update(req.tabla_transicion.get(q, {}).get(simbolo, []))
            actuales = siguientes
            pasos.append(f"({conjunto(actuales)}, {fmt(cadena[i + 1:])})")
        aceptada = valida and bool(actuales & set(req.estados_finales))
        resultados.append({
            "cadena": cadena,
            "resultado": "ACEPTADA" if aceptada else "RECHAZADA",
            "notacion_transicion": " ⊢ ".join(pasos),
        })

    return {
        "tipo": "AFN",
        "estados_totales": estados,
        "alfabeto": req.alfabeto,
        "estado_inicial": req.estado_inicial,
        "estados_finales": req.estados_finales,
        "resultados": resultados,
    }
