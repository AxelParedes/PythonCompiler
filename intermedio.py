# intermedio.py - VERSIÓN CORREGIDA QUE PROCESA EL AST REAL

class IntermediateCodeGenerator:
    def __init__(self):
        self.quadruples = []
        self.symbol_table = {}
        
    def generate(self, ast, symbol_table):
        """Genera código intermedio procesando el AST real"""
        self.quadruples = []
        self.symbol_table = symbol_table
        
        print("GENERANDO CÓDIGO INTERMEDIO DESDE AST REAL")
        
        # Procesar el AST real en lugar de usar datos fijos
        self._process_node(ast)
        
        print(f"Generados {len(self.quadruples)} cuádruplos desde AST:")
        for i, quad in enumerate(self.quadruples):
            print(f"  {i}: {quad}")
        
        return self.quadruples
    
    def _process_node(self, node):
        """Procesa recursivamente los nodos del AST"""
        if not node or not hasattr(node, 'type'):
            return
            
        node_type = node.type
        print(f"DEBUG INTERMEDIO: Procesando nodo {node_type}")
        
        if node_type == 'programa':
            self._process_program(node)
        elif node_type == 'sentencia':
            self._process_statement(node)
        elif node_type == 'lista_sentencias':
            self._process_statement_list(node)
        elif node_type == 'asignacion':
            self._process_assignment(node)
        elif node_type == 'output':
            self._process_output(node)
        elif node_type == 'input' or node_type == 'input_list':
            self._process_input(node)
        elif node_type == 'expresion_binaria':
            return self._process_binary_expression(node)
        elif node_type == 'identificador':
            return node.value
        elif node_type == 'numero':
            return node.value
        
        # Procesar hijos recursivamente
        if hasattr(node, 'children'):
            for child in node.children:
                self._process_node(child)
    
    def _process_program(self, node):
        """Procesa el nodo programa"""
        print("DEBUG: Procesando programa")
        if hasattr(node, 'children'):
            for child in node.children:
                self._process_node(child)
    
    def _process_statement_list(self, node):
        """Procesa lista de sentencias"""
        print("DEBUG: Procesando lista de sentencias")
        if hasattr(node, 'children'):
            for child in node.children:
                self._process_node(child)
    
    def _process_statement(self, node):
        """Procesa una sentencia individual"""
        if not node or not hasattr(node, 'children') or not node.children:
            return
            
        # El primer hijo contiene el tipo real de sentencia
        statement_node = node.children[0]
        self._process_node(statement_node)
    
    def _process_assignment(self, node):
        """Procesa una asignación: variable = expresión"""
        print("DEBUG: Procesando asignación")
        if hasattr(node, 'children') and len(node.children) >= 2:
            target = node.children[0]
            source = node.children[1]
            
            if hasattr(target, 'value'):
                var_name = target.value
                # Procesar la expresión del lado derecho
                source_value = self._process_expression(source)
                
                self.quadruples.append({
                    'type': 'assign',
                    'target': var_name,
                    'source': source_value
                })
                print(f"DEBUG: Asignación {var_name} = {source_value}")
    
    def _process_expression(self, node):
        """Procesa una expresión y retorna su valor"""
        if not node:
            return None
            
        if node.type == 'identificador':
            return node.value
        elif node.type == 'numero':
            return node.value
        elif node.type == 'expresion_binaria':
            return self._process_binary_expression(node)
        
        return None
    
    def _process_binary_expression(self, node):
        """Procesa una expresión binaria y genera cuádruplo"""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return None
            
        left = node.children[0]
        right = node.children[1]
        operator = getattr(node, 'value', '+')
        
        left_val = self._process_expression(left)
        right_val = self._process_expression(right)
        
        # Crear un temporal para el resultado
        temp_var = f"temp_{len(self.quadruples)}"
        
        self.quadruples.append({
            'type': 'binary_op',
            'target': temp_var,
            'operator': operator,
            'left': left_val,
            'right': right_val
        })
        
        print(f"DEBUG: Operación binaria {temp_var} = {left_val} {operator} {right_val}")
        return temp_var
    
    def _process_output(self, node):
        """Procesa sentencia de output: cout << valor"""
        print("DEBUG: Procesando output")
        if hasattr(node, 'children'):
            for child in node.children:
                if hasattr(child, 'type'):
                    if child.type == 'string_literal':
                        # Output de string literal
                        value = getattr(child, 'value', '')
                        self.quadruples.append({
                            'type': 'output',
                            'value': f'"{value}"'
                        })
                        print(f"DEBUG: Output string: '{value}'")
                    elif child.type == 'identificador':
                        # Output de variable
                        value = child.value
                        self.quadruples.append({
                            'type': 'output', 
                            'value': value
                        })
                        print(f"DEBUG: Output variable: {value}")
    
    def _process_input(self, node):
        """Procesa sentencia de input: cin >> variable"""
        print(f"DEBUG INTERMEDIO INPUT: Procesando input de tipo {node.type}")
        
        if node.type == 'input':
            # Input simple: cin >> variable;
            if node.children and hasattr(node.children[0], 'value'):
                var_name = node.children[0].value
                print(f"DEBUG INTERMEDIO INPUT: Variable: '{var_name}'")
                self.quadruples.append({
                    'type': 'input',
                    'target': var_name
                })
        elif node.type == 'input_list':
            # Múltiples inputs: cin >> var1 >> var2;
            for child in node.children:
                if hasattr(child, 'value'):
                    var_name = child.value
                    print(f"DEBUG INTERMEDIO INPUT: Variable múltiple: '{var_name}'")
                    self.quadruples.append({
                        'type': 'input', 
                        'target': var_name
                    })
    
    def get_quadruples_string(self):
        """Convierte los cuádruplos a string legible"""
        result = "=== CÓDIGO INTERMEDIO GENERADO DESDE AST ===\n"
        for i, quad in enumerate(self.quadruples):
            result += f"{i:3d}. "
            if quad['type'] == 'assign':
                result += f"{quad['target']} = {quad['source']}"
            elif quad['type'] == 'binary_op':
                result += f"{quad['target']} = {quad['left']} {quad['operator']} {quad['right']}"
            elif quad['type'] == 'output':
                result += f"OUTPUT {quad['value']}"
            elif quad['type'] == 'input':
                result += f"INPUT {quad['target']}"
            result += "\n"
        return result

def generate_intermediate_code(ast, symbol_table):
    """Función principal para generar código intermedio"""
    generator = IntermediateCodeGenerator()
    quadruples = generator.generate(ast, symbol_table)
    intermedio_str = generator.get_quadruples_string()
    return quadruples, intermedio_str