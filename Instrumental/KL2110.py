import pyvisa
import time

# Variables del Keithley 2110 (DCV, 10 V Range)
# --------------------------------------------------------------------------------
# Nota: El DMM2110 es un medidor de 6.5 dígitos, no tiene las mismas especificaciones
# de "Jitter" o "Sampling Gain Error" tan detalladas como el HP3458A.
# Usamos las especificaciones estándar de precisión.

# Precisión de la medida DCV (Componente de la lectura / Error de Ganancia)
# 0.0035% de la lectura = 35 ppm
Keithley2110_Accuracy_V  = 35e-6   

# Offset de la medida DCV (Componente del rango / Error de Desplazamiento)
# 0.0005% del rango = 5 ppm del rango (para rango de 10V)
Keithley2110_Offset_V    = 5e-6    

# Error de Ganancia de Muestreo (No aplica o está incluido en Accuracy)
# Si necesitas un valor separado para un modelo de cálculo similar al HP3458A,
# se suele tomar la parte de la lectura. Usamos el valor de Accuracy.
Keithley2110_Gain_error_V = 35e-6   

# Resolución Digital
# 6 1/2 dígitos: 1 en el millón. (e.g., 10 uV en rango de 10V, 1 uV en rango de 1V)
# Usamos 1 ppm del rango como resolución mínima:
Keithley2110_Resolution_V = 1e-6    # 1 / 1000000

class Keithley2110:
    """
    Controlador para el multímetro Keithley 2110.
    Incluye métodos específicos para medición sincronizada por trigger externo.
    """

    def __init__(self, resource_name=None):
        self.rm = pyvisa.ResourceManager()
        if resource_name is None:
            print("Instrumentos detectados:")
            for res in self.rm.list_resources():
                print(f" - {res}")
            raise ValueError("Debe especificar el resource_name del Keithley 2110.")
        self.inst = self.rm.open_resource(resource_name)
        self.inst.timeout = 5000
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'

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
    # CONFIGURACIONES DE MEDICIÓN
    # ===================================================

    def configurar_dc_range(self, rango=1):
        """Configura el rango DC y valida valores permitidos."""
        rangos_validos = [0.1, 1, 10, 100, 1000]

        if rango not in rangos_validos:
            raise ValueError(f"Rango no válido. Rangos permitidos: {rangos_validos}")

        self.inst.write("VOLT:DC:RANG:AUTO OFF")
        self.inst.write(f"VOLT:DC:RANG {rango}")
        
    # ===================================================
    # MÉTODOS DE ADQUISICIÓN POR TRIGGER EXTERNO
    # ===================================================
    def configurar_trigger_externo(self, muestras=1):
        """
        Trigger externo + flanco ascendente + número de muestras por trigger.
        """
        self.inst.write("ABOR")               # <- Limpia estados previos
        self.inst.write("TRIG:SOUR EXT")      # Trigger externo
        self.inst.write("TRIG:SLOP POS")      # Flanco ascendente
        self.inst.write("TRIG:DEL 0")         # Sin delay
        self.inst.write(f"SAMP:COUN {muestras}")  # Cantidad de muestras por trigger
        self.inst.write("TRIG:COUN 1")        # <- IMPORTANTE: un solo trigger externo
        self.inst.write("ABOR")               # <- Re-inicializa

    def medir_por_trigger(self):
        self.inst.write("ABOR")       # Limpia buffers previos
        self.inst.write("INIT")       # Espera el trigger
        datos = self.inst.query("FETCh?")
        return [float(x) for x in datos.split(',') if x]

    def medir_n_triggers(self, n):
        """
        Mide N veces, esperando un trigger en cada una.
        """
        valores = []
        for _ in range(n):
            valores.append(self.medir_por_trigger())
        return valores
    # ===================================================
    # VELOCIDADES DE ADQUISICIÓN
    # ===================================================    
    
    def configurar_fast_mode(self):
        """Modo rápido: máxima velocidad de muestreo (~50 lect/s)."""
        self.inst.write("VOLT:DC:NPLC 0.02")

    def configurar_normal_mode(self):
        """Modo estándar."""
        self.inst.write("VOLT:DC:NPLC 1")

    def configurar_precise_mode(self):
        """Modo muy preciso pero lento."""
        self.inst.write("VOLT:DC:NPLC 10")
        
        
"""
# Ejemplo de uso:
multimetro = Keithley2110("USB0::0x05E6::0x2110::8018964::INSTR")
print(multimetro.idn())
multimetro.reset()
multimetro.configurar_autorango(True)
print(multimetro.medir_tension_dc())
multimetro.close()


multimetro = Keithley2110("USB0::0x05E6::0x2110::8018964::INSTR")
print(multimetro.idn())
multimetro.reset()
multimetro.configurar_autorango(True)
# --- Configurar para sincronizar con TRIGGER EXTERNO ---
multimetro.configurar_trigger_externo(muestras=3, delay=0)
print("Esperando trigger externo...")
lecturas = multimetro.esperar_trigger_y_medicion()
print("Lecturas recibidas:", lecturas)
multimetro.close()
"""