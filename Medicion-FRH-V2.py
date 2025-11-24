from Instrumental.AFG1022 import TektronixAFG1022
from Instrumental.KL2110 import Keithley2110
import matplotlib.pyplot as plt
import Funciones_Archivos
import Funciones_Medicion
import numpy as np

N = 1
muestras_por_trigger = 2000

#estado_actual = "INICIO"
estado_actual = "INICIO"
Paso_de_medicion = "GENERADOR"
ARCHIVO_SALIDA_GEN = "mediciones_generador.txt"
ARCHIVO_SALIDA_CAP = "mediciones_capacitor.txt"
Sweep_Time = 0.02
#Sweep_Time = 0.000104

while True:
    
    if estado_actual == "INICIO":
        Funciones_Archivos.limpiar_pantalla()
        opcion = Funciones_Archivos.Mostrar_Menu()
        estado_actual = "INGRESO_VALORES"
    
    elif estado_actual == "INGRESO_VALORES":
        Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time, Cantidad_Ciclos = Funciones_Archivos.Configuracion()
        
        print(Vn_Cx, Vn_Rp, Vn_Tau, Frec, Sweep_time, Cantidad_Ciclos)
        input("Presione Enter para continuar...")
        estado_actual = "INICIALIZAR"
        
    elif estado_actual == "INICIALIZAR":
        
        afg = TektronixAFG1022("USB0::0x0699::0x0353::2234106::INSTR")
        dmm = Keithley2110("USB0::0x05E6::0x2110::8018964::INSTR")
        print(afg.idn())
        print(dmm.idn())
        
        #Reset de instrumentos
        afg.reset()
        dmm.reset()

        # Configuraciones iniciales
        afg.modo_independiente()
        
        #Canal 1: señal cuadrada 
        afg.configurar_senal_medida(1)
        
        #Canal 2: trigger TTL
        afg.configurar_trigger_ttl(1)
        
        #Sincróniza los canales para que empiecen juntos
        afg.sincronizar_canales()
        
        # Configuraciones del multímetro
        # Configurar rango fijo de 1 V   
        dmm.configurar_dc_range(rango=10)
        dmm.configurar_fast_mode()
        dmm.configurar_trigger_externo(muestras=muestras_por_trigger)
        
        estado_actual = "MEDIR"
        
    elif estado_actual == "MEDIR": 
        #Activa las salidas
        afg.iniciar_salidas()
        
        if Paso_de_medicion == "GENERADOR":
            print("Medición del canal 1, tensión en el generador cargado\n")                         
            print("Midiendo...")

            medicion_gen = dmm.medir_por_trigger()
            Funciones_Archivos.Graficar_Mediciones(medicion_gen)  
        
        elif Paso_de_medicion == "CAPACITOR":
            print("Medición del canal 1, tensión en el capacitor\n")                         
            print("Midiendo...")
            medicion_cap = dmm.medir_por_trigger()
            Funciones_Archivos.Graficar_Mediciones(medicion_cap)
        
        estado_actual = "GUARDAR"       

    elif estado_actual == "GUARDAR":
        
        # Guardar archivo
        if Paso_de_medicion == "GENERADOR":  
            Funciones_Archivos.Guardar_Medicion(ARCHIVO_SALIDA_GEN,medicion_gen)
            print(f"Archivo guardado como: {ARCHIVO_SALIDA_GEN}")
            Paso_de_medicion = "CAPACITOR"
            estado_actual = "MEDIR"

        elif Paso_de_medicion == "CAPACITOR":
            Funciones_Archivos.Guardar_Medicion(ARCHIVO_SALIDA_CAP,medicion_cap)
            print(f"Archivo guardado como: {ARCHIVO_SALIDA_CAP}")
            Paso_de_medicion = "GENERADOR"
            estado_actual = "ANALIZAR"
    

        
    elif estado_actual == "ANALIZAR":
        Funciones_Archivos.limpiar_pantalla()
        V_max, V_max_std = Funciones_Medicion.Analizar_senal_Generador(medicion_gen)
        print(f"Tensión máxima del generador cargado: {V_max:.6f} V ± {V_max_std:.6f} V\n")

        Cx_vector,slope_vector,intercept_vector,r_value_vector,std_err_vector,Cantidad_ciclos_validos,Cantidad_de_muestras,V_dig = Funciones_Medicion.Procesamiento_Curva(
                                                                                                                                    medicion_cap,                                                                                                                                                 
                                                                                                                                    V_max,
                                                                                                                                    Sweep_Time,
                                                                                                                                    Vn_Rp
                                                                                                                                    )
        Cx         = np.mean(Cx_vector)
        ucx, ucxp  = Funciones_Medicion.Calculo_Incertidumbre(slope_vector,Cantidad_ciclos_validos,V_dig,V_max,Vn_Cx,Vn_Rp)
        
        Funciones_Medicion.Mostrar_Resultado(Cx,ucx, ucxp, Vn_Rp)
        
        input("Presionar Enter para continuar") 
        Funciones_Archivos.limpiar_pantalla()
        estado_actual = "FINALIZACION"
    
    elif estado_actual == "FINALIZACION":
        estado_actual = Funciones_Archivos.Menu_Final()
        dmm.close()
        afg.close()
    
    else:
        Funciones_Archivos.limpiar_pantalla()
        break    
       
