#!/usr/bin/env python3
"""
Utilidades del Compilador
========================
Script con herramientas adicionales para desarrollo y testing del compilador.

Funciones incluidas:
- Compilación masiva de ejemplos
- Comparación de outputs
- Generación de reportes
- Limpieza de archivos temporales
- Validación de gramática
- Testing automatizado
"""

import os
import sys
import shutil
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

def limpiar_directorios():
    """Limpia todos los directorios de salida"""
    directorios = [
        'salida-tokens',
        'salida-arboles', 
        'salida-assembly',
        'ejecutables',
        '__pycache__'
    ]
    
    archivos_temp = [
        'Makefile'
    ]
    
    print("🧹 Limpiando directorios temporales...")
    
    for directorio in directorios:
        if os.path.exists(directorio):
            shutil.rmtree(directorio)
            print(f"   ✓ Eliminado: {directorio}/")
    
    for archivo in archivos_temp:
        if os.path.exists(archivo):
            os.remove(archivo)
            print(f"   ✓ Eliminado: {archivo}")
    
    print("✅ Limpieza completada")

def compilar_todos_ejemplos():
    """Compila todos los archivos de ejemplo y genera reporte"""
    directorio_ejemplos = Path("codigos-bocetos")
    
    if not directorio_ejemplos.exists():
        print("❌ Directorio 'codigos-bocetos' no encontrado")
        return None
    
    archivos = list(directorio_ejemplos.glob("*.txt"))
    if not archivos:
        print("❌ No se encontraron archivos .txt")
        return None
    
    resultados = {
        'timestamp': datetime.now().isoformat(),
        'total_archivos': len(archivos),
        'exitosos': [],
        'fallidos': [],
        'errores': [],
        'estadisticas': {}
    }
    
    print(f"🔄 Compilando {len(archivos)} archivos...")
    print("=" * 60)
    
    for i, archivo in enumerate(archivos, 1):
        nombre = archivo.name
        print(f"\n[{i}/{len(archivos)}] 📁 {nombre}")
        
        try:
            # Modificar archivo objetivo en lexico.py
            modificar_archivo_objetivo(nombre)
            
            # Ejecutar compilador
            inicio = time.time()
            resultado = subprocess.run([
                sys.executable, 'compilador/sintactico.py', '--quiet'
            ], capture_output=True, text=True, cwd='.')
            tiempo = time.time() - inicio
            
            info = {
                'archivo': nombre,
                'tiempo_compilacion': round(tiempo, 3),
                'codigo_salida': resultado.returncode,
                'stdout': resultado.stdout,
                'stderr': resultado.stderr
            }
            
            if resultado.returncode == 0:
                resultados['exitosos'].append(info)
                print(f"   ✅ ÉXITO ({tiempo:.3f}s)")
            else:
                resultados['fallidos'].append(info)
                print(f"   ❌ FALLO - código {resultado.returncode}")
                if resultado.stderr:
                    print(f"      Error: {resultado.stderr.strip()}")
                    
        except Exception as e:
            error_info = {
                'archivo': nombre,
                'error': str(e),
                'tipo': type(e).__name__
            }
            resultados['errores'].append(error_info)
            print(f"   💥 ERROR: {e}")
    
    # Calcular estadísticas
    resultados['estadisticas'] = {
        'tasa_exito': len(resultados['exitosos']) / len(archivos) * 100,
        'tiempo_total': sum(r['tiempo_compilacion'] for r in resultados['exitosos'] + resultados['fallidos']),
        'tiempo_promedio': sum(r['tiempo_compilacion'] for r in resultados['exitosos'] + resultados['fallidos']) / len(archivos) if archivos else 0
    }
    
    # Guardar reporte
    guardar_reporte(resultados)
    mostrar_resumen(resultados)
    
    return resultados

def modificar_archivo_objetivo(nombre_archivo):
    """Modifica temporalmente el archivo objetivo en lexico.py"""
    lexico_path = Path('compilador/lexico.py')
    
    if not lexico_path.exists():
        return
    
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

