import random
import math


def generar_tipo_tramite(parametros):
    """
    Determina qué trámite viene a hacer la persona.

    Probabilidades parametrizables:
    - préstamo
    - devolución
    - consulta
    """
    rnd = random.random()

    prob_prestamo = parametros["prob_prestamo"]
    prob_devolucion = parametros["prob_devolucion"]

    if rnd < prob_prestamo:
        return rnd, "prestamo"

    if rnd < prob_prestamo + prob_devolucion:
        return rnd, "devolucion"

    return rnd, "consulta"


def generar_tiempo_consulta(parametros):
    """
    Tiempo de consulta: U(a, b)
    Fórmula: a + RND * (b - a)
    """
    rnd = random.random()

    minimo = parametros["consulta_min"]
    maximo = parametros["consulta_max"]

    tiempo = minimo + rnd * (maximo - minimo)

    return rnd, tiempo


def generar_tiempo_prestamo(parametros):
    """
    Tiempo de préstamo: exponencial negativa.
    Fórmula: -media * ln(1 - RND)
    """
    rnd = random.random()

    media = parametros["media_prestamo"]
    tiempo = -media * math.log(1 - rnd)

    return rnd, tiempo


def generar_tiempo_devolucion(parametros):
    """
    Tiempo de devolución: U(a, b)
    Fórmula: a + RND * (b - a)
    """
    rnd = random.random()

    minimo = parametros["devolucion_min"]
    maximo = parametros["devolucion_max"]

    tiempo = minimo + rnd * (maximo - minimo)

    return rnd, tiempo


def generar_decision_post_prestamo(parametros):
    """
    Luego del préstamo:
    - se retira
    - lee en sala
    """
    rnd = random.random()

    prob_se_retira = parametros["prob_se_retira"]

    if rnd < prob_se_retira:
        return rnd, "se_retira"

    return rnd, "lee_en_sala"


def generar_tiempo_lectura(parametros):
    """
    Tiempo de lectura: exponencial negativa.
    Fórmula: -media * ln(1 - RND)
    """
    rnd = random.random()

    media = parametros["media_lectura"]
    tiempo = -media * math.log(1 - rnd)

    return rnd, tiempo