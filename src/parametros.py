PARAMETROS_DEFAULT = {
    # Simulación
    "tiempo_maximo": 180,
    "hora_desde": 0,
    "cantidad_iteraciones_mostrar": 50,
    "max_iteraciones": 100000,

    # Llegadas
    "tiempo_entre_llegadas": 4,

    # Probabilidades de trámite
    "prob_prestamo": 0.45,
    "prob_devolucion": 0.45,
    "prob_consulta": 0.10,

    # Consulta U(2, 5)
    "consulta_min": 2,
    "consulta_max": 5,

    # Préstamo Exp. negativa media 6
    "media_prestamo": 6,

    # Devolución 2 ± 0,5 => U(1.5, 2.5)
    "devolucion_min": 1.5,
    "devolucion_max": 2.5,

    # Decisión luego del préstamo
    "prob_se_retira": 0.60,
    "prob_lee_en_sala": 0.40,

    # Lectura Exp. negativa media 30
    "media_lectura": 30,

    # Capacidad
    "capacidad_maxima": 20,
}