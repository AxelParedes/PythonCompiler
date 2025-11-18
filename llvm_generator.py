# llvm_generator.py - VERSIÓN MEJORADA CON SOPORTE PARA VARIABLES
class LLVMGenerator:
    def __init__(self):
        self.llvm_code = []
        self.temp_counter = 0
        self.string_counter = 0
        self.variables = set()
        
    def generate(self, quadruples, symbol_table):
        """Genera código LLVM a partir de cuádruplos"""
        self.llvm_code = []
        self.temp_counter = 0
        self.string_counter = 0
        self.variables = set()
        self.symbol_table = symbol_table
        
        print(f"DEBUG LLVM: Generando código desde {len(quadruples)} cuádruplos")
        
        # Recopilar todas las variables
        for quad in quadruples:
            if quad['type'] == 'assign':
                self.variables.add(quad['target'])
            elif quad['type'] == 'output' and quad.get('value_type') == 'variable':
                self.variables.add(quad['value'])
            elif quad['type'] == 'binary_op':
                self.variables.add(quad['target'])
                if isinstance(quad['left'], str) and not quad['left'].startswith('"'):
                    self.variables.add(quad['left'])
                if isinstance(quad['right'], str) and not quad['right'].startswith('"'):
                    self.variables.add(quad['right'])
        
        # Cabecera
        self._add_header()
        
        # Declaraciones
        self._add_declarations()
        
        # Función main
        self._add_function_header()
        
        # Inicializar variables
        self._initialize_variables()
        
        # Generar código
        self._generate_from_quadruples(quadruples)
        
        # Retorno
        self._add_code("ret i32 0")
        self._add_code("}")
        
        return "\n".join(self.llvm_code)
    
    def _add_header(self):
        """Agrega cabecera LLVM"""
        self.llvm_code.append('target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"')
        self.llvm_code.append('target triple = "x86_64-pc-linux-gnu"')
        self.llvm_code.append('')
    
    def _add_declarations(self):
        """Agrega declaraciones de funciones y strings"""
        self.llvm_code.append('; Declaraciones de funciones externas')
        self.llvm_code.append('declare i32 @printf(i8*, ...)')
        self.llvm_code.append('')
        
        # Strings de formato
        self.llvm_code.append('; Strings de formato')
        self.llvm_code.append('@.str_int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"')
        self.llvm_code.append('@.str_float = private unnamed_addr constant [4 x i8] c"%f\\0A\\00"')
        self.llvm_code.append('@.str_string = private unnamed_addr constant [4 x i8] c"%s\\00"')
        self.llvm_code.append('')
    
    def _add_function_header(self):
        """Agrega cabecera de función main"""
        self.llvm_code.append('define i32 @main() {')
    
    def _initialize_variables(self):
        """Inicializa variables locales"""
        if self.variables:
            self.llvm_code.append('; Inicialización de variables')
            for var in self.variables:
                if not var.startswith('t'):  # No inicializar temporales
                    self._add_code(f"%{var} = alloca i32")
                    self._add_code(f"store i32 0, i32* %{var}")
            self.llvm_code.append('')
    
    def _add_code(self, code):
        """Agrega una línea de código LLVM"""
        self.llvm_code.append(f"  {code}")
    
    def _generate_from_quadruples(self, quadruples):
        """Genera código desde cuádruplos"""
        for i, quad in enumerate(quadruples):
            print(f"DEBUG LLVM: Procesando cuádruplo {i}: {quad}")
            
            if quad['type'] == 'assign':
                self._generate_assignment(quad)
            elif quad['type'] == 'binary_op':
                self._generate_binary_operation(quad)
            elif quad['type'] == 'output':
                self._generate_output(quad)
    
    def _generate_assignment(self, quad):
        """Genera código para asignación"""
        target = quad['target']
        source = quad['source']
        source_type = quad.get('source_type', 'direct')
        
        if source_type == 'direct':
            # Asignación directa: a = 5
            self._add_code(f"store i32 {source}, i32* %{target}")
        else:
            # Asignación desde variable: a = b
            temp = self._new_temp()
            self._add_code(f"{temp} = load i32, i32* %{source}")
            self._add_code(f"store i32 {temp}, i32* %{target}")
    
    def _generate_binary_operation(self, quad):
        """Genera código para operación binaria"""
        target = quad['target']
        left = quad['left']
        right = quad['right']
        operator = quad['operator']
        
        # Cargar operandos
        left_val = self._load_operand(left)
        right_val = self._load_operand(right)
        
        # Generar operación
        temp = self._new_temp()
        if operator == '+':
            self._add_code(f"{temp} = add i32 {left_val}, {right_val}")
        elif operator == '-':
            self._add_code(f"{temp} = sub i32 {left_val}, {right_val}")
        elif operator == '*':
            self._add_code(f"{temp} = mul i32 {left_val}, {right_val}")
        elif operator == '/':
            self._add_code(f"{temp} = sdiv i32 {left_val}, {right_val}")
        
        # Almacenar resultado
        self._add_code(f"store i32 {temp}, i32* %{target}")
    
    def _generate_output(self, quad):
        """Genera código para output"""
        value = quad['value']
        value_type = quad.get('value_type', 'string')
        
        if value_type == 'string':
            # Output de string literal
            string_content = value.strip('"')
            str_name = f"@.str_{self.string_counter}"
            self.string_counter += 1
            
            # Agregar string constante
            self.llvm_code.insert(-2, f'{str_name} = private unnamed_addr constant [{len(string_content) + 1} x i8] c"{string_content}\\00"')
            
            self._add_code(f'call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str_string, i32 0, i32 0), i8* getelementptr inbounds ([{len(string_content) + 1} x i8], [{len(string_content) + 1} x i8]* {str_name}, i32 0, i32 0))')
        
        elif value_type in ['variable', 'number']:
            # Output de variable o número
            if value_type == 'variable':
                # Cargar valor de variable
                temp = self._new_temp()
                self._add_code(f"{temp} = load i32, i32* %{value}")
                value_to_print = temp
            else:
                # Valor directo
                value_to_print = value
            
            self._add_code(f'call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str_int, i32 0, i32 0), i32 {value_to_print})')
    
    def _load_operand(self, operand):
        """Carga un operando (constante o variable)"""
        if isinstance(operand, int):
            return str(operand)
        elif operand.isdigit():
            return operand
        else:
            # Es una variable
            temp = self._new_temp()
            self._add_code(f"{temp} = load i32, i32* %{operand}")
            return temp
    
    def _new_temp(self):
        """Genera un nuevo temporal"""
        temp = f"%t{self.temp_counter}"
        self.temp_counter += 1
        return temp

