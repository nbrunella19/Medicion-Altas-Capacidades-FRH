import time
import Funciones_Archivos
import Funciones_Medicion
from Instrumental.AFG1022 import TektronixAFG1022
from Instrumental.KL2110 import Keithley2110
import matplotlib.pyplot as plt

# ==============================
# CONFIGURACIÓN DEL EXPERIMENTO
# ==============================
N_CICLOS = 5          # Número de ciclos a medir
FRECUENCIA = 1        # Frecuencia en Hz
ARCHIVO_SALIDA = "mediciones_multimetro.txt"

# Recursos VISA (cámbialos por los que te aparezcan en tu PC)
generador_RESOURCE = "USB0::0x0699::0x0353::2234106::INSTR"
multimetro_RESOURCE = "USB0::0x05E6::0x2110::8018964::INSTR"    

def main():

    # =========================
    # 1) CONFIGURAR GENERADOR
    # =========================
    generador = TektronixAFG1022(generador_RESOURCE)
    print("generador conectado:", generador.idn())

    generador.reset()
    generador.modo_independiente()

    # Canal 1: cuadrada 1 Hz, amplitud 1 Vpp, offset 0.5 V
    generador.configurar_canal(1, forma="SQU", frecuencia=1, amplitud=1.0, offset=0.5)
    # Canal 2: cuadrada 1 Hz, amplitud 1 Vpp, offset 2.5 V
    generador.configurar_canal(2, forma="SQU", frecuencia=1, amplitud=5.0, offset=2.5)

    # Sincronización (alineación de fase)
    generador.sincronizar_canales()

    # Activar ambas salidas
    generador.activar_salida(1, True)
    generador.activar_salida(2, True)

    print("Generador configurado y salidas activadas.")

    # ==========================
    # 2) CONFIGURAR MULTÍMETRO
    # ==========================
    multimetro = Keithley2110(multimetro_RESOURCE)
    print("Multímetro:", multimetro.idn())
    multimetro.reset()

    # Rango fijo 10 V
    multimetro.configurar_autorango(True)
    #multimetro.inst.write("VOLT:DC:RANG 10")

    # Trigger externo, 1 medición por trigger
    multimetro.configurar_trigger_externo(muestras=1, delay=0)

    print("Esperando mediciones por trigger externo...")
    
    mediciones = []

    for i in range(N_CICLOS):
        print(f"Esperando trigger {i+1}/{N_CICLOS}...")
        valores = multimetro.esperar_trigger_y_medicion()
        medicion = valores[0]
        mediciones.append(medicion)
        print(f"Medición {i+1}: {medicion} V")

    print("Mediciones completadas.")

    with open(ARCHIVO_SALIDA, "w") as f:
        f.write("Medicion(V)\n")
        for v in mediciones:
            f.write(f"{v:.6f}\n")

    # ==========================
    # 3) CERRAR INSTRUMENTOS
    # ==========================
    multimetro.close()
    generador.close()

    print("Instrumentos cerrados correctamente.")


if __name__ == "__main__":
    main()