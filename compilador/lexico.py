import os
import re
from tabulate import tabulate

# Configuración del archivo a compilar
archivo = 'verificarvariable.txt'

# Obtener la ruta completa del archivo
directorio_actual = os.path.dirname(__file__)
ruta_archivo = os.path.join(directorio_actual, '..', 'codigos-bocetos', archivo)

# Clase Token
class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return f"Token({self.tipo}, {self.valor}, {self.linea}, {self.columna})"

# Clase Error
class Error:
    def __init__(self, mensaje, linea, columna):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return f"Error en línea {self.linea}, columna {self.columna}: {self.mensaje}"

# Palabras reservadas
palabras_reservadas = {
    'fn': 'funcion',
    'main': 'principal',
    'if': 'condicional',
    'else': 'sino',
    'while': 'buclemientras',
    'for': 'buclepara',
    'do': 'hacer',
    'switch': 'interruptor',
    'case': 'caso',
    'default': 'pordefecto',
    'break': 'romper',
    'continue': 'continuar',
    'return': 'devolver',
    'int': 'tentero',
    'float': 'tflotante',
    'text': 'tcadena',
    'bool': 'tbooleano',
    'void': 'tvacio',
    'true': 'nbooleano',
    'false': 'nbooleano',
    'show': 'mostrar',
    'input': 'entrada',
    'read': 'leer'
}

# Operadores y símbolos
operadores_simbolos = {
    '+': 'suma',
    '-': 'resta',
    '*': 'mul',
    '/': 'div',
    '%': 'residuo',
    '=': 'igual',
    '==': 'igualbool',
    '!=': 'diferentede',
    '<': 'menorque',
    '>': 'mayorque',
    '<=': 'menorigualque',
    '>=': 'mayorigualque',
    '&&': 'y',
    '||': 'o',
    '!': 'no',
    '(': 'pabierto',
    ')': 'pcerrado',
    '{': 'llaveabi',
    '}': 'llavecerr',
    '[': 'corcheteabi',
    ']': 'corchetecer',
    ';': 'fsentencia',
    ',': 'coma',
    ':': 'dospuntos',
    '.': 'punto'
}

# Listas para almacenar tokens y errores
lista_de_tokens = []
lista_errores_lexicos = []

def es_palabra_reservada(palabra):
    """Verifica si una palabra es reservada"""
    return palabra in palabras_reservadas

def es_identificador_valido(cadena):
    """Verifica si una cadena es un identificador válido"""
    patron = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return re.match(patron, cadena) is not None

def es_numero_entero(cadena):
    """Verifica si una cadena es un número entero"""
    patron = r'^[+-]?\d+$'
    return re.match(patron, cadena) is not None

def es_numero_flotante(cadena):
    """Verifica si una cadena es un número flotante"""
    patron = r'^[+-]?\d+\.\d+$'
    return re.match(patron, cadena) is not None

def es_cadena_texto(cadena):
    """Verifica si una cadena es una cadena de texto válida"""
    patron = r'^".*"$'
    return re.match(patron, cadena) is not None

