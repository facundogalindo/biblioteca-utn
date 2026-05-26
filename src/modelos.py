from dataclasses import dataclass
from typing import Optional


# ==========================
# Estados visibles de Persona
# ==========================
ESTADO_PERSONA_ESPERANDO = "Esperando"
ESTADO_PERSONA_SIENDO_ATENDIDA = "Siendo_atendida"
ESTADO_PERSONA_LEYENDO = "Leyendo"
ESTADO_PERSONA_DEVOLVIENDO = "Devolviendo"

# Estado interno, NO visible en el vector.
# Se usa solo para saber que el objeto temporal fue destruido.
ESTADO_PERSONA_DESTRUIDA = "Destruida"


# ==========================
# Estados visibles de Empleado
# ==========================
ESTADO_EMPLEADO_LIBRE = "Libre"
ESTADO_EMPLEADO_ATENDIENDO_PRESTAMO = "Atendiendo_prestamo"
ESTADO_EMPLEADO_ATENDIENDO_DEVOLUCION = "Atendiendo_devolucion"
ESTADO_EMPLEADO_ATENDIENDO_CONSULTA = "Atendiendo_consulta"


@dataclass
class Persona:
    id_persona: int
    tramite_actual: str
    hora_llegada: float

    estado: str = ESTADO_PERSONA_ESPERANDO

    hora_inicio_atencion: Optional[float] = None
    hora_fin_atencion: Optional[float] = None

    hora_inicio_lectura: Optional[float] = None
    hora_fin_lectura: Optional[float] = None

    hora_salida: Optional[float] = None

    def calcular_permanencia(self):
        if self.hora_salida is None:
            return None

        return self.hora_salida - self.hora_llegada


@dataclass
class Empleado:
    id_empleado: int

    estado: str = ESTADO_EMPLEADO_LIBRE
    persona_actual: Optional[Persona] = None
    tipo_atencion: Optional[str] = None
    hora_inicio_ocupacion: Optional[float] = None

    tiempo_ocioso_acumulado: float = 0.0
    ultima_hora_libre: float = 0.0

    def esta_libre(self):
        return self.estado == ESTADO_EMPLEADO_LIBRE

    def comenzar_atencion(self, persona, tipo_atencion, hora_actual):
        self.tiempo_ocioso_acumulado += hora_actual - self.ultima_hora_libre

        self.persona_actual = persona
        self.tipo_atencion = tipo_atencion
        self.hora_inicio_ocupacion = hora_actual

        persona.hora_inicio_atencion = hora_actual

        if tipo_atencion == "prestamo":
            self.estado = ESTADO_EMPLEADO_ATENDIENDO_PRESTAMO
            persona.estado = ESTADO_PERSONA_SIENDO_ATENDIDA

        elif tipo_atencion == "devolucion":
            self.estado = ESTADO_EMPLEADO_ATENDIENDO_DEVOLUCION
            persona.estado = ESTADO_PERSONA_DEVOLVIENDO

        elif tipo_atencion == "consulta":
            self.estado = ESTADO_EMPLEADO_ATENDIENDO_CONSULTA
            persona.estado = ESTADO_PERSONA_SIENDO_ATENDIDA

        else:
            self.estado = ESTADO_EMPLEADO_LIBRE
            persona.estado = ESTADO_PERSONA_SIENDO_ATENDIDA

    def finalizar_atencion(self, hora_actual):
        persona = self.persona_actual

        if persona is not None:
            persona.hora_fin_atencion = hora_actual

        self.estado = ESTADO_EMPLEADO_LIBRE
        self.persona_actual = None
        self.tipo_atencion = None
        self.hora_inicio_ocupacion = None
        self.ultima_hora_libre = hora_actual

        return persona

    def cerrar_ocio_final(self, hora_final):
        if self.esta_libre():
            self.tiempo_ocioso_acumulado += hora_final - self.ultima_hora_libre
            self.ultima_hora_libre = hora_final