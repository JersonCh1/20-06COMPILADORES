#!/usr/bin/env python3
"""
Compilador Completo - Versión Simplificada
==========================================
Wrapper simplificado que ejecuta sintactico.py con diferentes archivos
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

def modificar_archivo_objetivo(nombre_archivo):
    """Modifica el archivo objetivo en lexico.py"""
    lexico_path = Path('compilador/lexico.py')
    
    if not lexico_path.exists():
        return False
    
    # Leer archivo
    with open(lexico_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar y reemplazar la línea del archivo
    lineas = contenido.split('\n')
    for i, linea in enumerate(lineas):
        if linea.strip().startswith("archivo = "):
            lineas[i] = f"archivo = '{nombre_archivo}'"
            break
    
    # Escribir archivo modificado
    with open(lexico_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas))
    
    return True

def compilar_archivo(nombre_archivo=None, mostrar_salida=True):
    """Compila un archivo específico"""
    
    if nombre_archivo:
        print(f"[INFO] Compilando archivo: {nombre_archivo}")
        if not modificar_archivo_objetivo(nombre_archivo):
            print("[ERROR] No se pudo modificar el archivo objetivo")
            return False
    
    try:
        # Ejecutar sintactico.py directamente
        inicio = time.time()
        
        if mostrar_salida:
            # Mostrar salida en tiempo real
            proceso = subprocess.run([
                sys.executable, 'compilador/sintactico.py'
            ], cwd='.')
            resultado = proceso.returncode == 0
        else:
            # Capturar salida
            proceso = subprocess.run([
                sys.executable, 'compilador/sintactico.py'
            ], capture_output=True, text=True, cwd='.')
            resultado = proceso.returncode == 0
            
            # Analizar resultado
            if "COMPILACION COMPLETA EXITOSA:" in proceso.stdout:
                print("[EXITO] Compilacion completa exitosa")
            elif "Error sintactico" in proceso.stdout:
                print("[ERROR] Errores sintacticos encontrados")
            elif "Errores semanticos" in proceso.stdout:
                print("[ERROR] Errores semanticos encontrados")
            elif "Errores de tipos" in proceso.stdout:
                print("[ERROR] Errores de tipos encontrados")
            else:
                print("[ERROR] Compilacion fallida")
        
        tiempo = time.time() - inicio
        print(f"[INFO] Tiempo de compilacion: {tiempo:.3f}s")
        
        return resultado
        
    except Exception as e:
        print(f"[ERROR] Error ejecutando compilador: {e}")
        return False

def compilar_todos_ejemplos():
    """Compila todos los archivos de ejemplo"""
    directorio_ejemplos = Path("codigos-bocetos")
    
    if not directorio_ejemplos.exists():
        print("[ERROR] Directorio 'codigos-bocetos' no encontrado")
        return
    
    archivos = list(directorio_ejemplos.glob("*.txt"))
    if not archivos:
        print("[ERROR] No se encontraron archivos .txt")
        return
    
    print(f"[INFO] Compilando {len(archivos)} archivos...")
    print("=" * 60)
    
    exitosos = []
    fallidos = []
    
    for i, archivo in enumerate(archivos, 1):
        nombre = archivo.name
        print(f"\n[{i}/{len(archivos)}] {nombre}")
        
        resultado = compilar_archivo(nombre, mostrar_salida=False)
        
        if resultado:
            exitosos.append(nombre)
            print(f"   [EXITO] {nombre}")
        else:
            fallidos.append(nombre)
            print(f"   [FALLO] {nombre}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE COMPILACION MASIVA")
    print("=" * 60)
    print(f"Total de archivos: {len(archivos)}")
    print(f"Exitosos: {len(exitosos)}")
    print(f"Fallidos: {len(fallidos)}")
    print(f"Tasa de exito: {len(exitosos)/len(archivos)*100:.1f}%")
    
    if exitosos:
        print(f"\nArchivos compilados exitosamente:")
        for archivo in exitosos:
            print(f"   - {archivo}")
    
    if fallidos:
        print(f"\nArchivos con errores:")
        for archivo in fallidos:
            print(f"   - {archivo}")

def crear_makefile():
    """Crea un Makefile simple para compilar assembly"""
    makefile_content = """# Makefile para compilar codigo assembly generado

CC = gcc
CFLAGS = -no-pie -g
ASM_DIR = salida-assembly
BIN_DIR = ejecutables

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

compile: $(BIN_DIR)
	$(CC) $(CFLAGS) -o $(BIN_DIR)/$(basename $(FILE)) $(ASM_DIR)/$(FILE)
	@echo "Compilado: $(BIN_DIR)/$(basename $(FILE))"

run: compile
	@echo "Ejecutando $(basename $(FILE))..."
	./$(BIN_DIR)/$(basename $(FILE))

clean:
	rm -rf $(BIN_DIR)
	@echo "Archivos ejecutables eliminados"

help:
	@echo "Comandos disponibles:"
	@echo "  make compile FILE=archivo.s  - Compilar archivo especifico"
	@echo "  make run FILE=archivo.s      - Compilar y ejecutar archivo"
	@echo "  make clean                   - Limpiar ejecutables"

.PHONY: compile run clean help
"""
    
    with open('Makefile', 'w', encoding='utf-8') as f:
        f.write(makefile_content)
    
    print("[INFO] Makefile creado exitosamente")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Compilador completo simplificado",
        epilog="""
Ejemplos de uso:
  python compilador_completo.py                       # Compilar archivo actual
  python compilador_completo.py --file tipos-validos.txt  # Archivo especifico
  python compilador_completo.py --compile-all         # Todos los archivos
  python compilador_completo.py --makefile            # Crear Makefile
        """
    )
    
    parser.add_argument('--file', '-f', help='Archivo especifico a compilar')
    parser.add_argument('--compile-all', action='store_true', help='Compilar todos los archivos')
    parser.add_argument('--makefile', action='store_true', help='Crear Makefile')
    parser.add_argument('--quiet', '-q', action='store_true', help='Modo silencioso')
    
    args = parser.parse_args()
    
    if args.makefile:
        crear_makefile()
        return
    
    if args.compile_all:
        compilar_todos_ejemplos()
        return
    
    print("COMPILADOR COMPLETO v1.0")
    print("=" * 40)
    
    try:
        resultado = compilar_archivo(args.file, not args.quiet)
        sys.exit(0 if resultado else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Compilacion interrumpida")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()