from modelos import Persona, Empleado
from generadores import (
    generar_tipo_tramite,
    generar_tiempo_consulta,
    generar_tiempo_prestamo,
    generar_tiempo_devolucion,
    generar_decision_post_prestamo,
    generar_tiempo_lectura,
)
from parametros import PARAMETROS_DEFAULT


class SimuladorBiblioteca:
    def __init__(self, parametros=None):
        if parametros is None:
            parametros = PARAMETROS_DEFAULT.copy()

        self.parametros = parametros

        self.tiempo_maximo = parametros["tiempo_maximo"]
        self.hora_actual = 0
        self.fila = 0

        self.empleado_1 = Empleado(id_empleado=1)
        self.empleado_2 = Empleado(id_empleado=2)

        self.cola = []

        self.personas = []
        self.contador_personas = 0

        self.proxima_llegada = 0
        self.fin_atencion_emp_1 = None
        self.fin_atencion_emp_2 = None

        self.fines_lectura = []

        self.vector_estado = []

        self.personas_dentro = 0
        self.capacidad_maxima = parametros["capacidad_maxima"]

        self.acum_permanencia = 0.0
        self.cant_personas_retiradas = 0

    def obtener_estado_biblioteca(self):
        if self.personas_dentro >= self.capacidad_maxima:
            return "Cerrada"
        return "Abierta"

    def obtener_estado_empleado(self, empleado):
        if empleado.esta_libre():
            return "Libre"

        if empleado.tipo_atencion == "prestamo":
            return "At. prestamo"

        if empleado.tipo_atencion == "devolucion":
            return "At. devolucion"

        if empleado.tipo_atencion == "consulta":
            return "At. consulta"

        return "Ocupado"

    def obtener_hora_inicio_persona(self, persona):
        if persona is None:
            return "-"

        if persona.estado == "esperando":
            return round(persona.hora_llegada, 2)

        if persona.estado == "siendo_atendida":
            if persona.hora_inicio_atencion is not None:
                return round(persona.hora_inicio_atencion, 2)
            return "-"

        if persona.estado == "leyendo":
            if persona.hora_inicio_lectura is not None:
                return round(persona.hora_inicio_lectura, 2)
            return "-"

        if persona.estado == "esperando_devolucion":
            if persona.hora_fin_lectura is not None:
                return round(persona.hora_fin_lectura, 2)
            return "-"

        return "-"

    def buscar_empleado_libre(self):
        if self.empleado_1.esta_libre():
            return self.empleado_1

        if self.empleado_2.esta_libre():
            return self.empleado_2

        return None

    def generar_tiempo_atencion(self, tipo_tramite):
        if tipo_tramite == "prestamo":
            rnd, tiempo = generar_tiempo_prestamo(self.parametros)
        elif tipo_tramite == "devolucion":
            rnd, tiempo = generar_tiempo_devolucion(self.parametros)
        else:
            rnd, tiempo = generar_tiempo_consulta(self.parametros)

        return rnd, tiempo

    def asignar_fin_atencion(self, empleado, hora_fin):
        if empleado.id_empleado == 1:
            self.fin_atencion_emp_1 = hora_fin
        else:
            self.fin_atencion_emp_2 = hora_fin

    def limpiar_fin_atencion(self, empleado):
        if empleado.id_empleado == 1:
            self.fin_atencion_emp_1 = None
        else:
            self.fin_atencion_emp_2 = None

    def iniciar_atencion(self, persona, empleado):
        rnd_tiempo, tiempo_atencion = self.generar_tiempo_atencion(persona.tipo_tramite)

        empleado.comenzar_atencion(
            persona=persona,
            tipo_atencion=persona.tipo_tramite,
            hora_actual=self.hora_actual
        )

        hora_fin = self.hora_actual + tiempo_atencion
        self.asignar_fin_atencion(empleado, hora_fin)

        return rnd_tiempo, tiempo_atencion, hora_fin

    def obtener_proximo_fin_lectura(self):
        if len(self.fines_lectura) == 0:
            return None

        return min(self.fines_lectura, key=lambda evento: evento["hora"])

    def obtener_proximo_evento(self):
        eventos = []

        if self.proxima_llegada is not None:
            eventos.append(("llegada_persona", self.proxima_llegada))

        if self.fin_atencion_emp_1 is not None:
            eventos.append(("fin_atencion_emp_1", self.fin_atencion_emp_1))

        if self.fin_atencion_emp_2 is not None:
            eventos.append(("fin_atencion_emp_2", self.fin_atencion_emp_2))

        proximo_fin_lectura = self.obtener_proximo_fin_lectura()
        if proximo_fin_lectura is not None:
            eventos.append(("fin_lectura", proximo_fin_lectura["hora"]))

        return min(eventos, key=lambda evento: evento[1])

    def registrar_salida_persona(self, persona):
        persona.estado = "retirada"
        persona.hora_salida = self.hora_actual

        self.personas_dentro -= 1

        permanencia = persona.calcular_permanencia()
        if permanencia is not None:
            self.acum_permanencia += permanencia
            self.cant_personas_retiradas += 1

    def obtener_personas_activas(self):
        return [
            persona for persona in self.personas
            if persona.estado != "retirada"
        ]

    def registrar_fila(
        self,
        evento,
        rnd_tipo=None,
        tipo_tramite=None,
        rnd_tiempo=None,
        tiempo_atencion=None,
        rnd_decision=None,
        decision_post_prestamo=None,
        rnd_lectura=None,
        tiempo_lectura=None,
    ):
        if evento == "Inicialización":
            numero_fila = 0
        else:
            self.fila += 1
            numero_fila = self.fila

        proximo_fin_lectura = self.obtener_proximo_fin_lectura()
        hora_proximo_fin_lectura = proximo_fin_lectura["hora"] if proximo_fin_lectura else None

        promedio_permanencia = 0
        if self.cant_personas_retiradas > 0:
            promedio_permanencia = self.acum_permanencia / self.cant_personas_retiradas

        fila_estado = {
            "fila": numero_fila,
            "evento": evento,
            "reloj": round(self.hora_actual, 2),

            # Eventos - Llegada_persona
            "rnd_tipo_tramite": round(rnd_tipo, 4) if rnd_tipo is not None else "-",
            "tipo_tramite": tipo_tramite if tipo_tramite is not None else "-",
            "tiempo_entre_llegadas": (
                self.parametros["tiempo_entre_llegadas"]
                if evento in ["Inicialización", "llegada_persona", "llegada_rechazada_biblioteca_cerrada"]
                else "-"
            ),
            "proxima_llegada": round(self.proxima_llegada, 2) if self.proxima_llegada is not None else "-",

            # Eventos - Fin lectura
            "rnd_post_prestamo": round(rnd_decision, 4) if rnd_decision is not None else "-",
            "post_prestamo": decision_post_prestamo if decision_post_prestamo is not None else "-",
            "rnd_tiempo_lectura": round(rnd_lectura, 4) if rnd_lectura is not None else "-",
            "tiempo_lectura": round(tiempo_lectura, 2) if tiempo_lectura is not None else "-",
            "proximo_fin_lectura": (
                round(hora_proximo_fin_lectura, 2)
                if hora_proximo_fin_lectura is not None
                else "-"
            ),

            # Eventos - Fin_atencion(i)
            "rnd_atencion": round(rnd_tiempo, 4) if rnd_tiempo is not None else "-",
            "tiempo_atencion": round(tiempo_atencion, 2) if tiempo_atencion is not None else "-",
            "fin_atencion(1)": round(self.fin_atencion_emp_1, 2) if self.fin_atencion_emp_1 is not None else "-",
            "fin_atencion(2)": round(self.fin_atencion_emp_2, 2) if self.fin_atencion_emp_2 is not None else "-",

            # Objetos permanentes - Empleado(N)
            "empleado(1)_estado": self.obtener_estado_empleado(self.empleado_1),
            "empleado(2)_estado": self.obtener_estado_empleado(self.empleado_2),
            "cola": len(self.cola),

            # Biblioteca
            "cantidad_personas": self.personas_dentro,
            "estado_biblioteca": self.obtener_estado_biblioteca(),

            # Variables estadísticas
            "personas_retiradas": self.cant_personas_retiradas,
            "promedio_permanencia": round(promedio_permanencia, 2),
            "ac_ocio_empleado_1": round(self.empleado_1.tiempo_ocioso_acumulado, 2),
            "ac_ocio_empleado_2": round(self.empleado_2.tiempo_ocioso_acumulado, 2),
        }

        personas_activas = self.obtener_personas_activas()

        for indice in range(1, self.capacidad_maxima + 1):
            persona = personas_activas[indice - 1] if indice <= len(personas_activas) else None

            fila_estado[f"persona({indice})_estado"] = (
                persona.estado if persona is not None else "-"
            )
            fila_estado[f"persona({indice})_hora_inicio"] = (
                self.obtener_hora_inicio_persona(persona)
            )

        self.vector_estado.append(fila_estado)

    def procesar_llegada(self):
        rnd_tipo = None
        tipo_tramite = None
        rnd_tiempo = None
        tiempo_atencion = None

        if self.personas_dentro >= self.capacidad_maxima:
            self.proxima_llegada = (
                self.hora_actual + self.parametros["tiempo_entre_llegadas"]
            )

            self.registrar_fila(
                evento="llegada_rechazada_biblioteca_cerrada",
                rnd_tipo=rnd_tipo,
                tipo_tramite=tipo_tramite,
                rnd_tiempo=rnd_tiempo,
                tiempo_atencion=tiempo_atencion
            )
            return

        self.contador_personas += 1
        self.personas_dentro += 1

        rnd_tipo, tipo_tramite = generar_tipo_tramite(self.parametros)

        persona = Persona(
            id_persona=self.contador_personas,
            tipo_tramite=tipo_tramite,
            hora_llegada=self.hora_actual
        )

        self.personas.append(persona)

        empleado_libre = self.buscar_empleado_libre()

        if empleado_libre is not None:
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(persona, empleado_libre)
        else:
            self.cola.append(persona)

        self.proxima_llegada = (
            self.hora_actual + self.parametros["tiempo_entre_llegadas"]
        )

        self.registrar_fila(
            evento="llegada_persona",
            rnd_tipo=rnd_tipo,
            tipo_tramite=tipo_tramite,
            rnd_tiempo=rnd_tiempo,
            tiempo_atencion=tiempo_atencion
        )

    def procesar_fin_atencion(self, empleado):
        persona = empleado.finalizar_atencion(self.hora_actual)
        self.limpiar_fin_atencion(empleado)

        rnd_decision = None
        decision = None
        rnd_lectura = None
        tiempo_lectura = None

        nombre_evento = f"Fin atencion({empleado.id_empleado})"

        if persona is not None:
            tipo_finalizado = persona.tipo_tramite

            if tipo_finalizado == "prestamo":
                nombre_evento = f"Fin atencion({empleado.id_empleado}) - prestamo"

                rnd_decision, decision = generar_decision_post_prestamo(self.parametros)

                if decision == "se_retira":
                    self.registrar_salida_persona(persona)
                else:
                    persona.estado = "leyendo"
                    persona.hora_inicio_lectura = self.hora_actual

                    rnd_lectura, tiempo_lectura = generar_tiempo_lectura(self.parametros)
                    persona.hora_fin_lectura = self.hora_actual + tiempo_lectura

                    self.fines_lectura.append({
                        "hora": persona.hora_fin_lectura,
                        "persona": persona
                    })

            elif tipo_finalizado == "devolucion":
                nombre_evento = f"Fin atencion({empleado.id_empleado}) - devolucion"
                self.registrar_salida_persona(persona)

            elif tipo_finalizado == "consulta":
                nombre_evento = f"Fin atencion({empleado.id_empleado}) - consulta"
                self.registrar_salida_persona(persona)

        rnd_tiempo = None
        tiempo_atencion = None

        if len(self.cola) > 0:
            siguiente_persona = self.cola.pop(0)
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(siguiente_persona, empleado)

        self.registrar_fila(
            evento=nombre_evento,
            rnd_tiempo=rnd_tiempo,
            tiempo_atencion=tiempo_atencion,
            rnd_decision=rnd_decision,
            decision_post_prestamo=decision,
            rnd_lectura=rnd_lectura,
            tiempo_lectura=tiempo_lectura,
        )

    def procesar_fin_lectura(self):
        evento_lectura = self.obtener_proximo_fin_lectura()
        self.fines_lectura.remove(evento_lectura)

        persona = evento_lectura["persona"]
        persona.estado = "esperando_devolucion"
        persona.tipo_tramite = "devolucion"

        empleado_libre = self.buscar_empleado_libre()

        rnd_tiempo = None
        tiempo_atencion = None

        if empleado_libre is not None:
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(persona, empleado_libre)
        else:
            self.cola.append(persona)

        self.registrar_fila(
            evento="Fin lectura",
            rnd_tiempo=rnd_tiempo,
            tiempo_atencion=tiempo_atencion
        )

    def cerrar_simulacion(self):
        self.hora_actual = self.tiempo_maximo

        self.empleado_1.cerrar_ocio_final(self.tiempo_maximo)
        self.empleado_2.cerrar_ocio_final(self.tiempo_maximo)

        self.registrar_fila(evento="Fin simulacion")

    def simular(self):
        iteraciones = 0
        max_iteraciones = self.parametros["max_iteraciones"]

        self.registrar_fila(evento="Inicialización")

        while self.hora_actual <= self.tiempo_maximo and iteraciones < max_iteraciones:
            evento, hora_evento = self.obtener_proximo_evento()

            if hora_evento > self.tiempo_maximo:
                break

            self.hora_actual = hora_evento

            if evento == "llegada_persona":
                self.procesar_llegada()

            elif evento == "fin_atencion_emp_1":
                self.procesar_fin_atencion(self.empleado_1)

            elif evento == "fin_atencion_emp_2":
                self.procesar_fin_atencion(self.empleado_2)

            elif evento == "fin_lectura":
                self.procesar_fin_lectura()

            iteraciones += 1

        self.cerrar_simulacion()

        return self.vector_estado