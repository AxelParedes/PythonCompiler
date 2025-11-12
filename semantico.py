# semantico.py - Versión completamente corregida
from sintactico import ASTNode

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.current_scope = 0
        self.all_symbols = []

    def enter_scope(self):
        self.scopes.append({})
        self.current_scope += 1
        print(f"DEBUG: Entrando a ámbito {self.current_scope}")

    def exit_scope(self):
        """Sale del ámbito actual - PERO MANTIENE LOS SÍMBOLOS PARA ANÁLISIS"""
        if self.current_scope > 0:
            print(f"DEBUG: Saliendo de ámbito {self.current_scope}")
            
            # ANTES de eliminar el scope, guardar los símbolos locales
            current_scope_symbols = self.scopes[self.current_scope]
            for name, info in current_scope_symbols.items():
                self.all_symbols.append({
                    'nombre': name,
                    'tipo': info['type'],
                    'valor': info.get('value'),
                    'alcance': f'{self.current_scope}',
                    'linea': info.get('line', 'N/A')
                })
                print(f"DEBUG: Guardando símbolo local '{name}' del ámbito {self.current_scope}")
            
            self.scopes.pop()
            self.current_scope -= 1
        else:
            print(f"DEBUG: ERROR - Intentando salir del ámbito global")

    def add_symbol(self, name, symbol_type, value=None, line=None):
        """Agrega un símbolo al ámbito actual"""
        if name in self.scopes[self.current_scope]:
            return False
        
        ambito = "GLOBAL" if self.current_scope == 0 else f"LOCAL({self.current_scope})"
        print(f"DEBUG: Agregando símbolo '{name}' tipo '{symbol_type}' en ámbito {ambito}")

        self.scopes[self.current_scope][name] = {
            'type': symbol_type,
            'value': value,
            'line': line
        }
        
        # Si es global, guardarlo inmediatamente en all_symbols
        if self.current_scope == 0:
            self.all_symbols.append({
                'nombre': name,
                'tipo': symbol_type,
                'valor': value,
                'alcance': 'global',
                'linea': line
            })
        
        return True
        
        

    def lookup(self, name):
        """Busca un símbolo desde el ámbito actual hacia afuera"""
        for i in range(self.current_scope, -1, -1):
            if name in self.scopes[i]:
                return self.scopes[i][name]
        return None
    
    def p_expresion_string_literal(p):
        'expresion : STRING_LITERAL'
        p[0] = ASTNode('string_literal', value=p[1], lineno=p.lineno(1))
        
    def get_all_symbols(self):
        """Obtiene todos los símbolos - INCLUYENDO LOCALES"""
        print(f"DEBUG: Obteniendo {len(self.all_symbols)} símbolos totales")
        
        # También agregar símbolos globales actuales por si acaso
        for name, info in self.scopes[0].items():
            exists = any(s['nombre'] == name for s in self.all_symbols)
            if not exists:
                self.all_symbols.append({
                    'nombre': name,
                    'tipo': info['type'],
                    'valor': info.get('value'),
                    'alcance': 'global',
                    'linea': info.get('line', 'N/A')
                })
        
        # DEBUG
        for symbol in self.all_symbols:
            print(f"DEBUG SYMBOL: {symbol['nombre']} -> {symbol['alcance']}")
            
        return self.all_symbols

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.semantic_tree = None
        self.current_function_return_type = None
        self.current_function_name = None
        # Nuevo: Contadores para estadísticas de ámbitos
        self.global_vars = 0
        self.local_vars = 0

    def analyze(self, ast):
        self.errors = []
        self.global_vars = 0
        self.local_vars = 0
        if ast:
            self._traverse_ast(ast)
            self.semantic_tree = self._build_semantic_tree(ast)
        return self.errors

    def get_symbol_table_data(self):
        symbols = self.symbol_table.get_all_symbols()
        # Agregar información de ámbito a cada símbolo
        for symbol in symbols:
            if symbol['alcance'] == "global":
                symbol['es_global'] = True
            else:
                symbol['es_global'] = False
        return symbols
    
    def get_scope_stats(self):
        """Retorna estadísticas de ámbitos"""
        return {
            'globales': self.global_vars,
            'locales': self.local_vars,
            'total': self.global_vars + self.local_vars
        }

    def get_semantic_tree(self):
        return self.semantic_tree
    
    # Agregar tipo string a la tabla de símbolos
    def agregar_tipo_string(self):
        self.tipos['string'] = {'operaciones': {
            '+': 'string',  # concatenación
            '==': 'bool',
            '!=': 'bool'
        }}

    def _process_function_definition(self, node):
        """Procesa definición de función"""
        if hasattr(node, 'func_name'):
            func_name = node.func_name
            func_type = node.value
            
            # Agregar función a la tabla de símbolos
            if not self.symbol_table.add_symbol(func_name, 'function', value=func_type, line=node.lineno):
                self.errors.append(f"Error semántico (línea {node.lineno}): Función '{func_name}' ya declarada")
                return
            
            # Entrar en ámbito de función
            self.symbol_table.enter_scope()
            
            # Procesar parámetros
            if node.children and len(node.children) > 0:
                params_node = node.children[0]
                self._process_parameters(params_node, func_name)
            
            # Procesar cuerpo de función
            if node.children and len(node.children) > 1:
                body_node = node.children[1]
                self._traverse_ast(body_node)
            
            # Salir del ámbito de función
            self.symbol_table.exit_scope()

    def _process_parameters(self, params_node, func_name):
        """Procesa parámetros de función"""
        if not params_node or not params_node.children:
            return
        
        for param in params_node.children:
            if param.type == 'parameter' and len(param.children) >= 2:
                param_type_node = param.children[0]
                param_name_node = param.children[1]
                
                if hasattr(param_type_node, 'value') and hasattr(param_name_node, 'value'):
                    param_type = param_type_node.value
                    param_name = param_name_node.value
                    
                    # Agregar parámetro a la tabla de símbolos
                    if not self.symbol_table.add_symbol(param_name, param_type, line=param.lineno):
                        self.errors.append(f"Error semántico (línea {param.lineno}): Parámetro '{param_name}' duplicado en función '{func_name}'")

    def _process_function_declaration(self, node):
        """Procesa declaración/definición de función - VERSIÓN CORREGIDA"""
        if hasattr(node, 'func_name'):
            func_name = node.func_name
            func_type = node.value  # Tipo de retorno de la función
            
            # Guardar contexto actual
            old_function_type = self.current_function_return_type
            old_function_name = self.current_function_name
            
            # Establecer contexto de función actual
            self.current_function_return_type = func_type
            self.current_function_name = func_name
            
            # Agregar función a tabla de símbolos global
            if not self.symbol_table.add_symbol(func_name, 'function', value=func_type, line=node.lineno):
                self.errors.append(f"Error semántico (línea {node.lineno}): Función '{func_name}' ya declarada")
                # Restaurar contexto
                self.current_function_return_type = old_function_type
                self.current_function_name = old_function_name
                return
            
            # Entrar en ámbito de función
            self.symbol_table.enter_scope()
            
            # Procesar parámetros - BUSCAR CORRECTAMENTE EL NODO DE PARÁMETROS
            params_node = None
            for child in node.children:
                if child and hasattr(child, 'type') and child.type == 'parametros':
                    params_node = child
                    break
            
            if params_node and params_node.children:
                for param in params_node.children:
                    if param.type == 'parameter' and len(param.children) >= 2:
                        param_type_node = param.children[0]
                        param_name_node = param.children[1]
                        
                        if hasattr(param_type_node, 'value') and hasattr(param_name_node, 'value'):
                            param_type = param_type_node.value
                            param_name = param_name_node.value
                            
                            # Agregar parámetro al ámbito de la función
                            if not self.symbol_table.add_symbol(param_name, param_type, line=param.lineno):
                                self.errors.append(f"Error semántico (línea {param.lineno}): Parámetro '{param_name}' duplicado en función '{func_name}'")
            
            # Procesar cuerpo de función
            body_node = None
            for child in node.children:
                if child and hasattr(child, 'type') and child.type in ['lista_declaraciones', 'bloque']:
                    body_node = child
                    break
            
            if body_node:
                self._traverse_ast(body_node)
            
            # Verificar que la función tenga return si no es void
            if func_type != 'void' and self.current_function_return_type is None:
                self.errors.append(f"Error semántico (línea {node.lineno}): Función '{func_name}' debe retornar un valor de tipo '{func_type}'")
            
            # Salir del ámbito de función
            self.symbol_table.exit_scope()
            
            # Restaurar contexto anterior
            self.current_function_return_type = old_function_type
            self.current_function_name = old_function_name

    def _process_function_call(self, node):
        """Procesa llamada a función - VERSIÓN MEJORADA"""
        if len(node.children) >= 2:
            func_name_node = node.children[0]
            args_node = node.children[1]
            
            if hasattr(func_name_node, 'value'):
                func_name = func_name_node.value
                func_symbol = self.symbol_table.lookup(func_name)
                
                if not func_symbol or func_symbol['type'] != 'function':
                    self.errors.append(f"Error semántico (línea {node.lineno}): Función '{func_name}' no declarada")
                    return None
                
                # Procesar argumentos
                expected_param_count = 0
                if args_node and args_node.children:
                    expected_param_count = len(args_node.children)
                    for i, arg in enumerate(args_node.children):
                        arg_type = self._get_expression_type(arg)
                        if not arg_type:
                            self.errors.append(f"Error semántico (línea {node.lineno}): No se puede determinar el tipo del argumento {i+1} en llamada a '{func_name}'")
                
                # Retornar el tipo de la función
                return func_symbol.get('value', 'int')  # Default a int si no hay tipo
        
        return None

    
    def _process_arguments(self, args_node, func_name, line):
        """Procesa argumentos de llamada a función"""
        if not args_node.children:
            return
        
        for i, arg in enumerate(args_node.children):
            arg_type = self._get_expression_type(arg)
            if not arg_type:
                self.errors.append(f"Error semántico (línea {line}): No se puede determinar el tipo del argumento {i+1} en llamada a '{func_name}'")

    def _process_return_statement(self, node):
        """Procesa sentencia return - VERSIÓN CORREGIDA (ÚNICA)"""
        if not self.current_function_name:
            self.errors.append(f"Error semántico (línea {node.lineno}): Return fuera de función")
            return None
            
        if node.children and len(node.children) > 0:
            expr_node = node.children[0]
            return_type = self._get_expression_type(expr_node)
            
            if not return_type:
                self.errors.append(f"Error semántico (línea {node.lineno}): No se puede determinar tipo de retorno")
                return None
                
            # Verificar compatibilidad con el tipo de retorno de la función
            if return_type != self.current_function_return_type:
                self.errors.append(f"Error semántico (línea {node.lineno}): Tipo de retorno '{return_type}' no coincide con el tipo de función '{self.current_function_return_type}'")
            
            return return_type
        else:
            # Return sin expresión - verificar si la función es void
            if self.current_function_return_type != 'void':
                self.errors.append(f"Error semántico (línea {node.lineno}): Función '{self.current_function_name}' debe retornar un valor de tipo '{self.current_function_return_type}'")
            return 'void'
    
    def _build_semantic_tree(self, node):
        if not isinstance(node, ASTNode):
            return None

        # Información básica del nodo
        semantic_node = {
            'type': node.type,
            'value': getattr(node, 'value', None),
            'line': getattr(node, 'lineno', None),
            'children': []
        }

        # Agregar información semántica específica solo para nodos importantes
        if node.type == 'identificador':
            symbol = self.symbol_table.lookup(node.value)
            if symbol:
                semantic_node['symbol_type'] = symbol['type']
        
        elif node.type == 'asignacion' and len(node.children) >= 2:
            var_type = self._get_symbol_type(node.children[0])
            expr_type = self._get_expression_type(node.children[1])
            if var_type and expr_type:
                semantic_node['assignment_types'] = f"{var_type} = {expr_type}"

        elif node.type == 'expresion_binaria' and len(node.children) >= 2:
            left_type = self._get_expression_type(node.children[0])
            right_type = self._get_expression_type(node.children[1])
            if left_type and right_type:
                semantic_node['operation_types'] = f"{left_type} {node.value} {right_type}"

        # Procesar hijos (solo los necesarios)
        if hasattr(node, 'children'):
            for child in node.children:
                # Filtrar nodos muy básicos que no aportan información
                if child and isinstance(child, ASTNode):
                    child_node = self._build_semantic_tree(child)
                    if child_node:
                        semantic_node['children'].append(child_node)

        return semantic_node

    def _traverse_ast(self, node):
        """Recorre el AST - VERSIÓN CON FIX INMEDIATO"""
        if not isinstance(node, ASTNode):
            return

        try:
            # EVITAR PROCESAR NODOS DUPLICADOS - FIX INMEDIATO
            if hasattr(node, '_processed'):
                return
            node._processed = True
            
            if node.type == 'programa':
                self._process_program(node)
            elif node.type == 'declaracion_variable':
                self._process_declaration(node)
            elif node.type == 'asignacion':
                self._process_assignment(node)
            elif node.type == 'expresion_binaria':
                self._process_binary_expression(node)
            
            # ESTRUCTURAS DE CONTROL
            elif node.type in ['if', 'if_then', 'if_else']:
                self._process_if_statement(node)
            elif node.type == 'while':
                self._process_while_statement(node)
            elif node.type == 'do_while':
                self._process_do_while_statement(node)

            # Procesar hijos recursivamente SOLO UNA VEZ
            if hasattr(node, 'children'):
                for child in node.children:
                    if isinstance(child, ASTNode) and not hasattr(child, '_processed'):
                        self._traverse_ast(child)
                        
        except Exception as e:
            self.errors.append(f"Error durante análisis: {str(e)}")
        
        
    def _process_if_statement(self, node):
        """Procesa if con ámbito local - VERSIÓN DEFINITIVA"""
        if len(node.children) >= 2:
            # Procesar condición
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del if debe ser booleana")

            # Procesar bloque THEN con NUEVO ÁMBITO
            self.symbol_table.enter_scope()
            if node.children[1]:  # Solo procesar si existe el bloque
                self._traverse_ast(node.children[1])
            self.symbol_table.exit_scope()

            # Procesar bloque ELSE si existe
            if len(node.children) >= 3 and node.children[2]:
                self.symbol_table.enter_scope()
                self._traverse_ast(node.children[2])
                self.symbol_table.exit_scope()

    def _process_while_statement(self, node):
        """Procesa while con ámbito local"""
        if len(node.children) >= 2:
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del while debe ser booleana")

            # Procesar cuerpo con NUEVO ÁMBITO
            self.symbol_table.enter_scope()
            self._process_statement(node.children[1])
            self.symbol_table.exit_scope()

    def _process_do_while_statement(self, node):
            """Procesa do-while con ámbito local"""
            if len(node.children) >= 2:
                # Procesar cuerpo primero con NUEVO ÁMBITO
                self.symbol_table.enter_scope()
                self._process_statement(node.children[0])
                self.symbol_table.exit_scope()

                # Luego procesar condición
                cond_type = self._get_expression_type(node.children[1])
                if cond_type != 'bool' and cond_type is not None:
                    self.errors.append(f"Error semántico (línea {node.lineno}): La condición del while debe ser booleana")


    def _process_statement(self, node):
        """Procesa una sentencia individual o bloque - VERSIÓN CORREGIDA"""
        if not node:
            return
            
        print(f"DEBUG: Procesando statement tipo: {node.type}")
        
        # Si es un bloque con llaves { ... }, procesar su contenido
        if node.type == 'lista_declaraciones':
            for child in node.children:
                self._traverse_ast(child)
        elif node.type == 'bloque':  # Si existe nodo bloque explícito
            for child in node.children:
                self._traverse_ast(child)
        else:
            # Es una sentencia individual
            self._traverse_ast(node)
                    
    def _process_if_then(self, node):
        """Procesa if-then con ámbito local"""
        if len(node.children) >= 2:
            # Procesar condición
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del if debe ser booleana")

            # Procesar bloque THEN con nuevo ámbito
            self.symbol_table.enter_scope()
            self._process_block(node.children[1])  # Procesar todo el bloque
            self.symbol_table.exit_scope()

    def _process_if_then_else(self, node):
        """Procesa if-then-else con ámbito local"""
        if len(node.children) >= 3:
            # Procesar condición
            cond_type = self._get_expression_type(node.children[0])
            if cond_type != 'bool' and cond_type is not None:
                self.errors.append(f"Error semántico (línea {node.lineno}): La condición del if debe ser booleana")

            # Procesar bloque THEN con nuevo ámbito
            self.symbol_table.enter_scope()
            self._process_block(node.children[1])
            self.symbol_table.exit_scope()

            # Procesar bloque ELSE con nuevo ámbito
            self.symbol_table.enter_scope()
            self._process_block(node.children[2])
            self.symbol_table.exit_scope()

    def _process_block(self, node):
        """Procesa un bloque de código (puede ser lista_declaraciones o un nodo de bloque)"""
        if not node:
            return
            
        # Si es una lista de declaraciones, procesar todos sus hijos
        if node.type == 'lista_declaraciones':
            for child in node.children:
                self._traverse_ast(child)
        # Si es un nodo de bloque con llaves, buscar la lista_declaraciones dentro
        elif hasattr(node, 'children'):
            for child in node.children:
                if child.type == 'lista_declaraciones':
                    for grandchild in child.children:
                        self._traverse_ast(grandchild)
                else:
                    self._traverse_ast(child)
        else:
            self._traverse_ast(node)
        
    # def _process_while(self, node):
    #     """Procesa while con ámbito local"""
    #     if len(node.children) >= 2:
    #         cond_type = self._get_expression_type(node.children[0])
    #         if cond_type != 'bool' and cond_type is not None:
    #             self.errors.append(f"Error semántico (línea {node.lineno}): La condición del while debe ser booleana")

    #         # Procesar cuerpo con nuevo ámbito
    #         self.symbol_table.enter_scope()
    #         self._process_block(node.children[1])
    #         self.symbol_table.exit_scope()

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
        """Procesa declaración de variables con contadores de ámbito"""
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

            # Usar la línea del nodo de declaración o del primer identificador
            line_number = node.lineno if hasattr(node, 'lineno') else 0
            if not line_number and ids_node.children:
                line_number = ids_node.children[0].lineno if hasattr(ids_node.children[0], 'lineno') else 0

            for var_name in identifiers:
                if not self.symbol_table.add_symbol(var_name, var_type, line=line_number):
                    self.errors.append(f"Error semántico (línea {line_number}): Variable '{var_name}' ya declarada")
                else:
                    # CONTAR VARIABLES POR ÁMBITO
                    if self.symbol_table.current_scope == 0:  # Ámbito global
                        self.global_vars += 1
                    else:  # Ámbito local
                        self.local_vars += 1

    def _process_assignment(self, node):
        """Procesa asignación con verificación de ámbito"""
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
                    return
                
    def _process_binary_expression(self, node):
        if len(node.children) >= 2 and hasattr(node, 'value'):
            left_type = self._get_expression_type(node.children[0])
            right_type = self._get_expression_type(node.children[1])
            operator = node.value

            if left_type and right_type:
                if operator in ['+', '-', '*', '/', '%', '^']:
                    # Operaciones aritméticas
                    if left_type not in ['int', 'float'] or right_type not in ['int', 'float']:
                        # Excepto concatenación de strings
                        if not (operator == '+' and left_type == 'string' and right_type == 'string'):
                            self.errors.append(f"Error semántico (línea {node.lineno}): Operación '{operator}' no válida entre '{left_type}' y '{right_type}'")
                elif operator in ['&&', '||']:
                    # Operaciones lógicas
                    if left_type != 'bool' or right_type != 'bool':
                        self.errors.append(f"Error semántico (línea {node.lineno}): Operación lógica '{operator}' requiere operandos booleanos")
                elif operator in ['==', '!=']:
                    # Comparaciones - permitir comparar tipos iguales (incluyendo strings)
                    if left_type != right_type:
                        self.errors.append(f"Error semántico (línea {node.lineno}): Comparación '{operator}' no válida entre '{left_type}' y '{right_type}'")
                            
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
        """Determina el tipo de una expresión - VERSIÓN CORREGIDA"""
        
        # CASO 1: Si es un string simple (viene directamente del parser como string literal)
        if isinstance(node, str):
            # Verificar si podría ser un identificador buscando en la tabla de símbolos
            symbol = self.symbol_table.lookup(node)
            if symbol:
                return symbol['type']  # Es una variable
            else:
                return 'string'  # Es un string literal
        
        if not isinstance(node, ASTNode):
            return None

        # CASO 2: Identificador (variable)
        if node.type == 'identificador':
            symbol = self.symbol_table.lookup(node.value)
            return symbol['type'] if symbol else None

        # CASO 3: String literal del parser
        elif node.type == 'string_literal':
            return 'string'

        # CASO 4: Número
        elif node.type == 'numero':
            if hasattr(node, 'value'):
                value_str = str(node.value)
                return 'float' if '.' in value_str else 'int'
            return 'int'

        # CASO 5: Booleano
        elif node.type == 'booleano':
            return 'bool'

        # CASO 6: Expresión binaria
        elif node.type == 'expresion_binaria' and hasattr(node, 'value'):
            left_type = self._get_expression_type(node.children[0])
            right_type = self._get_expression_type(node.children[1])
            operator = node.value

            if not left_type or not right_type:
                return None

            # Lógica de operaciones
            if operator == '+':
                # Concatenación de strings
                if left_type == 'string' and right_type == 'string':
                    return 'string'
                # Suma de números
                elif left_type in ['int', 'float'] and right_type in ['int', 'float']:
                    return 'float' if 'float' in [left_type, right_type] else 'int'
            elif operator in ['-', '*', '/', '%', '^']:
                if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                    return 'float' if 'float' in [left_type, right_type] else 'int'
            elif operator in ['&&', '||']:
                if left_type == 'bool' and right_type == 'bool':
                    return 'bool'
            elif operator in ['<', '<=', '>', '>=', '==', '!=']:
                if (left_type in ['int', 'float'] and right_type in ['int', 'float']) or \
                (left_type == right_type):  # Permite comparar strings
                    return 'bool'

        # CASO 7: Operación unaria (NOT)
        elif node.type == 'operacion_unaria' and hasattr(node, 'value'):
            if node.value == '!':
                child_type = self._get_expression_type(node.children[0])
                if child_type == 'bool':
                    return 'bool'
        # CASO 8: Llamada a función
        elif node.type == 'function_call':
            return self._process_function_call(node)

        return None

    def _are_types_compatible(self, target_type, source_type):
        if target_type == source_type:
            return True
        if target_type == 'float' and source_type == 'int':
            return True
        # Strings solo son compatibles con strings
        if target_type == 'string' and source_type == 'string':
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
def test_ambitos():
    """Prueba específica para el manejo de ámbitos"""
    test_code = """
    main{
        int global;
        global = 10;

        if (global > 5){
            int local;
            local = 20;
        }
    }
    """
    
    from sintactico import parse_code
    result = parse_code(test_code)
    
    if result['success'] and result['ast']:
        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(result['ast'])
        
        print("=== DIAGNÓSTICO DE ÁMBITOS ===")
        symbols = analyzer.get_symbol_table_data()
        for symbol in symbols:
            print(f"SYMBOL: {symbol['nombre']} -> ámbito: {symbol['alcance']}")
        
        return {
            'errors': errors,
            'symbol_table': symbols,
            'success': len(errors) == 0
        }

if __name__ == "__main__":
    # Ejecutar prueba de diagnóstico
    test_ambitos()