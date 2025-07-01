import os

# Función helper que necesita assembly.py
def buscar_hijo(nodo, tipo):
    """Encuentra un hijo con el tipo especificado."""
    for hijo in nodo.hijos:
        if hijo.tipo == tipo:
            return hijo
    return None

class GeneradorAssembly:
    def __init__(self):
        self.codigo = []
        self.contador_etiquetas = 0
        self.contador_temporales = 0
        self.stack_offset = 0
        self.variables_locales = {}
        self.funciones_declaradas = set()
        self.en_funcion = False
        self.nombre_funcion_actual = ""
        
            
    def nueva_etiqueta(self, prefijo="L"):
        """Genera una nueva etiqueta única"""
        self.contador_etiquetas += 1
        return f"{prefijo}{self.contador_etiquetas}"
    
    def nuevo_temporal(self):
        """Genera un nuevo nombre de variable temporal"""
        self.contador_temporales += 1
        return f"temp{self.contador_temporales}"
    
    def agregar_codigo(self, instruccion, comentario=""):
        """Agrega una línea de código assembly"""
        if comentario:
            self.codigo.append(f"    {instruccion:<30} ; {comentario}")
        else:
            self.codigo.append(f"    {instruccion}")
    
    def agregar_etiqueta(self, etiqueta):
        """Agrega una etiqueta"""
        self.codigo.append(f"{etiqueta}:")
    
    def generar_preambulo(self):
        """Genera el preámbulo del programa assembly"""
        self.codigo.extend([
            ".section .data",
            "    format_int: .asciz \"%d\\n\"",
            "    format_float: .asciz \"%.2f\\n\"", 
            "    format_string: .asciz \"%s\\n\"",
            "    input_int: .asciz \"%d\"",
            "    input_float: .asciz \"%f\"",
            "    input_string: .asciz \"%s\"",
            "",
            ".section .bss",
            "    .lcomm buffer, 256",
            "",
            ".section .text",
            "    .global _start",
            ""
        ])
    
    def generar_epilogo(self):
        """Genera el epílogo del programa"""
        self.codigo.extend([
            "",
            "_start:",
            "    call main",
            "    mov %eax, %edi",
            "    mov $60, %eax",
            "    syscall",
            ""
        ])
    
    def obtener_offset_variable(self, nombre_var, ambito):
        """Obtiene el offset de una variable en el stack"""
        simbolo = ambito.buscar_simbolo(nombre_var)
        if not simbolo:
            return None
        
        if nombre_var not in self.variables_locales:
            self.stack_offset += 8  # 8 bytes por variable
            self.variables_locales[nombre_var] = -self.stack_offset
        
        return self.variables_locales[nombre_var]
    
    def generar_expresion(self, nodo_expresion, ambito):
        """Genera código para una expresión y retorna el registro donde está el resultado"""
        if not nodo_expresion:
            return None
            
        if nodo_expresion.tipo == 'expresion':
            primer_hijo = nodo_expresion.hijos[0] if nodo_expresion.hijos else None
            
            if primer_hijo and primer_hijo.tipo == 'valordato':
                return self.generar_valor_dato(primer_hijo)
            
            elif primer_hijo and primer_hijo.tipo == 'id':
                nombre_var = primer_hijo.valor
                offset = self.obtener_offset_variable(nombre_var, ambito)
                
                if offset is not None:
                    self.agregar_codigo(f"mov {offset}(%rbp), %rax", f"cargar variable {nombre_var}")
                    
                    # Verificar si hay operaciones adicionales
                    masexpresiones = buscar_hijo(nodo_expresion, 'masexpresiones')
                    if masexpresiones and masexpresiones.hijos and masexpresiones.hijos[0].tipo != 'e':
                        return self.generar_operacion_binaria(nodo_expresion, ambito, 'rax')
                    
                    return 'rax'
                
            elif primer_hijo and primer_hijo.tipo == 'pabierto':
                # Expresión entre paréntesis
                expr_interna = buscar_hijo(nodo_expresion, 'expresion')
                if expr_interna:
                    return self.generar_expresion(expr_interna, ambito)
                    
        elif nodo_expresion.tipo == 'valordato':
            return self.generar_valor_dato(nodo_expresion)
            
        return None
    
    def generar_valor_dato(self, nodo_valordato):
        """Genera código para un valor literal"""
        if not nodo_valordato.hijos:
            return None
            
        tipo_valor = nodo_valordato.hijos[0].tipo
        valor = nodo_valordato.hijos[0].valor
        
        if tipo_valor == 'nentero':
            self.agregar_codigo(f"mov ${valor}, %rax", f"cargar entero {valor}")
            return 'rax'
        elif tipo_valor == 'nflotante':
            # Para números flotantes necesitaríamos registros XMM
            self.agregar_codigo(f"mov ${int(valor * 100)}, %rax", f"cargar float {valor} como entero * 100")
            return 'rax'
        elif tipo_valor == 'ncadena':
            # Para cadenas necesitaríamos manejo especial
            etiqueta_string = self.nueva_etiqueta("str")
            self.codigo.insert(-1, f"    {etiqueta_string}: .asciz \"{valor}\"")
            self.agregar_codigo(f"lea {etiqueta_string}(%rip), %rax", f"cargar dirección de cadena")
            return 'rax'
            
        return None
    
    def generar_operacion_binaria(self, nodo_expresion, ambito, registro_izq):
        """Genera código para operaciones binarias"""
        masexpresiones = buscar_hijo(nodo_expresion, 'masexpresiones')
        if not masexpresiones or not masexpresiones.hijos:
            return registro_izq
            
        nodo_operacion = buscar_hijo(masexpresiones, 'operacion')
        nodo_expr_der = buscar_hijo(masexpresiones, 'expresion')
        
        if not nodo_operacion or not nodo_expr_der:
            return registro_izq
            
        # Guardar el valor izquierdo
        self.agregar_codigo(f"push %{registro_izq}", "guardar operando izquierdo")
        
        # Generar el operando derecho
        registro_der = self.generar_expresion(nodo_expr_der, ambito)
        
        if registro_der:
            # Recuperar operando izquierdo
            self.agregar_codigo("pop %rbx", "recuperar operando izquierdo")
            
            # Generar la operación
            tipo_op = nodo_operacion.hijos[0].tipo
            
            if tipo_op == 'suma':
                self.agregar_codigo(f"add %{registro_der}, %rbx", "suma")
            elif tipo_op == 'resta':
                self.agregar_codigo(f"sub %{registro_der}, %rbx", "resta")
            elif tipo_op == 'mul':
                self.agregar_codigo(f"imul %{registro_der}, %rbx", "multiplicación")
            elif tipo_op == 'div':
                self.agregar_codigo("cqo", "extender signo para división")
                self.agregar_codigo(f"idiv %{registro_der}", "división")
                self.agregar_codigo("mov %rax, %rbx", "mover resultado a rbx")
            elif tipo_op == 'menorque':
                self.agregar_codigo(f"cmp %{registro_der}, %rbx", "comparar <")
                self.agregar_codigo("setl %al", "establecer si menor")
                self.agregar_codigo("movzbl %al, %ebx", "extender resultado")
            elif tipo_op == 'mayorque':
                self.agregar_codigo(f"cmp %{registro_der}, %rbx", "comparar >")
                self.agregar_codigo("setg %al", "establecer si mayor")
                self.agregar_codigo("movzbl %al, %ebx", "extender resultado")
            elif tipo_op == 'igualbool':
                self.agregar_codigo(f"cmp %{registro_der}, %rbx", "comparar ==")
                self.agregar_codigo("sete %al", "establecer si igual")
                self.agregar_codigo("movzbl %al, %ebx", "extender resultado")
            
            self.agregar_codigo("mov %rbx, %rax", "mover resultado final")
            return 'rax'
            
        return registro_izq
    
    def generar_asignacion(self, nodo_asignaciones, ambito):
        """Genera código para asignaciones"""
        nodo_id = buscar_hijo(nodo_asignaciones, 'id')
        nodo_ext = buscar_hijo(nodo_asignaciones, 'ext')
        
        if not nodo_id or not nodo_ext:
            return
            
        nombre_var = nodo_id.valor
        
        # Buscar la expresión a asignar
        nodo_expresion = None
        
        # Caso 1: declaración con tipo
        if nodo_ext.hijos and nodo_ext.hijos[0].tipo == 'tipodato':
            nodo_opcionesasig = buscar_hijo(nodo_ext, 'opcionesasig')
            if nodo_opcionesasig and nodo_opcionesasig.hijos:
                nodo_expresion = buscar_hijo(nodo_opcionesasig, 'expresion')
        
        # Caso 2: asignación directa
        elif nodo_ext.hijos and nodo_ext.hijos[0].tipo == 'extension':
            nodo_extension = nodo_ext.hijos[0]
            nodo_expresion = buscar_hijo(nodo_extension, 'expresion')
        
        if nodo_expresion:
            # Generar código para la expresión
            registro = self.generar_expresion(nodo_expresion, ambito)
            
            if registro:
                # Almacenar en la variable
                offset = self.obtener_offset_variable(nombre_var, ambito)
                if offset is not None:
                    self.agregar_codigo(f"mov %{registro}, {offset}(%rbp)", f"asignar a {nombre_var}")
    
    def generar_show(self, nodo_mostrar, ambito):
        """Genera código para la función show/imprimir"""
        nodo_comandos = buscar_hijo(nodo_mostrar, 'comandos')
        if not nodo_comandos:
            return
            
        # Buscar la expresión a mostrar
        nodo_expresion = buscar_hijo(nodo_comandos, 'expresion')
        if nodo_expresion:
            registro = self.generar_expresion(nodo_expresion, ambito)
            
            if registro:
                # Preparar llamada a printf
                self.agregar_codigo("mov %rax, %rsi", "segundo argumento para printf")
                self.agregar_codigo("lea format_int(%rip), %rdi", "formato para printf")
                self.agregar_codigo("mov $0, %eax", "número de argumentos vectoriales")
                self.agregar_codigo("call printf", "llamar printf")
    
    def generar_condicional(self, nodo_condicional, ambito):
        """Genera código para estructuras if-else"""
        # Buscar la expresión condicional
        nodo_expresion = buscar_hijo(nodo_condicional, 'expresion')
        
        etiqueta_false = self.nueva_etiqueta("else")
        etiqueta_end = self.nueva_etiqueta("endif")
        
        if nodo_expresion:
            registro = self.generar_expresion(nodo_expresion, ambito)
            
            if registro:
                self.agregar_codigo(f"cmp $0, %{registro}", "evaluar condición")
                self.agregar_codigo(f"je {etiqueta_false}", "saltar si falso")
        
        # Generar código del bloque if
        nodo_instrucciones = buscar_hijo(nodo_condicional, 'masinstrucciones')
        if nodo_instrucciones:
            self.generar_instrucciones(nodo_instrucciones, ambito)
        
        self.agregar_codigo(f"jmp {etiqueta_end}", "saltar al final")
        self.agregar_etiqueta(etiqueta_false)
        
        # Buscar posible bloque else
        nodo_posibilidad = buscar_hijo(nodo_condicional, 'posibilidad')
        if nodo_posibilidad and nodo_posibilidad.hijos:
            primer_hijo = nodo_posibilidad.hijos[0]
            if primer_hijo.tipo == 'sino':
                # Hay bloque else
                nodo_instrucciones_else = buscar_hijo(nodo_posibilidad, 'masinstrucciones')
                if nodo_instrucciones_else:
                    self.generar_instrucciones(nodo_instrucciones_else, ambito)
        
        self.agregar_etiqueta(etiqueta_end)
    
    def generar_while(self, nodo_while, ambito):
        """Genera código para bucles while"""
        etiqueta_inicio = self.nueva_etiqueta("while_start")
        etiqueta_fin = self.nueva_etiqueta("while_end")
        
        self.agregar_etiqueta(etiqueta_inicio)
        
        # Evaluar condición
        nodo_expresion = buscar_hijo(nodo_while, 'expresion')
        if nodo_expresion:
            registro = self.generar_expresion(nodo_expresion, ambito)
            
            if registro:
                self.agregar_codigo(f"cmp $0, %{registro}", "evaluar condición while")
                self.agregar_codigo(f"je {etiqueta_fin}", "salir si falso")
        
        # Generar código del cuerpo
        nodo_instrucciones = buscar_hijo(nodo_while, 'masinstrucciones')
        if nodo_instrucciones:
            self.generar_instrucciones(nodo_instrucciones, ambito)
        
        self.agregar_codigo(f"jmp {etiqueta_inicio}", "volver al inicio del bucle")
        self.agregar_etiqueta(etiqueta_fin)
    
    def generar_return(self, nodo_return, ambito):
        """Genera código para return"""
        nodo_expresion = buscar_hijo(nodo_return, 'expresion')
        if nodo_expresion:
            registro = self.generar_expresion(nodo_expresion, ambito)
            
            if registro and registro != 'rax':
                self.agregar_codigo(f"mov %{registro}, %rax", "mover valor de retorno a rax")
        
        # Restaurar stack y retornar
        self.agregar_codigo("mov %rbp, %rsp", "restaurar stack pointer")
        self.agregar_codigo("pop %rbp", "restaurar base pointer")
        self.agregar_codigo("ret", "retornar")
    
    def generar_instruccion(self, nodo_instruccion, ambito):
        """Genera código para una instrucción individual"""
        if not nodo_instruccion.hijos:
            return
            
        tipo_instruccion = nodo_instruccion.hijos[0]
        
        if tipo_instruccion.tipo == 'asignaciones':
            self.generar_asignacion(tipo_instruccion, ambito)
        elif tipo_instruccion.tipo == 'mostrar':
            self.generar_show(tipo_instruccion, ambito)
        elif tipo_instruccion.tipo == 'condicional':
            self.generar_condicional(tipo_instruccion, ambito)
        elif tipo_instruccion.tipo == 'buclemientras':
            self.generar_while(tipo_instruccion, ambito)
        elif tipo_instruccion.tipo == 'devolver':
            self.generar_return(nodo_instruccion, ambito)
    
    def generar_instrucciones(self, nodo_masinstrucciones, ambito):
        """Genera código para múltiples instrucciones"""
        if not nodo_masinstrucciones or not nodo_masinstrucciones.hijos:
            return
            
        for hijo in nodo_masinstrucciones.hijos:
            if hijo.tipo == 'instruccion':
                self.generar_instruccion(hijo, ambito)
            elif hijo.tipo == 'masinstrucciones':
                self.generar_instrucciones(hijo, ambito)
    
    def generar_funcion(self, nodo_funcion, ambito, nombre_funcion):
        """Genera código para una función"""
        self.en_funcion = True
        self.nombre_funcion_actual = nombre_funcion
        self.variables_locales.clear()
        self.stack_offset = 0
        
        # Etiqueta de la función
        self.agregar_etiqueta(nombre_funcion)
        
        # Prólogo de la función
        self.agregar_codigo("push %rbp", "guardar base pointer")
        self.agregar_codigo("mov %rsp, %rbp", "establecer nuevo base pointer")
        
        # Reservar espacio para variables locales (se calculará dinámicamente)
        pos_reserva_espacio = len(self.codigo)
        self.agregar_codigo("", "# RESERVAR_ESPACIO_PLACEHOLDER")
        
        # Generar código para el cuerpo de la función
        nodo_instrucciones = buscar_hijo(nodo_funcion, 'masinstrucciones')
        if nodo_instrucciones:
            # Usar el ámbito de la función
            if ambito.hijos:
                ambito_funcion = ambito.hijos[0]
                self.generar_instrucciones(nodo_instrucciones, ambito_funcion)
        
        # Actualizar la reserva de espacio
        if self.stack_offset > 0:
            self.codigo[pos_reserva_espacio] = f"    sub ${self.stack_offset}, %rsp    ; reservar espacio para variables locales"
        else:
            self.codigo[pos_reserva_espacio] = ""
        
        # Epílogo por defecto (si no hay return explícito)
        if nombre_funcion == 'main':
            self.agregar_codigo("mov $0, %eax", "valor de retorno por defecto")
        
        self.agregar_codigo("mov %rbp, %rsp", "restaurar stack pointer")
        self.agregar_codigo("pop %rbp", "restaurar base pointer")
        self.agregar_codigo("ret", "retornar")
        self.agregar_codigo("", "")
        
        self.en_funcion = False
    
    def generar_programa(self, nodo_programa, ambito):
        """Genera código para todo el programa"""
        if nodo_programa.tipo != 'programaprincipal':
            return
        
        # Procesar funciones en el programa
        nodo_actual = nodo_programa
        indice_ambito = 0
        
        while nodo_actual and nodo_actual.tipo == 'programaprincipal':
            # Buscar función definida
            nodo_funcion = buscar_hijo(nodo_actual, 'funcion')
            nodo_opcionprincipal = buscar_hijo(nodo_actual, 'opcionprincipal')
            
            if nodo_funcion and nodo_funcion.hijos:
                # Función regular
                nodo_func = nodo_funcion.hijos[0]  # restofuncn
                nodo_id = buscar_hijo(nodo_func, 'id')
                if nodo_id and nodo_id.valor:
                    nombre_func = nodo_id.valor
                    ambito_func = ambito if indice_ambito >= len(ambito.simbolos) else ambito
                    self.generar_funcion(nodo_func, ambito_func, nombre_func)
                    indice_ambito += 1
                    
            elif nodo_opcionprincipal and nodo_opcionprincipal.hijos:
                # Función main o función regular
                nodo_func = nodo_opcionprincipal.hijos[0]
                if nodo_func.tipo == 'restomain':
                    self.generar_funcion(nodo_func, ambito, 'main')
                elif nodo_func.tipo == 'restofuncn':
                    nodo_id = buscar_hijo(nodo_func, 'id')
                    if nodo_id and nodo_id.valor:
                        nombre_func = nodo_id.valor
                        ambito_func = ambito if indice_ambito >= len(ambito.simbolos) else ambito
                        self.generar_funcion(nodo_func, ambito_func, nombre_func)
                        indice_ambito += 1
            
            # Continuar con más funciones
            nodo_masfuncn = buscar_hijo(nodo_actual, 'masfuncn')
            if nodo_masfuncn and nodo_masfuncn.hijos:
                nodo_actual = nodo_masfuncn.hijos[0]
            else:
                break
    
    def generar(self, arbol_sintactico, tabla_simbolos):
        """Función principal que genera todo el código assembly"""
        self.generar_preambulo()
        self.generar_programa(arbol_sintactico, tabla_simbolos)
        self.generar_epilogo()
        
        return '\n'.join(self.codigo)

