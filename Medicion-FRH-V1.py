import time
from Instrumental.AFG1022 import TektronixAFG1022
from Instrumental.KL2110 import Keithley2110
import matplotlib.pyplot as plt

# ============================
# CONFIGURACIÓN DEL EXPERIMENTO
# ============================
N_CICLOS = 5
FRECUENCIA = 1            # Hz del pulso de medición
ARCHIVO_SALIDA = "mediciones_multimetro.txt"

# Recursos VISA
generador_RESOURCE = "USB0::0x0699::0x0353::2234106::INSTR"
multimetro_RESOURCE = "USB0::0x05E6::0x2110::8018964::INSTR"


def configurar_generador(afg):
    print("Configurando generador...")

    afg.reset()
    time.sleep(1)
    afg.modo_independiente()

    # =====================
    # CANAL 1: señal medida
    # =====================
    afg.configurar_canal(
        canal=1,
        forma="SQU",
        frecuencia=FRECUENCIA,
        amplitud=1.0,
        offset=0.5
    )

    # =====================
    # CANAL 2: pulso TTL
    # =====================
    # Usar PULSE (mucho mejor para trigger externo)
    afg.inst.write("SOUR2:FUNC PULS")
    afg.inst.write(f"SOUR2:FREQ {FRECUENCIA}")
    afg.inst.write("SOUR2:PULS:WIDT 0.001")    # pulso de 1 ms
    afg.inst.write("SOUR2:PULS:TRAN 1e-6")     # bordes rápidos (1 us)

    # TTL real: 0–5 V
    afg.inst.write("SOUR2:VOLT 5")
    afg.inst.write("SOUR2:VOLT:OFFS 2.5")

    # Asegurar High-Z (si no, la amplitud queda dividida por 2)
    afg.inst.write("OUTP2:LOAD INF")

    # Sincronizar fases
    afg.sincronizar_canales()

    # Activar salidas
    afg.activar_salida(1, True)
    afg.activar_salida(2, True)

    print("Generador listo.\n")
    time.sleep(0.5)


def configurar_multimetro(dmm):
    print("Configurando multímetro...")

    dmm.reset()
    time.sleep(1)

    # Modo voltímetro DC, rango fijo 10 V
    dmm.configurar_autorango(False)
    dmm.inst.write("VOLT:DC:RANG 10")

    # Trigger externo
    dmm.inst.write("TRIG:SOUR EXT")   # trigger externo
    dmm.inst.write("TRIG:SLOP POS")   # flanco ascendente
    dmm.inst.write("TRIG:DEL 0")      # sin delay

    # Una medición por trigger
    dmm.inst.write("SAMP:COUN 1")

    print("Multímetro listo.\n")


def medir_un_ciclo(dmm):
    """
    Espera un trigger externo y devuelve una única medición.
    """
    # INIT prepara el instrumento en modo "waiting for trigger"
    # *WAI bloquea hasta que termine la medición
    dmm.inst.write("INIT; *WAI")

    # FETCh? devuelve la lectura capturada después del trigger
    valor = float(dmm.inst.query("FETCh?"))

    return valor


def main():
    # =========================
    # 1) Conectar instrumentos
    # =========================
    afg = TektronixAFG1022(generador_RESOURCE)
    print("Generador:", afg.idn())

    dmm = Keithley2110(multimetro_RESOURCE)
    print("Multímetro:", dmm.idn())

    # =========================
    # 2) Configurar instrumentos
    # =========================
    configurar_generador(afg)
    configurar_multimetro(dmm)

    print("Esperando triggers externos...\n")

    mediciones = []

    # =========================
    # 3) Ciclo de adquisición
    # =========================
    for i in range(N_CICLOS):
        print(f"→ Esperando trigger {i+1}/{N_CICLOS}...")
        valor = medir_un_ciclo(dmm)
        mediciones.append(valor)
        print(f"   Medición {i+1}: {valor:.6f} V\n")

    print("Mediciones completadas.\n")

    # =========================
    # 4) Guardar archivo
    # =========================
    with open(ARCHIVO_SALIDA, "w") as f:
        f.write("Medicion(V)\n")
        for v in mediciones:
            f.write(f"{v:.6f}\n")

    print(f"Archivo guardado en: {ARCHIVO_SALIDA}")

    # =========================
    # 5) Cerrar instrumentos
    # =========================
    dmm.close()
    afg.close()

    print("Instrumentos cerrados correctamente.")


if __name__ == "__main__":
    main()