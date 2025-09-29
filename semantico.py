# semantico.py - Versión completamente corregida
from sintactico import ASTNode

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.current_scope = 0

    def enter_scope(self):
        self.scopes.append({})
        self.current_scope += 1

    def exit_scope(self):
        if self.current_scope > 0:
            self.scopes.pop()
            self.current_scope -= 1

    def add_symbol(self, name, symbol_type, value=None, line=None):
        if name in self.scopes[self.current_scope]:
            return False
        self.scopes[self.current_scope][name] = {
            'type': symbol_type,
            'value': value,
            'line': line
        }
        return True

    def lookup(self, name):
        for i in range(self.current_scope, -1, -1):
            if name in self.scopes[i]:
                return self.scopes[i][name]
        return None

    def get_all_symbols(self):
        symbols = []
        for i, scope in enumerate(self.scopes):
            for name, info in scope.items():
                symbols.append({
                    'nombre': name,
                    'tipo': info['type'],
                    'valor': info['value'],
                    'alcance': 'global' if i == 0 else f'local_{i}',
                    'linea': info['line']
                })
        return symbols

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.semantic_tree = None

    def analyze(self, ast):
        self.errors = []
        if ast:
            self._traverse_ast(ast)
            self.semantic_tree = self._build_semantic_tree(ast)
        return self.errors

    def get_symbol_table_data(self):
        return self.symbol_table.get_all_symbols()

    def get_semantic_tree(self):
        return self.semantic_tree

    def _build_semantic_tree(self, node):
        if not isinstance(node, ASTNode):
            return None

        semantic_node = {
            'type': node.type,
            'value': getattr(node, 'value', None),
            'line': getattr(node, 'lineno', None),
            'children': []
        }

        # Añadir información semántica específica
        if node.type == 'identificador':
            symbol = self.symbol_table.lookup(node.value)
            if symbol:
                semantic_node['symbol_type'] = symbol['type']
        
        elif node.type == 'asignacion':
            if len(node.children) >= 2:
                var_type = self._get_symbol_type(node.children[0])
                expr_type = self._get_expression_type(node.children[1])
                semantic_node['assignment_types'] = f"{var_type} = {expr_type}"

        elif node.type == 'expresion_binaria':
            if len(node.children) >= 2:
                left_type = self._get_expression_type(node.children[0])
                right_type = self._get_expression_type(node.children[1])
                semantic_node['operation_types'] = f"{left_type} {node.value} {right_type}"

        # Procesar hijos
        if hasattr(node, 'children'):
            for child in node.children:
                child_node = self._build_semantic_tree(child)
                if child_node:
                    semantic_node['children'].append(child_node)

        return semantic_node

    def _traverse_ast(self, node):
        if not isinstance(node, ASTNode):
            return

        try:
            if node.type == 'programa':
                self._process_program(node)
            elif node.type == 'declaracion_variable':
                self._process_declaration(node)
            elif node.type == 'asignacion':
                self._process_assignment(node)
            elif node.type == 'expresion_binaria':
                self._process_binary_expression(node)
            
            # ESTRUCTURAS DE CONTROL
            elif node.type == 'if_then':
                self._process_if_then(node)
            elif node.type == 'if_then_else':
                self._process_if_then_else(node)
            elif node.type == 'while':
                self._process_while(node)
            elif node.type == 'do_until':
                self._process_do_until(node)
            elif node.type == 'for':
                self._process_for(node)
            elif node.type == 'switch':
                self._process_switch(node)

            # Procesar hijos
            if hasattr(node, 'children'):
                for child in node.children:
                    self._traverse_ast(child)
                    
        except Exception as e:
            self.errors.append(f"Error durante análisis: {str(e)}")
                    
    def _process_if_then(self, node):
        """Procesa if-then"""
        if len(node.children) >= 2:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del if debe ser booleana")

            # Entrar en ámbito para el bloque then
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[1])  # Bloque then
            self.symbol_table.exit_scope()

    def _process_if_then_else(self, node):
        """Procesa if-then-else"""
        if len(node.children) >= 3:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del if debe ser booleana")

            # Bloque then
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[1])
            self.symbol_table.exit_scope()

            # Bloque else
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[2])
            self.symbol_table.exit_scope()

    def _process_while(self, node):
        """Procesa while"""
        if len(node.children) >= 2:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del while debe ser booleana")

            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[1])  # Cuerpo del while
            self.symbol_table.exit_scope()

    def _process_do_until(self, node):
        """Procesa do-until"""
        if len(node.children) >= 2:
            # Primero ejecutar el cuerpo
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[0])  # Cuerpo do
            self.symbol_table.exit_scope()

            # Luego verificar la condición
            cond_type = self._get_expression_type(node.children[1])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del until debe ser booleana")

    def _process_for(self, node):
        """Procesa for loop"""
        if len(node.children) >= 4:
            # Inicialización
            self._traverse_ast(node.children[0])
            
            # Condición
            cond_type = self._get_expression_type(node.children[1])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del for debe ser booleana")
            
            # Incremento
            self._traverse_ast(node.children[2])
            
            # Cuerpo
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[3])
            self.symbol_table.exit_scope()

    def _process_switch(self, node):
        """Procesa switch"""
        if len(node.children) >= 2:
            expr_type = self._get_expression_type(node.children[0])
            if expr_type not in ['int', 'bool'] and expr_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La expresión del switch debe ser entera o booleana")

            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[1])  # Casos
            self.symbol_table.exit_scope()
        

    def _process_program(self, node):
        pass

    def _process_declaration(self, node):
        if len(node.children) >= 2:
            tipo_node = node.children[0]
            ids_node = node.children[1]

            var_type = tipo_node.value if hasattr(tipo_node, 'value') else 'unknown'

            # Extraer identificadores
            identifiers = []
            if ids_node.type == 'lista_ids':
                for child in ids_node.children:
                    if child.type == 'identificador' and hasattr(child, 'value'):
                        identifiers.append(child.value)
            elif ids_node.type == 'identificador' and hasattr(ids_node, 'value'):
                identifiers.append(ids_node.value)

            for var_name in identifiers:
                if not self.symbol_table.add_symbol(var_name, var_type, line=node.lineno):
                    self.errors.append(f"Error semántico (línea {node.lineno}): Variable '{var_name}' ya declarada")

    def _process_assignment(self, node):
        if len(node.children) >= 2:
            var_node = node.children[0]
            expr_node = node.children[1]

            if hasattr(var_node, 'value'):
                var_name = var_node.value
                symbol = self.symbol_table.lookup(var_name)
                
                if symbol is None:
                    self.errors.append(f"Error semántico (línea {node.lineno}): Variable '{var_name}' no declarada")
                    return

                var_type = symbol['type']
                expr_type = self._get_expression_type(expr_node)

                if expr_type is None:
                    self.errors.append(f"Error semántico (línea {node.lineno}): No se puede determinar el tipo de la expresión")
                    return

                if not self._are_types_compatible(var_type, expr_type):
                    self.errors.append(f"Error semántico (línea {node.lineno}): Tipo incompatible en asignación. Se esperaba '{var_type}' pero se encontró '{expr_type}'")

    def _process_binary_expression(self, node):
        if len(node.children) >= 2 and hasattr(node, 'value'):
            left_type = self._get_expression_type(node.children[0])
            right_type = self._get_expression_type(node.children[1])
            operator = node.value

            if left_type and right_type:
                if operator in ['+', '-', '*', '/', '%', '^']:
                    if left_type not in ['int', 'float'] or right_type not in ['int', 'float']:
                        self.errors.append(f"Error semántico (línea {node.lineno}): Operación '{operator}' no válida entre '{left_type}' y '{right_type}'")
                elif operator in ['&&', '||']:
                    if left_type != 'bool' or right_type != 'bool':
                        self.errors.append(f"Error semántico (línea {node.lineno}): Operación lógica '{operator}' requiere operandos booleanos")

    def _process_conditional(self, node):
        if len(node.children) >= 1:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición debe ser booleana")

            self.symbol_table.enter_scope()
            for i in range(1, len(node.children)):
                self._traverse_ast(node.children[i])
            self.symbol_table.exit_scope()

    def _process_while(self, node):
        if len(node.children) >= 2:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del while debe ser booleana")

            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[1])
            self.symbol_table.exit_scope()

    def _process_do_until(self, node):
        if len(node.children) >= 2:
            self.symbol_table.enter_scope()
            self._traverse_ast(node.children[0])
            self.symbol_table.exit_scope()

            cond_type = self._get_expression_type(node.children[1])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del until debe ser booleana")

    def _process_input(self, node):
        for child in node.children:
            if hasattr(child, 'value'):
                var_name = child.value
                if self.symbol_table.lookup(var_name) is None:
                    self.errors.append(f"Error semántico (línea {node.lineno}): Variable '{var_name}' no declarada")

    def _process_output(self, node):
        for child in node.children:
            expr_type = self._get_expression_type(child)
            if expr_type is None:
                self.errors.append(f"Error semántico (línea {node.lineno}): Expresión inválida en salida")

    def _get_symbol_type(self, node):
        """Obtiene el tipo de un símbolo (variable)"""
        if node.type == 'identificador' and hasattr(node, 'value'):
            symbol = self.symbol_table.lookup(node.value)
            return symbol['type'] if symbol else None
        return None

    def _get_expression_type(self, node):
        """Determina el tipo de una expresión - VERSIÓN ROBUSTA"""
        if not isinstance(node, ASTNode):
            return None

        try:
            # Caso 1: Identificador
            if node.type == 'identificador':
                return self._get_symbol_type(node)

            # Caso 2: Número literal
            elif node.type == 'numero':
                if hasattr(node, 'value'):
                    value_str = str(node.value)
                    return 'float' if '.' in value_str else 'int'
                return 'int'

            # Caso 3: Expresión binaria
            elif node.type == 'expresion_binaria' and hasattr(node, 'value'):
                left_type = self._get_expression_type(node.children[0])
                right_type = self._get_expression_type(node.children[1])
                operator = node.value

                if not left_type or not right_type:
                    return None

                # Operaciones aritméticas
                if operator in ['+', '-', '*', '/', '%', '^']:
                    if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                        return 'float' if 'float' in [left_type, right_type] else 'int'

                # Operaciones lógicas
                elif operator in ['&&', '||']:
                    if left_type == 'bool' and right_type == 'bool':
                        return 'bool'

                # Operaciones relacionales
                elif operator in ['<', '<=', '>', '>=', '==', '!=']:
                    if (left_type in ['int', 'float'] and right_type in ['int', 'float']) or \
                       (left_type == right_type):
                        return 'bool'

            # Caso 4: Expresión entre paréntesis
            elif node.type == 'expresion':
                return self._get_expression_type(node.children[0]) if node.children else None

            # Caso 5: Valor booleano
            elif node.type in ['true', 'false']:
                return 'bool'

        except Exception as e:
            # En caso de error, retornar None en lugar de fallar
            return None

        return None

    def _are_types_compatible(self, target_type, source_type):
        if target_type == source_type:
            return True
        if target_type == 'float' and source_type == 'int':
            return True
        return False

