# intermedio.py - Generación de código intermedio (cuádruplos)
class IntermediateCodeGenerator:
    def __init__(self):
        self.quadruples = []
        self.temp_counter = 0
        self.label_counter = 0
        self.symbol_table = None
        
    def generate(self, ast, symbol_table):
        """Genera código intermedio a partir del AST"""
        self.quadruples = []
        self.temp_counter = 0
        self.label_counter = 0
        self.symbol_table = symbol_table
        
        if ast and ast.type == 'programa':
            self._generate_program(ast)
        
        return self.quadruples
    
    def _new_temp(self):
        """Genera un nuevo temporal"""
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def _new_label(self):
        """Genera una nueva etiqueta"""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def _generate_program(self, node):
        """Genera código para el programa principal"""
        if node.children:
            self._generate_declarations(node.children[0])
    
    def _generate_declarations(self, node):
        """Genera código para declaraciones"""
        if not node or not node.children:
            return
            
        for child in node.children:
            if child.type == 'declaracion_variable':
                self._generate_variable_declaration(child)
            elif child.type == 'asignacion':
                self._generate_assignment(child)
            elif child.type == 'if':
                self._generate_if_statement(child)
            elif child.type == 'if_else':
                self._generate_if_else_statement(child)
            elif child.type == 'while':
                self._generate_while_statement(child)
            elif child.type == 'do_while':
                self._generate_do_while_statement(child)
            elif child.type == 'input':
                self._generate_input(child)
            elif child.type == 'output':
                self._generate_output(child)
    
    def _generate_variable_declaration(self, node):
        """Genera código para declaración de variables"""
        # En código intermedio, las declaraciones no generan cuádruplos
        # Solo se procesan para la tabla de símbolos
        pass
    
    def _generate_assignment(self, node):
        """Genera código para asignación"""
        if len(node.children) >= 2:
            target = node.children[0].value
            expr_result = self._generate_expression(node.children[1])
            
            self.quadruples.append({
                'type': 'assign',
                'target': target,
                'source': expr_result
            })
    
    def _generate_expression(self, node):
        """Genera código para expresiones y retorna el temporal resultante"""
        if node.type == 'identificador':
            return node.value
        elif node.type == 'numero':
            return node.value
        elif node.type == 'booleano':
            return 1 if node.value == 'true' else 0
        elif node.type == 'string_literal':
            return f'"{node.value}"'
        elif node.type == 'expresion_binaria':
            return self._generate_binary_expression(node)
        elif node.type == 'operacion_unaria':
            return self._generate_unary_expression(node)
        
        return self._new_temp()
    
    def _generate_binary_expression(self, node):
        """Genera código para expresiones binarias"""
        if len(node.children) >= 2:
            left = self._generate_expression(node.children[0])
            right = self._generate_expression(node.children[1])
            operator = node.value
            
            result_temp = self._new_temp()
            
            self.quadruples.append({
                'type': 'binary_op',
                'target': result_temp,
                'operator': operator,
                'left': left,
                'right': right
            })
            
            return result_temp
        return self._new_temp()
    
    def _generate_unary_expression(self, node):
        """Genera código para operaciones unarias"""
        if node.children:
            operand = self._generate_expression(node.children[0])
            operator = node.value
            
            result_temp = self._new_temp()
            
            self.quadruples.append({
                'type': 'unary_op',
                'target': result_temp,
                'operator': operator,
                'operand': operand
            })
            
            return result_temp
        return self._new_temp()
    
    def _generate_if_statement(self, node):
        """Genera código para if simple"""
        if len(node.children) >= 2:
            condition = self._generate_expression(node.children[0])
            false_label = self._new_label()
            end_label = self._new_label()
            
            # Salto condicional si condición es falsa
            self.quadruples.append({
                'type': 'if_false_goto',
                'condition': condition,
                'label': false_label
            })
            
            # Código del then
            self._generate_declarations(node.children[1])
            
            # Salto al final
            self.quadruples.append({
                'type': 'goto',
                'label': end_label
            })
            
            # Etiqueta false
            self.quadruples.append({
                'type': 'label',
                'name': false_label
            })
            
            # Etiqueta end
            self.quadruples.append({
                'type': 'label',
                'name': end_label
            })
    
    def _generate_if_else_statement(self, node):
        """Genera código para if-else"""
        if len(node.children) >= 3:
            condition = self._generate_expression(node.children[0])
            false_label = self._new_label()
            end_label = self._new_label()
            
            # Salto condicional si condición es falsa
            self.quadruples.append({
                'type': 'if_false_goto',
                'condition': condition,
                'label': false_label
            })
            
            # Código del then
            self._generate_declarations(node.children[1])
            
            # Salto al final (evitar ejecutar el else)
            self.quadruples.append({
                'type': 'goto',
                'label': end_label
            })
            
            # Etiqueta false (inicio del else)
            self.quadruples.append({
                'type': 'label',
                'name': false_label
            })
            
            # Código del else
            self._generate_declarations(node.children[2])
            
            # Etiqueta end
            self.quadruples.append({
                'type': 'label',
                'name': end_label
            })
    
    def _generate_while_statement(self, node):
        """Genera código para while"""
        if len(node.children) >= 2:
            start_label = self._new_label()
            condition_label = self._new_label()
            end_label = self._new_label()
            
            # Ir a evaluación de condición
            self.quadruples.append({
                'type': 'goto',
                'label': condition_label
            })
            
            # Etiqueta de inicio del cuerpo
            self.quadruples.append({
                'type': 'label',
                'name': start_label
            })
            
            # Código del cuerpo
            self._generate_declarations(node.children[1])
            
            # Etiqueta de condición
            self.quadruples.append({
                'type': 'label',
                'name': condition_label
            })
            
            # Evaluar condición
            condition = self._generate_expression(node.children[0])
            
            # Salto condicional si condición es verdadera
            self.quadruples.append({
                'type': 'if_true_goto',
                'condition': condition,
                'label': start_label
            })
            
            # Etiqueta end
            self.quadruples.append({
                'type': 'label',
                'name': end_label
            })
    
    def _generate_do_while_statement(self, node):
        """Genera código para do-while"""
        if len(node.children) >= 2:
            start_label = self._new_label()
            condition_label = self._new_label()
            
            # Etiqueta de inicio
            self.quadruples.append({
                'type': 'label',
                'name': start_label
            })
            
            # Código del cuerpo
            self._generate_declarations(node.children[0])
            
            # Etiqueta de condición
            self.quadruples.append({
                'type': 'label',
                'name': condition_label
            })
            
            # Evaluar condición
            condition = self._generate_expression(node.children[1])
            
            # Salto condicional si condición es verdadera
            self.quadruples.append({
                'type': 'if_true_goto',
                'condition': condition,
                'label': start_label
            })
    
    def _generate_input(self, node):
        """Genera código para entrada"""
        if node.children:
            var_name = node.children[0].value
            self.quadruples.append({
                'type': 'input',
                'target': var_name
            })
    
    def _generate_output(self, node):
        """Genera código para salida"""
        if node.children:
            expr_result = self._generate_expression(node.children[0])
            self.quadruples.append({
                'type': 'output',
                'value': expr_result
            })
    
    def get_quadruples_string(self):
        """Convierte los cuádruplos a string legible"""
        result = "=== CÓDIGO INTERMEDIO (CUÁDRUPLOS) ===\n"
        for i, quad in enumerate(self.quadruples):
            result += f"{i:3d}. "
            if quad['type'] == 'assign':
                result += f"{quad['target']} = {quad['source']}"
            elif quad['type'] == 'binary_op':
                result += f"{quad['target']} = {quad['left']} {quad['operator']} {quad['right']}"
            elif quad['type'] == 'unary_op':
                result += f"{quad['target']} = {quad['operator']}{quad['operand']}"
            elif quad['type'] == 'if_false_goto':
                result += f"IF_FALSE {quad['condition']} GOTO {quad['label']}"
            elif quad['type'] == 'if_true_goto':
                result += f"IF_TRUE {quad['condition']} GOTO {quad['label']}"
            elif quad['type'] == 'goto':
                result += f"GOTO {quad['label']}"
            elif quad['type'] == 'label':
                result += f"{quad['name']}:"
            elif quad['type'] == 'input':
                result += f"INPUT {quad['target']}"
            elif quad['type'] == 'output':
                result += f"OUTPUT {quad['value']}"
            result += "\n"
        return result

def generate_intermediate_code(ast, symbol_table):
    """Función principal para generar código intermedio"""
    generator = IntermediateCodeGenerator()
    quadruples = generator.generate(ast, symbol_table)
    return quadruples, generator.get_quadruples_string()