# llvm_generator.py - Generador básico de código LLVM
def generate_llvm_code(quadruples, symbol_table):
    """Genera código LLVM a partir de cuádruplos"""
    
    llvm_code = []
    
    # Cabecera
    llvm_code.append("; Código LLVM generado por el compilador")
    llvm_code.append('target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"')
    llvm_code.append('target triple = "x86_64-pc-linux-gnu"')
    llvm_code.append('')
    
    # Declaraciones de funciones
    llvm_code.append('declare i32 @printf(i8*, ...)')
    llvm_code.append('@.str = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"')
    llvm_code.append('')
    
    # Variables globales (todas las variables del símbolo)
    for var_name in symbol_table.keys():
        llvm_code.append(f'@{var_name} = global i32 0')
    
    llvm_code.append('')
    
    # Función main
    llvm_code.append('define i32 @main() {')
    
    # Procesar cuádruplos
    for quad in quadruples:
        if quad['type'] == 'assign':
            target = quad['target']
            source = quad['source']
            
            if isinstance(source, int):
                llvm_code.append(f'  store i32 {source}, i32* @{target}')
            else:
                # Si es otra variable, cargar y almacenar
                llvm_code.append(f'  %temp = load i32, i32* @{source}')
                llvm_code.append(f'  store i32 %temp, i32* @{target}')
                
        elif quad['type'] == 'binary_op':
            target = quad['target']
            left = quad['left']
            right = quad['right']
            operator = quad['operator']
            
            # Cargar operandos
            if isinstance(left, int):
                left_val = left
            else:
                llvm_code.append(f'  %left = load i32, i32* @{left}')
                left_val = '%left'
                
            if isinstance(right, int):
                right_val = right
            else:
                llvm_code.append(f'  %right = load i32, i32* @{right}')
                right_val = '%right'
            
            # Operación
            if operator == '+':
                llvm_code.append(f'  %{target} = add i32 {left_val}, {right_val}')
            elif operator == '-':
                llvm_code.append(f'  %{target} = sub i32 {left_val}, {right_val}')
            elif operator == '*':
                llvm_code.append(f'  %{target} = mul i32 {left_val}, {right_val}')
            
            # Almacenar resultado si es una variable
            if not target.startswith('t'):
                llvm_code.append(f'  store i32 %{target}, i32* @{target}')
                
        elif quad['type'] == 'output':
            value = quad['value']
            
            if isinstance(value, int):
                llvm_code.append(f'  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), i32 {value})')
            elif value.startswith('"'):
                # String literal - crear constante para este string
                str_content = value.strip('"')
                str_const = f'@.str_{len(llvm_code)}'
                llvm_code.insert(5, f'{str_const} = private unnamed_addr constant [{len(str_content)+3} x i8] c"{str_content}\\0A\\00"')
                llvm_code.append(f'  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([{len(str_content)+3} x i8], [{len(str_content)+3} x i8]* {str_const}, i32 0, i32 0))')
            else:
                # Variable
                llvm_code.append(f'  %out_val = load i32, i32* @{value}')
                llvm_code.append(f'  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), i32 %out_val)')
    
    llvm_code.append('  ret i32 0')
    llvm_code.append('}')
    
    return '\n'.join(llvm_code)