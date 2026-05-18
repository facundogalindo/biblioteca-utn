from dataclasses import dataclass
from typing import Optional


@dataclass
class Persona:
    id_persona: int
    tipo_tramite: str
    hora_llegada: float

    estado: str = "esperando"

    hora_inicio_atencion: Optional[float] = None
    hora_fin_atencion: Optional[float] = None

    hora_inicio_lectura: Optional[float] = None
    hora_fin_lectura: Optional[float] = None

    hora_salida: Optional[float] = None

    def calcular_permanencia(self) -> Optional[float]:
        if self.hora_salida is None:
            return None

        return self.hora_salida - self.hora_llegada
    
@dataclass
class Empleado:
    id_empleado: int

    estado: str = "libre"
    persona_actual: Optional[Persona] = None
    tipo_atencion: Optional[str] = None
    hora_inicio_ocupacion: Optional[float] = None

    tiempo_ocioso_acumulado: float = 0.0
    ultima_hora_libre: float = 0.0

    def esta_libre(self) -> bool:
        return self.estado == "libre"

    def comenzar_atencion(self, persona: Persona, tipo_atencion: str, hora_actual: float):
        self.estado = "ocupado"
        self.persona_actual = persona
        self.tipo_atencion = tipo_atencion
        self.hora_inicio_ocupacion = hora_actual

        persona.estado = "siendo_atendida"
        persona.hora_inicio_atencion = hora_actual

        self.tiempo_ocioso_acumulado += hora_actual - self.ultima_hora_libre

    def finalizar_atencion(self, hora_actual: float) -> Optional[Persona]:
        persona = self.persona_actual

        if persona is not None:
            persona.hora_fin_atencion = hora_actual

        self.estado = "libre"
        self.persona_actual = None
        self.tipo_atencion = None
        self.hora_inicio_ocupacion = None
        self.ultima_hora_libre = hora_actual

        return persona