def guardar_codigo_assembly(codigo_asm, nombre_archivo):
    """Guarda el código assembly en un archivo"""
    output_folder = 'salida-assembly'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    nombre_archivo_sin_extension = os.path.splitext(nombre_archivo)[0]
    nombre_archivo_salida = f"{nombre_archivo_sin_extension}.s"
    ruta_salida = os.path.join(output_folder, nombre_archivo_salida)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(codigo_asm)
    
    return ruta_salida

def ejecutar_generacion_assembly():
    """Función principal que ejecuta la generación de assembly"""
    # Verificar que el análisis previo fue exitoso
    if not respuesta or errores_sintacticos or errores_semanticos:
        print("❌ No se puede generar assembly debido a errores previos")
        return False
    
    print("\n🔧 Iniciando generación de código assembly...")
    
    try:
        generador = GeneradorAssembly()
        codigo_assembly = generador.generar(arbol_sintactico, tabla_simbolos)
        
        # Guardar el código generado
        ruta_archivo = guardar_codigo_assembly(codigo_assembly, archivo)
        
        print(f"✅ Código assembly generado exitosamente: {ruta_archivo}")
        print("\n📋 Código generado:")
        print("-" * 50)
        print(codigo_assembly)
        print("-" * 50)
        
        # Instrucciones para compilar y ejecutar
        print("\n🚀 Para compilar y ejecutar:")
        print(f"   gcc -no-pie -o programa {ruta_archivo}")
        print("   ./programa")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la generación de assembly: {str(e)}")
        return False

# Ejecutar la generación de assembly solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    ejecutar_generacion_assembly()