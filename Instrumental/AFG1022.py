import pyvisa
import time

class TektronixAFG1022:
    """
    Controlador para el generador de funciones Tektronix AFG1022.
    Incluye métodos extendidos para generar señales de medición y señales TTL de disparo.
    """

    def __init__(self, resource_name=None):
        self.rm = pyvisa.ResourceManager()
        if resource_name is None:
            print("Instrumentos detectados:")
            for res in self.rm.list_resources():
                print(f" - {res}")
            raise ValueError("Debe especificar el resource_name del Tektronix AFG1022.")
        self.inst = self.rm.open_resource(resource_name)
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'
        self.inst.timeout = 5000

    # ===================================================
    # MÉTODOS BÁSICOS
    # ===================================================

    def idn(self):
        return self.inst.query("*IDN?")

    def reset(self):
        self.inst.write("*RST")
        self.inst.write("*CLS")
        time.sleep(0.5)

    def close(self):
        self.inst.close()
        self.rm.close()

    # ===================================================
    # MÉTODOS DE CONFIGURACIÓN DE CANALES
    # ===================================================

    def modo_independiente(self):
        """Desacopla los canales."""
        self.inst.write("SOUR:COUP:FREQ OFF")
        self.inst.write("SOUR:COUP:AMPL OFF")
        self.inst.write("SOUR:COUP:PHAS 0")

    def activar_salida(self, canal=1, estado=True):
        estado_str = "ON" if estado else "OFF"
        self.inst.write(f"OUTP{canal} {estado_str}")

    def sincronizar_canales(self):
        self.inst.write("SOUR:PHAS:ALIGN")

    # ===================================================
    # MÉTODOS ESPECÍFICOS PARA EXPERIMENTO FRH
    # ===================================================

    def configurar_senal_medida(self, frecuencia, amplitud=1.0, offset=0.5):
        """
        Configura el canal 1 como señal cuadrada normal para medir.
        """
        self.inst.write("SOUR1:FUNC SQU")
        self.inst.write(f"SOUR1:FREQ {frecuencia}")
        self.inst.write(f"SOUR1:VOLT {amplitud}")
        self.inst.write(f"SOUR1:VOLT:OFFS {offset}")
        self.inst.write("OUTP1:LOAD INF")  # asegurar amplitud correcta

    def configurar_trigger_ttl(self, frecuencia):
        """
        Configura canal 2 como fuente de trigger TTL (PULSE, 0–5 V, bordes rápidos).
        """
        self.inst.write("SOUR2:FUNC PULS")
        self.inst.write(f"SOUR2:FREQ {frecuencia}")
        self.inst.write("SOUR2:PULS:WIDT 0.001")   # pulso de 1 ms
        self.inst.write("SOUR2:PULS:TRAN 1e-6")     # bordes rápidos
        self.inst.write("SOUR2:VOLT 5")
        self.inst.write("SOUR2:VOLT:OFFS 2.5")
        self.inst.write("OUTP2:LOAD INF")           # 0–5 V reales

    def iniciar_salidas(self):
        """Activa ambos canales luego de la configuración."""
        self.activar_salida(1, True)
        self.activar_salida(2, True)

"""
# Ejemplo de uso:

afg = TektronixAFG1022("USB0::0x0699::0x0353::2234106::INSTR")
print(afg.idn())
afg.reset()
time.sleep(1)   # <- muy importante

afg.configurar_canal(1, forma="SQU", frecuencia=1, amplitud=1.0, offset=0.5)
afg.configurar_canal(2, forma="SQU", frecuencia=1, amplitud=5.0, offset=2.5)
afg.sincronizar_canales()
afg.activar_salida(1, True)
afg.activar_salida(2, True)

# 👉 Lee de vuelta y muestra en pantalla
print("CANAL 1:")
print("  Forma:", afg.leer_forma(1))
print("  Frecuencia:", afg.leer_frecuencia(1))
print("  Amplitud:", afg.leer_amplitud(1))
print("  Offset:", afg.leer_offset(1))
print("  Salida:", afg.leer_salida(1))

print("CANAL 2:")
print("  Forma:", afg.leer_forma(2))
print("  Frecuencia:", afg.leer_frecuencia(2))
print("  Amplitud:", afg.leer_amplitud(2))
print("  Offset:", afg.leer_offset(2))
print("  Salida:", afg.leer_salida(2))

afg.close()
"""