def analizar_lexico(contenido):
    """Función principal del análisis léxico"""
    linea = 1
    columna = 0
    i = 0
    
    while i < len(contenido):
        caracter = contenido[i]
        columna += 1
        
        # Saltar espacios en blanco
        if caracter.isspace():
            if caracter == '\n':
                linea += 1
                columna = 0
            i += 1
            continue
        
        # Comentarios de línea //
        if i < len(contenido) - 1 and contenido[i:i+2] == '//':
            while i < len(contenido) and contenido[i] != '\n':
                i += 1
            continue
        
        # Comentarios de bloque /* */
        if i < len(contenido) - 1 and contenido[i:i+2] == '/*':
            i += 2
            columna += 1
            while i < len(contenido) - 1:
                if contenido[i:i+2] == '*/':
                    i += 2
                    columna += 1
                    break
                if contenido[i] == '\n':
                    linea += 1
                    columna = 0
                else:
                    columna += 1
                i += 1
            continue
        
        # Cadenas de texto
        if caracter == '"':
            inicio_cadena = i
            inicio_columna = columna
            i += 1
            columna += 1
            cadena = '"'
            
            while i < len(contenido) and contenido[i] != '"':
                if contenido[i] == '\n':
                    linea += 1
                    columna = 0
                else:
                    columna += 1
                cadena += contenido[i]
                i += 1
            
            if i < len(contenido):
                cadena += '"'
                valor_cadena = cadena[1:-1]  # Quitar las comillas
                token = Token('ncadena', valor_cadena, linea, inicio_columna)
                lista_de_tokens.append(token)
                i += 1
                columna += 1
            else:
                error = Error("Cadena de texto no cerrada", linea, inicio_columna)
                lista_errores_lexicos.append(error)
                break
            continue
        
        # Operadores de dos caracteres
        if i < len(contenido) - 1:
            doble_caracter = contenido[i:i+2]
            if doble_caracter in operadores_simbolos:
                token = Token(operadores_simbolos[doble_caracter], doble_caracter, linea, columna)
                lista_de_tokens.append(token)
                i += 2
                columna += 1
                continue
        
        # Operadores de un caracter
        if caracter in operadores_simbolos:
            token = Token(operadores_simbolos[caracter], caracter, linea, columna)
            lista_de_tokens.append(token)
            i += 1
            continue
        
        # Números y palabras
        if caracter.isalnum() or caracter == '_':
            inicio_token = i
            inicio_columna = columna
            token_str = ''
            
            # Leer el token completo
            while i < len(contenido) and (contenido[i].isalnum() or contenido[i] == '_' or contenido[i] == '.'):
                token_str += contenido[i]
                i += 1
                if i < len(contenido):
                    columna += 1
            
            # Clasificar el token
            if es_numero_flotante(token_str):
                token = Token('nflotante', float(token_str), linea, inicio_columna)
                lista_de_tokens.append(token)
            elif es_numero_entero(token_str):
                token = Token('nentero', int(token_str), linea, inicio_columna)
                lista_de_tokens.append(token)
            elif es_palabra_reservada(token_str):
                token = Token(palabras_reservadas[token_str], token_str, linea, inicio_columna)
                lista_de_tokens.append(token)
            elif es_identificador_valido(token_str):
                token = Token('id', token_str, linea, inicio_columna)
                lista_de_tokens.append(token)
            else:
                error = Error(f"Token no reconocido: {token_str}", linea, inicio_columna)
                lista_errores_lexicos.append(error)
            continue
        
        # Caracter no reconocido
        error = Error(f"Caracter no reconocido: {caracter}", linea, columna)
        lista_errores_lexicos.append(error)
        i += 1

def crear_tabla_tokens():
    """Crea una tabla formateada con los tokens"""
    if not lista_de_tokens:
        return "No hay tokens para mostrar."
    
    headers = ["Tipo", "Valor", "Línea", "Columna"]
    data = []
    
    for token in lista_de_tokens:
        data.append([token.tipo, token.valor, token.linea, token.columna])
    
    return tabulate(data, headers=headers, tablefmt="grid")

def guardar_tokens_archivo():
    """Guarda los tokens en un archivo"""
    output_folder = 'salida-tokens'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    nombre_archivo_sin_extension = os.path.splitext(archivo)[0]
    nombre_archivo_salida = f"{nombre_archivo_sin_extension}-tokens.txt"
    ruta_salida = os.path.join(output_folder, nombre_archivo_salida)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(f"Análisis léxico del archivo: {archivo}\n")
        f.write("="*50 + "\n\n")
        
        if lista_errores_lexicos:
            f.write("ERRORES LÉXICOS:\n")
            for error in lista_errores_lexicos:
                f.write(f"- {error}\n")
            f.write("\n")
        
        f.write("TOKENS RECONOCIDOS:\n")
        f.write(crear_tabla_tokens())
    
    return ruta_salida

def mostrar_resultado_lexico(errores):
    """Muestra el resultado del análisis léxico"""
    print(f"\nCódigo a compilar: {archivo}\n")
    
    # Mostrar tabla de tokens
    print("Lista de Tokens:")
    print(crear_tabla_tokens())
    
    if errores:
        print("\nErrores lexicos encontrados:")
        for error in errores:
            print(f"  - {error}")
        print("\n❌ Análisis léxico fallido ❌\n")
        return False
    else:
        print("\nAnalisis lexico exitoso")
        ruta_archivo_tokens = guardar_tokens_archivo()
        print(f"Tokens escritos exitosamente en el archivo {ruta_archivo_tokens}\n")
        return True

# Ejecutar análisis léxico
if os.path.exists(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as file:
        contenido_archivo = file.read()
    
    # Limpiar listas anteriores
    lista_de_tokens.clear()
    lista_errores_lexicos.clear()
    
    # Realizar análisis léxico
    analizar_lexico(contenido_archivo)
else:
    print(f"❌ El archivo {archivo} no existe en la carpeta codigos-bocetos")
    exit(1)