def guardar_reporte(resultados):
    """Guarda un reporte detallado en JSON"""
    os.makedirs('reportes', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_reporte = f'reportes/reporte_compilacion_{timestamp}.json'
    
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado: {archivo_reporte}")

def mostrar_resumen(resultados):
    """Muestra un resumen de los resultados"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE COMPILACIÓN MASIVA")
    print("=" * 60)
    
    stats = resultados['estadisticas']
    print(f"📁 Total de archivos: {resultados['total_archivos']}")
    print(f"✅ Exitosos: {len(resultados['exitosos'])}")
    print(f"❌ Fallidos: {len(resultados['fallidos'])}")
    print(f"💥 Errores: {len(resultados['errores'])}")
    print(f"🎯 Tasa de éxito: {stats['tasa_exito']:.1f}%")
    print(f"⏱️  Tiempo total: {stats['tiempo_total']:.3f}s")
    print(f"⏱️  Tiempo promedio: {stats['tiempo_promedio']:.3f}s")
    
    if resultados['exitosos']:
        print(f"\n🎉 Archivos compilados exitosamente:")
        for resultado in resultados['exitosos']:
            print(f"   • {resultado['archivo']} ({resultado['tiempo_compilacion']}s)")
    
    if resultados['fallidos']:
        print(f"\n⚠️  Archivos con errores de compilación:")
        for resultado in resultados['fallidos']:
            print(f"   • {resultado['archivo']} (código {resultado['codigo_salida']})")
    
    if resultados['errores']:
        print(f"\n💥 Archivos con errores críticos:")
        for error in resultados['errores']:
            print(f"   • {error['archivo']}: {error['error']}")

def verificar_estructura_proyecto():
    """Verifica que la estructura del proyecto sea correcta"""
    print("🔍 Verificando estructura del proyecto...")
    
    estructura_esperada = {
        'directorios': [
            'compilador',
            'codigos-bocetos',
            'gramatica',
            'tabla-ll1',
            'generador-de-tablas-ll1'
        ],
        'archivos_importantes': [
            'compilador/lexico.py',
            'compilador/sintactico.py',
            'gramatica/gramatica.txt',
            'tabla-ll1/tabla_ll1.csv',
            'requirements.txt'
        ]
    }
    
    problemas = []
    
    # Verificar directorios
    for directorio in estructura_esperada['directorios']:
        if not os.path.exists(directorio):
            problemas.append(f"❌ Directorio faltante: {directorio}")
        else:
            print(f"   ✓ {directorio}/")
    
    # Verificar archivos
    for archivo in estructura_esperada['archivos_importantes']:
        if not os.path.exists(archivo):
            problemas.append(f"❌ Archivo faltante: {archivo}")
        else:
            print(f"   ✓ {archivo}")
    
    if problemas:
        print("\n⚠️  Problemas encontrados:")
        for problema in problemas:
            print(f"   {problema}")
        return False
    else:
        print("\n✅ Estructura del proyecto correcta")
        return True

def ejecutar_tests():
    """Ejecuta una suite básica de tests"""
    print("🧪 Ejecutando tests básicos...")
    
    tests = [
        {
            'nombre': 'Test de importación de módulos',
            'funcion': test_importacion_modulos
        },
        {
            'nombre': 'Test de análisis léxico',
            'funcion': test_analisis_lexico
        },
        {
            'nombre': 'Test de tabla LL(1)',
            'funcion': test_tabla_ll1
        },
        {
            'nombre': 'Test de compilación simple',
            'funcion': test_compilacion_simple
        }
    ]
    
    resultados = []
    
    for test in tests:
        print(f"\n🔹 {test['nombre']}")
        try:
            exito = test['funcion']()
            if exito:
                print(f"   ✅ PASÓ")
                resultados.append(True)
            else:
                print(f"   ❌ FALLÓ")
                resultados.append(False)
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            resultados.append(False)
    
    # Resumen
    pasaron = sum(resultados)
    total = len(resultados)
    print(f"\n📊 Resumen de tests: {pasaron}/{total} pasaron ({pasaron/total*100:.1f}%)")
    
    return all(resultados)

def test_importacion_modulos():
    """Test para verificar que todos los módulos se importan correctamente"""
    try:
        import compilador.lexico
        import compilador.sintactico
        return True
    except ImportError:
        return False

def test_analisis_lexico():
    """Test básico del análisis léxico"""
    try:
        from compilador.lexico import analizar_lexico, es_identificador_valido, es_numero_entero
        
        # Test de funciones básicas
        assert es_identificador_valido('variable1') == True
        assert es_identificador_valido('123abc') == False
        assert es_numero_entero('123') == True
        assert es_numero_entero('12.3') == False
        
        return True
    except:
        return False

def test_tabla_ll1():
    """Test para verificar que la tabla LL(1) existe y es válida"""
    try:
        tabla_path = Path('tabla-ll1/tabla_ll1.csv')
        if not tabla_path.exists():
            return False
        
        import pandas as pd
        df = pd.read_csv(tabla_path, index_col=0)
        
        # Verificar que tiene contenido
        return len(df) > 0 and len(df.columns) > 0
    except:
        return False

def test_compilacion_simple():
    """Test de compilación de un programa simple"""
    try:
        # Crear archivo de prueba temporal
        codigo_test = '''fn main() int {
    return 0;
}'''
        
        test_file = Path('test_temp.txt')
        with open(test_file, 'w') as f:
            f.write(codigo_test)
        
        # Mover a directorio de bocetos
        dest_path = Path('codigos-bocetos/test_temp.txt')
        shutil.move(test_file, dest_path)
        
        # Modificar archivo objetivo
        modificar_archivo_objetivo('test_temp.txt')
        
        # Ejecutar compilador
        resultado = subprocess.run([
            sys.executable, 'compilador/sintactico.py', '--no-assembly', '--quiet'
        ], capture_output=True)
        
        # Limpiar
        if dest_path.exists():
            dest_path.unlink()
        
        return resultado.returncode == 0
        
    except Exception as e:
        print(f"Error en test: {e}")
        return False

def generar_documentacion():
    """Genera documentación automática del proyecto"""
    print("📚 Generando documentación...")
    
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    
    # Generar lista de archivos de ejemplo
    ejemplos_path = docs_dir / 'ejemplos.md'
    with open(ejemplos_path, 'w', encoding='utf-8') as f:
        f.write("# Ejemplos de Código\n\n")
        
        bocetos_dir = Path('codigos-bocetos')
        if bocetos_dir.exists():
            for archivo in sorted(bocetos_dir.glob('*.txt')):
                f.write(f"## {archivo.name}\n\n")
                f.write("```c\n")
                f.write(archivo.read_text(encoding='utf-8'))
                f.write("\n```\n\n")
    
    print(f"   ✓ Generado: {ejemplos_path}")
    
    # Generar índice de archivos de salida
    if os.path.exists('salida-tokens'):
        tokens_path = docs_dir / 'tokens_generados.md'
        with open(tokens_path, 'w', encoding='utf-8') as f:
            f.write("# Tokens Generados\n\n")
            
            for archivo in sorted(Path('salida-tokens').glob('*.txt')):
                f.write(f"## {archivo.name}\n\n")
                f.write("```\n")
                f.write(archivo.read_text(encoding='utf-8')[:1000])  # Primeros 1000 chars
                f.write("\n```\n\n")
        
        print(f"   ✓ Generado: {tokens_path}")
    
    print("✅ Documentación generada en docs/")

def main():
    """Función principal del script de utilidades"""
    parser = argparse.ArgumentParser(
        description="Utilidades del compilador",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponibles:
  --clean              Limpiar directorios temporales
  --compile-all        Compilar todos los ejemplos
  --test              Ejecutar suite de tests
  --verify            Verificar estructura del proyecto
  --docs              Generar documentación
  --report            Mostrar último reporte
        """
    )
    
    parser.add_argument('--clean', action='store_true', help='Limpiar archivos temporales')
    parser.add_argument('--compile-all', action='store_true', help='Compilar todos los ejemplos')
    parser.add_argument('--test', action='store_true', help='Ejecutar tests')
    parser.add_argument('--verify', action='store_true', help='Verificar estructura')
    parser.add_argument('--docs', action='store_true', help='Generar documentación')
    parser.add_argument('--report', action='store_true', help='Mostrar último reporte')
    parser.add_argument('--all', action='store_true', help='Ejecutar todas las utilidades')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🛠️  UTILIDADES DEL COMPILADOR")
    print("=" * 40)
    
    if args.all:
        args.verify = True
        args.test = True
        args.compile_all = True
        args.docs = True
    
    if args.clean:
        limpiar_directorios()
    
    if args.verify:
        if not verificar_estructura_proyecto():
            print("⚠️  Estructura incorrecta, algunos comandos pueden fallar")
    
    if args.test:
        if not ejecutar_tests():
            print("⚠️  Algunos tests fallaron")
    
    if args.compile_all:
        compilar_todos_ejemplos()
    
    if args.docs:
        generar_documentacion()
    
    if args.report:
        mostrar_ultimo_reporte()
    
    print("\n✅ Utilidades completadas")

def mostrar_ultimo_reporte():
    """Muestra el último reporte generado"""
    reportes_dir = Path('reportes')
    
    if not reportes_dir.exists():
        print("❌ No hay reportes disponibles")
        return
    
    reportes = list(reportes_dir.glob('reporte_compilacion_*.json'))
    
    if not reportes:
        print("❌ No se encontraron reportes")
        return
    
    ultimo_reporte = max(reportes, key=lambda x: x.stat().st_mtime)
    
    print(f"📄 Último reporte: {ultimo_reporte.name}")
    
    with open(ultimo_reporte, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    mostrar_resumen(datos)

if __name__ == "__main__":
    main()