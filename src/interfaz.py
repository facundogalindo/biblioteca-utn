import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from simulador import SimuladorBiblioteca
from parametros import PARAMETROS_DEFAULT


class InterfazBiblioteca:
    def __init__(self, root):
        self.root = root
        self.root.title("TP4 - Simulación Biblioteca UTN")
        self.root.geometry("1400x750")

        self.df_vector = pd.DataFrame()
        self.entries = {}

        self.crear_widgets()

    def crear_widgets(self):
        frame_principal = ttk.Frame(self.root)
        frame_principal.pack(fill="both", expand=True)

        frame_parametros = ttk.LabelFrame(frame_principal, text="Parámetros")
        frame_parametros.pack(fill="x", padx=10, pady=10)

        self.crear_inputs_parametros(frame_parametros)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.pack(fill="x", padx=10, pady=5)

        self.btn_simular = ttk.Button(
            frame_botones,
            text="Ejecutar simulación",
            command=self.ejecutar_simulacion
        )
        self.btn_simular.pack(side="left", padx=5)

        frame_resultados = ttk.LabelFrame(frame_principal, text="Resultados")
        frame_resultados.pack(fill="x", padx=10, pady=5)

        self.lbl_resultados = ttk.Label(
            frame_resultados,
            text="Todavía no se ejecutó ninguna simulación."
        )
        self.lbl_resultados.pack(anchor="w", padx=10, pady=10)

        frame_tabla = ttk.LabelFrame(frame_principal, text="Vector de estado")
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabla = ttk.Treeview(frame_tabla, show="headings")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tabla.xview)

        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabla.rowconfigure(0, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

    def crear_inputs_parametros(self, frame):
        campos = [
            ("tiempo_maximo", "Tiempo máximo X"),
            ("hora_desde", "Hora desde j"),
            ("cantidad_iteraciones_mostrar", "Iteraciones i"),
            ("tiempo_entre_llegadas", "Tiempo entre llegadas"),
            ("prob_prestamo", "Prob. préstamo"),
            ("prob_devolucion", "Prob. devolución"),
            ("prob_consulta", "Prob. consulta"),
            ("consulta_min", "Consulta mín."),
            ("consulta_max", "Consulta máx."),
            ("media_prestamo", "Media préstamo"),
            ("devolucion_min", "Devolución mín."),
            ("devolucion_max", "Devolución máx."),
            ("prob_se_retira", "Prob. se retira"),
            ("prob_lee_en_sala", "Prob. lee en sala"),
            ("media_lectura", "Media lectura"),
            ("capacidad_maxima", "Capacidad máxima"),
            ("max_iteraciones", "Máx. iteraciones"),
        ]

        columnas_por_fila = 4

        for index, (clave, etiqueta) in enumerate(campos):
            fila = index // columnas_por_fila
            columna_base = (index % columnas_por_fila) * 2

            ttk.Label(frame, text=etiqueta).grid(
                row=fila,
                column=columna_base,
                padx=5,
                pady=4,
                sticky="w"
            )

            entry = ttk.Entry(frame, width=12)
            entry.grid(
                row=fila,
                column=columna_base + 1,
                padx=5,
                pady=4,
                sticky="w"
            )

            entry.insert(0, str(PARAMETROS_DEFAULT[clave]))
            self.entries[clave] = entry

    def leer_parametros(self):
        parametros = {}

        for clave, entry in self.entries.items():
            valor = entry.get().strip()

            try:
                if clave in ["cantidad_iteraciones_mostrar", "max_iteraciones", "capacidad_maxima"]:
                    parametros[clave] = int(valor)
                else:
                    parametros[clave] = float(valor)
            except ValueError:
                raise ValueError(f"El parámetro '{clave}' debe ser numérico.")

        self.validar_parametros(parametros)

        return parametros

    def validar_parametros(self, parametros):
        suma_tramites = (
            parametros["prob_prestamo"]
            + parametros["prob_devolucion"]
            + parametros["prob_consulta"]
        )

        if abs(suma_tramites - 1) > 0.0001:
            raise ValueError("Las probabilidades de préstamo, devolución y consulta deben sumar 1.")

        suma_post_prestamo = (
            parametros["prob_se_retira"]
            + parametros["prob_lee_en_sala"]
        )

        if abs(suma_post_prestamo - 1) > 0.0001:
            raise ValueError("Las probabilidades post préstamo deben sumar 1.")

        if parametros["tiempo_maximo"] <= 0:
            raise ValueError("El tiempo máximo debe ser mayor a 0.")

        if parametros["hora_desde"] < 0:
            raise ValueError("La hora desde j no puede ser negativa.")

        if parametros["cantidad_iteraciones_mostrar"] <= 0:
            raise ValueError("La cantidad de iteraciones a mostrar debe ser mayor a 0.")

        if parametros["tiempo_entre_llegadas"] <= 0:
            raise ValueError("El tiempo entre llegadas debe ser mayor a 0.")

        if parametros["capacidad_maxima"] <= 0:
            raise ValueError("La capacidad máxima debe ser mayor a 0.")

        if parametros["max_iteraciones"] <= 0:
            raise ValueError("El máximo de iteraciones debe ser mayor a 0.")

        if parametros["consulta_min"] > parametros["consulta_max"]:
            raise ValueError("Consulta mín. no puede ser mayor que consulta máx.")

        if parametros["devolucion_min"] > parametros["devolucion_max"]:
            raise ValueError("Devolución mín. no puede ser mayor que devolución máx.")

    def ejecutar_simulacion(self):
        try:
            parametros = self.leer_parametros()

            simulador = SimuladorBiblioteca(parametros=parametros)
            vector_estado = simulador.simular()

            df_completo = pd.DataFrame(vector_estado)

            self.df_vector = self.filtrar_vector_estado(df_completo, parametros)

            self.cargar_tabla(self.df_vector)
            self.mostrar_resultados(simulador)

        except ValueError as error:
            messagebox.showerror("Error de parámetros", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", str(error))

    def filtrar_vector_estado(self, df, parametros):
        hora_desde = parametros["hora_desde"]
        cantidad = parametros["cantidad_iteraciones_mostrar"]

        if df.empty:
            return df

        df_filtrado = df[df["reloj"] >= hora_desde].head(cantidad)

        ultima_fila = df.tail(1)

        if not ultima_fila.empty:
            df_filtrado = pd.concat([df_filtrado, ultima_fila]).drop_duplicates()

        return df_filtrado

    def cargar_tabla(self, df):
        self.tabla.delete(*self.tabla.get_children())
        self.tabla["columns"] = list(df.columns)

        anchos_columnas = {
            "fila": 60,
            "evento": 210,
            "reloj": 80,

            "rnd_tipo_tramite": 130,
            "tipo_tramite": 120,
            "tiempo_entre_llegadas": 160,
            "proxima_llegada": 140,

            "rnd_atencion": 120,
            "tiempo_atencion": 140,
            "fin_atencion(1)": 140,
            "fin_atencion(2)": 140,
            "proximo_fin_lectura": 160,

            "empleado(1)_estado": 160,
            "empleado(2)_estado": 160,
            "cola": 80,

            "cantidad_personas": 150,
            "estado_biblioteca": 150,

            "personas_retiradas": 160,
            "promedio_permanencia": 180,
            "ac_ocio_empleado_1": 180,
            "ac_ocio_empleado_2": 180,

            "persona(1)_estado": 160,
            "persona(1)_hora_inicio": 170,
            "persona(2)_estado": 160,
            "persona(2)_hora_inicio": 170,

            "rnd_decision_post_prestamo": 210,
            "decision_post_prestamo": 190,
            "rnd_tiempo_lectura": 170,
            "tiempo_lectura": 140,
        }

        for columna in df.columns:
            self.tabla.heading(columna, text=columna)
            ancho = anchos_columnas.get(columna, 140)
            self.tabla.column(columna, width=ancho, anchor="center", stretch=False)

        for _, fila in df.iterrows():
            valores = [fila[columna] for columna in df.columns]
            self.tabla.insert("", "end", values=valores)

    def mostrar_resultados(self, simulador):
        if simulador.cant_personas_retiradas > 0:
            promedio_permanencia = (
                simulador.acum_permanencia / simulador.cant_personas_retiradas
            )
        else:
            promedio_permanencia = 0

        texto = (
            f"Personas retiradas: {simulador.cant_personas_retiradas} | "
            f"Promedio permanencia: {promedio_permanencia:.2f} min | "
            f"AC ocio empleado 1: {simulador.empleado_1.tiempo_ocioso_acumulado:.2f} min | "
            f"AC ocio empleado 2: {simulador.empleado_2.tiempo_ocioso_acumulado:.2f} min"
        )

        self.lbl_resultados.config(text=texto)