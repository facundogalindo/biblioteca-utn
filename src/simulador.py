from modelos import (
    Persona,
    Empleado,
    ESTADO_PERSONA_ESPERANDO,
    ESTADO_PERSONA_LEYENDO,
    ESTADO_PERSONA_DESTRUIDA,
)
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

        # En inicialización se programa la primera llegada.
        self.proxima_llegada = parametros["tiempo_entre_llegadas"]

        self.fin_atencion_emp_1 = None
        self.fin_atencion_emp_2 = None

        self.fines_lectura = []

        self.vector_estado = []

        self.personas_dentro = 0
        self.capacidad_maxima = parametros["capacidad_maxima"]

        # ==========================
        # Variables estadísticas
        # ==========================
        # Misma lógica que Excel:
        # acum_tiempo_permanencia(x) =
        # acum_tiempo_permanencia(x-1)
        # + (reloj(x) - reloj(x-1)) * cantidad_personas(x-1)
        self.acum_tiempo_permanencia = 0.0
        self.cant_personas_promedio = 0
        self.ultimo_reloj_estadisticas = 0.0

    def obtener_estado_biblioteca(self):
        if self.personas_dentro >= self.capacidad_maxima:
            return "Cerrada"
        return "Abierta"

    def obtener_estado_empleado(self, empleado):
        return empleado.estado

    def obtener_hora_inicio_persona(self, persona):
        if persona is None:
            return "-"

        return round(persona.hora_llegada, 2)

    def obtener_fin_lectura_persona(self, persona):
        if persona is None:
            return "-"

        if persona.estado == ESTADO_PERSONA_LEYENDO and persona.hora_fin_lectura is not None:
            return round(persona.hora_fin_lectura, 2)

        return "-"

    def obtener_personas_activas(self):
        return [
            persona for persona in self.personas
            if persona.estado != ESTADO_PERSONA_DESTRUIDA
        ]

    def obtener_personas_por_id(self):
        return {
            persona.id_persona: persona
            for persona in self.personas
        }

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
        rnd_tiempo, tiempo_atencion = self.generar_tiempo_atencion(
            persona.tramite_actual
        )

        empleado.comenzar_atencion(
            persona=persona,
            tipo_atencion=persona.tramite_actual,
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

    def actualizar_tiempo_permanencia_hasta(self, nuevo_reloj):
        """
        Aplica exactamente la lógica del Excel:

        tiempo_transcurrido(x) =
        tiempo_transcurrido(x-1)
        + (reloj(x) - reloj(x-1)) * cantidad_personas(x-1)

        Se llama ANTES de procesar el evento actual.
        Así, cantidad_personas usada es la de la fila anterior.
        """
        diferencia_reloj = nuevo_reloj - self.ultimo_reloj_estadisticas

        if diferencia_reloj > 0:
            self.acum_tiempo_permanencia += diferencia_reloj * self.personas_dentro
            self.ultimo_reloj_estadisticas = nuevo_reloj

    def destruir_persona(self, persona):
        """
        Cuando la persona sale del sistema, el objeto temporal se destruye.
        En el vector no se muestra como Retirada; sus columnas quedan con "-".

        Importante:
        NO se suma acá la permanencia al acumulador, porque ahora la permanencia
        ya se acumula por intervalos con la fórmula del Excel.
        """
        persona.estado = ESTADO_PERSONA_DESTRUIDA
        persona.hora_salida = self.hora_actual

        self.personas_dentro -= 1

    def obtener_ocio_actual_empleado(self, empleado):
        if empleado.esta_libre():
            return empleado.tiempo_ocioso_acumulado + (
                self.hora_actual - empleado.ultima_hora_libre
            )

        return empleado.tiempo_ocioso_acumulado

    def calcular_metricas_permanencia_actual(self):
        tiempo_transcurrido = self.acum_tiempo_permanencia

        if self.cant_personas_promedio == 0:
            promedio_permanencia = 0
        else:
            promedio_permanencia = (
                tiempo_transcurrido / self.cant_personas_promedio
            )

        return (
            tiempo_transcurrido,
            self.cant_personas_promedio,
            promedio_permanencia
        )

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
        hora_proximo_fin_lectura = (
            proximo_fin_lectura["hora"]
            if proximo_fin_lectura is not None
            else None
        )

        tiempo_transcurrido, cant_personas_promedio, promedio_permanencia = (
            self.calcular_metricas_permanencia_actual()
        )

        fila_estado = {
            "fila": numero_fila,
            "evento": evento,
            "reloj": round(self.hora_actual, 2),

            # Eventos - Llegada_persona
            "rnd_tipo_tramite": round(rnd_tipo, 4) if rnd_tipo is not None else "-",
            "tipo_tramite": tipo_tramite if tipo_tramite is not None else "-",
            "tiempo_entre_llegadas": (
                self.parametros["tiempo_entre_llegadas"]
                if evento == "Inicialización" or evento.startswith("llegada_persona")
                else "-"
            ),
            "proxima_llegada": (
                round(self.proxima_llegada, 2)
                if self.proxima_llegada is not None
                else "-"
            ),

            # Eventos - Fin_atencion(i)
            "rnd_atencion": round(rnd_tiempo, 4) if rnd_tiempo is not None else "-",
            "tiempo_atencion": (
                round(tiempo_atencion, 2)
                if tiempo_atencion is not None
                else "-"
            ),
            "fin_atencion(1)": (
                round(self.fin_atencion_emp_1, 2)
                if self.fin_atencion_emp_1 is not None
                else "-"
            ),
            "fin_atencion(2)": (
                round(self.fin_atencion_emp_2, 2)
                if self.fin_atencion_emp_2 is not None
                else "-"
            ),

            # Eventos - fin_lectura
            "rnd_post_prestamo": (
                round(rnd_decision, 4)
                if rnd_decision is not None
                else "-"
            ),
            "post_prestamo": (
                decision_post_prestamo
                if decision_post_prestamo is not None
                else "-"
            ),
            "rnd_tiempo_lectura": (
                round(rnd_lectura, 4)
                if rnd_lectura is not None
                else "-"
            ),
            "tiempo_lectura": (
                round(tiempo_lectura, 2)
                if tiempo_lectura is not None
                else "-"
            ),
            "proximo_fin_lectura": (
                round(hora_proximo_fin_lectura, 2)
                if hora_proximo_fin_lectura is not None
                else "-"
            ),

            # Objetos permanentes - Empleado(N)
            "empleado(1)_estado": self.obtener_estado_empleado(self.empleado_1),
            "empleado(2)_estado": self.obtener_estado_empleado(self.empleado_2),
            "cola": len(self.cola),

            # Objetos permanentes - Biblioteca
            "cantidad_personas": self.personas_dentro,
            "estado_biblioteca": self.obtener_estado_biblioteca(),

            # Variables estadísticas
            "tiempo_transcurrido": round(tiempo_transcurrido, 2),
            "cant_personas_promedio": cant_personas_promedio,
            "promedio_permanencia": round(promedio_permanencia, 2),
            "ac_ocio_empleado_1": round(
                self.obtener_ocio_actual_empleado(self.empleado_1),
                2
            ),
            "ac_ocio_empleado_2": round(
                self.obtener_ocio_actual_empleado(self.empleado_2),
                2
            ),
        }

        personas_por_id = self.obtener_personas_por_id()

        for indice in range(1, self.contador_personas + 1):
            persona = personas_por_id.get(indice)

            if persona is not None and persona.estado != ESTADO_PERSONA_DESTRUIDA:
                fila_estado[f"cli({indice})_estado"] = persona.estado
                fila_estado[f"cli({indice})_hora_inicio"] = (
                    self.obtener_hora_inicio_persona(persona)
                )
                fila_estado[f"cli({indice})_tramite"] = persona.tramite_actual
                fila_estado[f"cli({indice})_fin_lectura"] = (
                    self.obtener_fin_lectura_persona(persona)
                )
            else:
                fila_estado[f"cli({indice})_estado"] = "-"
                fila_estado[f"cli({indice})_hora_inicio"] = "-"
                fila_estado[f"cli({indice})_tramite"] = "-"
                fila_estado[f"cli({indice})_fin_lectura"] = "-"

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
                evento="llegada_persona no_ingresa",
                rnd_tipo=None,
                tipo_tramite=None,
                rnd_tiempo=None,
                tiempo_atencion=None
            )
            return

        self.contador_personas += 1
        self.cant_personas_promedio += 1
        self.personas_dentro += 1

        rnd_tipo, tipo_tramite = generar_tipo_tramite(self.parametros)

        persona = Persona(
            id_persona=self.contador_personas,
            tramite_actual=tipo_tramite,
            hora_llegada=self.hora_actual
        )

        self.personas.append(persona)

        empleado_libre = self.buscar_empleado_libre()

        if empleado_libre is not None:
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(
                persona,
                empleado_libre
            )
        else:
            persona.estado = ESTADO_PERSONA_ESPERANDO
            self.cola.append(persona)

        self.proxima_llegada = (
            self.hora_actual + self.parametros["tiempo_entre_llegadas"]
        )

        self.registrar_fila(
            evento=f"llegada_persona cli_{persona.id_persona}",
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

        nombre_evento = f"fin_atencion({empleado.id_empleado})"

        if persona is not None:
            tramite_finalizado = persona.tramite_actual
            nombre_evento = (
                f"fin_atencion_{tramite_finalizado}"
                f"({empleado.id_empleado}) cli_{persona.id_persona}"
            )

            if tramite_finalizado == "prestamo":
                rnd_decision, decision = generar_decision_post_prestamo(
                    self.parametros
                )

                if decision == "se_retira":
                    self.destruir_persona(persona)

                else:
                    persona.estado = ESTADO_PERSONA_LEYENDO
                    persona.tramite_actual = "prestamo"
                    persona.hora_inicio_lectura = self.hora_actual

                    rnd_lectura, tiempo_lectura = generar_tiempo_lectura(
                        self.parametros
                    )
                    persona.hora_fin_lectura = self.hora_actual + tiempo_lectura

                    self.fines_lectura.append({
                        "hora": persona.hora_fin_lectura,
                        "persona": persona
                    })

            elif tramite_finalizado == "devolucion":
                self.destruir_persona(persona)

            elif tramite_finalizado == "consulta":
                self.destruir_persona(persona)

        rnd_tiempo = None
        tiempo_atencion = None

        if len(self.cola) > 0:
            siguiente_persona = self.cola.pop(0)
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(
                siguiente_persona,
                empleado
            )

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

        persona.tramite_actual = "devolucion"
        persona.hora_fin_lectura = None

        empleado_libre = self.buscar_empleado_libre()

        rnd_tiempo = None
        tiempo_atencion = None

        if empleado_libre is not None:
            rnd_tiempo, tiempo_atencion, _ = self.iniciar_atencion(
                persona,
                empleado_libre
            )
        else:
            persona.estado = ESTADO_PERSONA_ESPERANDO
            self.cola.append(persona)

        self.registrar_fila(
            evento=f"fin_lectura cli_{persona.id_persona}",
            rnd_tiempo=rnd_tiempo,
            tiempo_atencion=tiempo_atencion
        )

    def normalizar_columnas_objetos_temporales(self):
        for fila in self.vector_estado:
            for indice in range(1, self.contador_personas + 1):
                fila.setdefault(f"cli({indice})_estado", "-")
                fila.setdefault(f"cli({indice})_hora_inicio", "-")
                fila.setdefault(f"cli({indice})_tramite", "-")
                fila.setdefault(f"cli({indice})_fin_lectura", "-")

    def cerrar_simulacion(self, hora_final):
        self.actualizar_tiempo_permanencia_hasta(hora_final)

        self.hora_actual = hora_final

        self.empleado_1.cerrar_ocio_final(hora_final)
        self.empleado_2.cerrar_ocio_final(hora_final)

        self.registrar_fila(evento="Fin simulacion")

    def simular(self):
        iteraciones = 0
        max_iteraciones = self.parametros["max_iteraciones"]

        self.registrar_fila(evento="Inicialización")

        termino_por_iteraciones = False

        while self.hora_actual <= self.tiempo_maximo and iteraciones < max_iteraciones:
            evento, hora_evento = self.obtener_proximo_evento()

            if hora_evento > self.tiempo_maximo:
                break

            # Primero actualizamos estadística usando la cantidad_personas anterior.
            self.actualizar_tiempo_permanencia_hasta(hora_evento)

            # Luego avanzamos el reloj y procesamos el evento.
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

            if iteraciones >= max_iteraciones:
                termino_por_iteraciones = True

        if termino_por_iteraciones:
            hora_final = self.hora_actual
        else:
            hora_final = self.tiempo_maximo

        self.cerrar_simulacion(hora_final)
        self.normalizar_columnas_objetos_temporales()

        return self.vector_estado