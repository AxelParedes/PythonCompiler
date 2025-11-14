# llvm_generator.py - VERSIÓN CORREGIDA
class LLVMGenerator:
    def __init__(self):
        self.llvm_code = []
        self.temp_counter = 0
        self.label_counter = 0
        self.string_counter = 0
        self.string_table = {}
        self.current_block = "entry"
        
    def generate(self, intermediate_code, symbol_table):
        """Genera código LLVM a partir del código intermedio - VERSIÓN CORREGIDA"""
        self.llvm_code = []
        self.temp_counter = 0
        self.label_counter = 0
        self.string_counter = 0
        self.string_table = {}
        self.current_block = "entry"
        
        # Cabecera LLVM
        self._add_header()
        
        # Declaraciones de funciones externas
        self._add_external_declarations()
        
        # Declaraciones de variables globales
        self._add_global_declarations(symbol_table)
        
        # Función main
        self._add_function_header("main", "i32")
        
        # Inicializar variables
        self._initialize_variables(symbol_table)
        
        # Generar código desde los cuádruplos
        self._generate_from_quadruples(intermediate_code, symbol_table)
        
        # Retorno de main
        self._add_code("ret i32 0")
        
        # Final de función
        self._add_code("}")
        
        # Agregar strings constantes
        self._add_string_constants()
        
        return "\n".join(self.llvm_code)
    
    def _add_header(self):
        """Agrega cabecera LLVM"""
        self.llvm_code.append("; Código LLVM generado por el compilador")
        self.llvm_code.append('target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"')
        self.llvm_code.append('target triple = "x86_64-pc-windows-msvc"')
        self.llvm_code.append("")
    
    def _add_external_declarations(self):
        """Declara funciones externas (printf, scanf) - VERSIÓN WINDOWS"""
        self.llvm_code.append("; Declaraciones de funciones externas")
        self.llvm_code.append('declare i32 @printf(i8* nocapture readonly, ...)')
        self.llvm_code.append('declare i32 @scanf(i8* nocapture readonly, ...)')
        self.llvm_code.append('declare i32 @_getch()')
        self.llvm_code.append("")
    
    def _add_global_declarations(self, symbol_table):
        """Declara variables globales"""
        if any(sym.get('alcance') == 'global' for sym in symbol_table.values()):
            self.llvm_code.append("; Variables globales")
            for name, info in symbol_table.items():
                if info.get('alcance') == 'global':
                    var_type = self._get_llvm_type(info.get('tipo', 'int'))
                    self.llvm_code.append(f"@{name} = global {var_type} 0")
            self.llvm_code.append("")
    
    def _add_function_header(self, name, return_type):
        """Agrega cabecera de función"""
        self.llvm_code.append(f"define {return_type} @{name}() {{")
        self.current_block = "entry"
    
    def _initialize_variables(self, symbol_table):
        """Inicializa variables locales"""
        for name, info in symbol_table.items():
            if info.get('alcance') != 'global':
                var_type = self._get_llvm_type(info.get('tipo', 'int'))
                self._add_code(f"%{name} = alloca {var_type}")
                self._add_code(f"store {var_type} 0, {var_type}* %{name}")
    
    def _add_code(self, code):
        """Agrega una línea de código LLVM"""
        if code.startswith(('L', 'if.', 'else.')) and code.endswith(':'):
            # Es una etiqueta - formatear correctamente
            label_name = code[:-1]  # Remover el :
            self.llvm_code.append(f"{label_name}:")
            self.current_block = label_name
        else:
            self.llvm_code.append(f"  {code}")
    
    def _generate_from_quadruples(self, quadruples, symbol_table):
        """Genera código LLVM a partir de cuádruplos - VERSIÓN CORREGIDA"""
        for quad in quadruples:
            try:
                if quad['type'] == 'assign':
                    self._generate_assignment(quad, symbol_table)
                elif quad['type'] == 'binary_op':
                    self._generate_binary_operation(quad, symbol_table)
                elif quad['type'] == 'unary_op':
                    self._generate_unary_operation(quad, symbol_table)
                elif quad['type'] == 'if_false_goto':
                    self._generate_conditional_jump(quad, False)
                elif quad['type'] == 'if_true_goto':
                    self._generate_conditional_jump(quad, True)
                elif quad['type'] == 'goto':
                    self._generate_unconditional_jump(quad)
                elif quad['type'] == 'label':
                    self._generate_label(quad)
                elif quad['type'] == 'input':
                    self._generate_input(quad, symbol_table)
                elif quad['type'] == 'output':
                    self._generate_output(quad, symbol_table)
            except Exception as e:
                print(f"Error generando código para: {quad} - {e}")
                continue
    
    def _generate_assignment(self, quad, symbol_table):
        """Genera código para asignación - VERSIÓN CORREGIDA"""
        target = quad['target']
        source = quad['source']
        
        # Determinar tipo
        var_type = self._infer_type(source, symbol_table)
        llvm_type = self._get_llvm_type(var_type)
        
        # Obtener referencia a la variable
        target_ref = f"@{target}" if symbol_table.get(target, {}).get('alcance') == 'global' else f"%{target}"
        
        if isinstance(source, (int, float)):
            self._add_code(f"store {llvm_type} {source}, {llvm_type}* {target_ref}")
        elif self._is_constant(source):
            self._add_code(f"store {llvm_type} {source}, {llvm_type}* {target_ref}")
        else:
            # Cargar desde otra variable
            source_ref = f"@{source}" if symbol_table.get(source, {}).get('alcance') == 'global' else f"%{source}"
            temp = self._new_temp()
            self._add_code(f"{temp} = load {llvm_type}, {llvm_type}* {source_ref}")
            self._add_code(f"store {llvm_type} {temp}, {llvm_type}* {target_ref}")
    
    def _generate_label(self, quad):
        """Genera etiqueta - VERSIÓN CORREGIDA"""
        label = quad['name']
        self._add_code(f"{label}:")
    
    def _generate_conditional_jump(self, quad, is_true):
        """Genera salto condicional - VERSIÓN CORREGIDA"""
        condition = quad['condition']
        label = quad['label']
        
        # Cargar condición
        if self._is_constant(condition):
            condition_value = 1 if condition else 0
            condition_temp = f"i1 {condition_value}"
        else:
            condition_var = f"@{condition}" if self._is_global(condition) else f"%{condition}"
            condition_temp = self._new_temp()
            self._add_code(f"{condition_temp} = load i32, i32* {condition_var}")
            
            # Convertir a booleano
            bool_temp = self._new_temp()
            self._add_code(f"{bool_temp} = icmp ne i32 {condition_temp}, 0")
            condition_temp = bool_temp
        
        # Generar salto
        if is_true:
            self._add_code(f"br i1 {condition_temp}, label %{label}, label %{label}_exit")
            self._add_code(f"{label}_exit:")
        else:
            self._add_code(f"br i1 {condition_temp}, label %{label}_exit, label %{label}")
            self._add_code(f"{label}_exit:")
    
    def _generate_unconditional_jump(self, quad):
        """Genera salto incondicional - VERSIÓN CORREGIDA"""
        label = quad['label']
        self._add_code(f"br label %{label}")
    
    def _generate_input(self, quad, symbol_table):
        """Genera código para entrada - VERSIÓN WINDOWS"""
        target = quad['target']
        var_info = symbol_table.get(target, {})
        var_type = var_info.get('tipo', 'int')
        
        # Determinar formato y tipo
        if var_type == 'int':
            format_str = self._get_string_constant("%d\\00")
            scanf_type = "i32*"
            format_name = "@.scanf_int"
        elif var_type == 'float':
            format_str = self._get_string_constant("%lf\\00")
            scanf_type = "double*"
            format_name = "@.scanf_float"
        else:
            format_str = self._get_string_constant("%d\\00")
            scanf_type = "i32*"
            format_name = "@.scanf_int"
        
        # Referencia a la variable
        target_ref = f"@{target}" if var_info.get('alcance') == 'global' else f"%{target}"
        
        # Llamada a scanf
        self._add_code(f"call i32 (i8*, ...) @scanf(i8* {format_name}, {scanf_type} {target_ref})")
    
    def _generate_output(self, quad, symbol_table):
        """Genera código para salida - VERSIÓN CORREGIDA"""
        value = quad['value']
        
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            # String literal
            str_content = value[1:-1] + "\\0A\\00"  # Agregar newline y null terminator
            str_constant = self._get_string_constant(str_content)
            self._add_code(f'call i32 (i8*, ...) @printf(i8* {str_constant})')
        else:
            # Valor numérico o variable
            value_type = self._infer_type(value, symbol_table)
            
            if value_type == 'int':
                format_str = self._get_string_constant("%d\\0A\\00")
                format_name = "@.printf_int"
                
                if self._is_constant(value):
                    value_temp = str(value)
                else:
                    value_ref = f"@{value}" if self._is_global(value) else f"%{value}"
                    value_temp = self._new_temp()
                    self._add_code(f"{value_temp} = load i32, i32* {value_ref}")
                
                self._add_code(f'call i32 (i8*, ...) @printf(i8* {format_name}, i32 {value_temp})')
                
            elif value_type == 'float':
                format_str = self._get_string_constant("%f\\0A\\00")
                format_name = "@.printf_float"
                
                if self._is_constant(value):
                    value_temp = str(value)
                else:
                    value_ref = f"@{value}" if self._is_global(value) else f"%{value}"
                    value_temp = self._new_temp()
                    self._add_code(f"{value_temp} = load double, double* {value_ref}")
                
                self._add_code(f'call i32 (i8*, ...) @printf(i8* {format_name}, double {value_temp})')
    
    def _is_constant(self, value):
        """Verifica si un valor es constante"""
        return isinstance(value, (int, float, bool)) or (isinstance(value, str) and value.replace('.', '').isdigit())
    
    def _is_global(self, var_name):
        """Verifica si una variable es global"""
        # Asumir que los temporales no son globales
        return not var_name.startswith('t')
    
    def _get_llvm_type(self, value_type):
        """Obtiene el tipo LLVM correspondiente"""
        type_map = {
            'int': 'i32',
            'float': 'double', 
            'bool': 'i1',
            'string': 'i8*'
        }
        return type_map.get(value_type, 'i32')
    
    def _infer_type(self, value, symbol_table):
        """Infiere el tipo de un valor"""
        if isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, str):
            if value in symbol_table:
                return symbol_table[value].get('tipo', 'int')
            elif value.replace('.', '').isdigit():
                return 'float' if '.' in value else 'int'
            elif value.startswith('t'):
                return 'int'  # Los temporales son int por defecto
        return 'int'
    
    def _new_temp(self):
        """Genera un nuevo temporal LLVM"""
        temp = f"%t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def _get_string_constant(self, string):
        """Obtiene o crea una constante string"""
        if string not in self.string_table:
            str_name = f"@.str.{self.string_counter}"
            self.string_counter += 1
            self.string_table[string] = str_name
        return self.string_table[string]
    
    def _add_string_constants(self):
        """Agrega las constantes string al final del código"""
        if self.string_table:
            self.llvm_code.append("")
            self.llvm_code.append("; String constants")
            for string, name in self.string_table.items():
                length = len(string.encode('utf-8'))  # Longitud en bytes
                self.llvm_code.append(f'{name} = private unnamed_addr constant [{length} x i8] c"{string}"')

def generate_llvm_code(intermediate_code, symbol_table):
    """Función principal para generar código LLVM"""
    generator = LLVMGenerator()
    llvm_code = generator.generate(intermediate_code, symbol_table)
    return llvm_code