def test_semantics(input_text):
    from sintactico import parse_code

    result = parse_code(input_text)
    
    if result['success'] and result['ast']:
        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(result['ast'])
        
        return {
            'errors': errors,
            'symbol_table': analyzer.get_symbol_table_data(),
            'semantic_tree': analyzer.get_semantic_tree(),
            'success': len(errors) == 0
        }
    else:
        errors = ["No se puede realizar análisis semántico debido a errores sintácticos"]
        errors.extend([f"Error sintáctico: {e.get('message', str(e))}" for e in result.get('errors', [])])
        
        return {
            'errors': errors,
            'symbol_table': [],
            'semantic_tree': None,
            'success': False
        }

# Prueba específica
if __name__ == "__main__":
    test_code = """
    main{
        int a;
        int b;
        int c;
        a = 5;
        b = 4;
        c = a + b;
        float x;
        float y;
        float z;
        x = 5.5;
        y = 3.2;
        z = x * y;
    }
    """
    
    result = test_semantics(test_code)
    print("=== RESULTADOS DEL ANÁLISIS SEMÁNTICO ===")
    
    if result['success']:
        print("✓ Análisis exitoso")
        print("\nTabla de símbolos:")
        for symbol in result['symbol_table']:
            print(f"  {symbol['nombre']}: {symbol['tipo']} (línea {symbol['linea']})")
    else:
        print("✗ Errores encontrados:")
        for error in result['errors']:
            print(f"  {error}")