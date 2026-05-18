from pathlib import Path
import pandas as pd


def exportar_a_excel(df_mostrado, df_completo, resultados, ruta_salida="output/vector_estado.xlsx"):
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        df_mostrado.to_excel(writer, sheet_name="Vector mostrado", index=False)
        df_completo.to_excel(writer, sheet_name="Vector completo", index=False)

        df_resultados = pd.DataFrame([resultados])
        df_resultados.to_excel(writer, sheet_name="Resultados", index=False)

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    value = cell.value
                    if value is not None:
                        max_length = max(max_length, len(str(value)))

                worksheet.column_dimensions[column_letter].width = min(max_length + 2, 35)

    return ruta