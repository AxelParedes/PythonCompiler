from lexico import tokens, lexer

class ASTNode:
    def __init__(self, type, children=None, value=None, lineno=None, lexpos=None):
        self.type = type
        self.children = children if children is not None else []
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos

    def __repr__(self):
        return f"{self.type}: {self.value}" if self.value else self.type

def test_declarations():
    """Función para probar declaraciones sin necesidad del IDE"""
    test_cases = [
        "int x, y;",
        "int x, y, z;", 
        "int x, z = 123;"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== TEST CASE {i}: {test_case} ===")
        try:
            # Usar parser alternativo directamente
            result = parse_simple_declaration(test_case)
            print("Parseado exitosamente")
            print_ast(result, "Arbol generado:")
                
        except Exception as e:
            print(f"Error: {e}")

def parse_simple_declaration(input_text):
    """Parser alternativo solo para declaraciones simples"""
    print("Analizando declaracion...")
    
    # Limpiar y tokenizar manualmente
    input_text = input_text.strip().rstrip(';')
    if not input_text:
        return None
    
    parts = input_text.split()
    if len(parts) < 2:
        return None
    
    tipo = parts[0]
    variables_str = ' '.join(parts[1:])
    variables = [var.strip() for var in variables_str.split(',') if var.strip()]
    
    # Crear nodos AST manualmente
    tipo_node = ASTNode('tipo', value=tipo)
    
    # Asignar tipo semántico
    if tipo == 'int':
        tipo_node.dtype = 'integer'
    elif tipo == 'float':
        tipo_node.dtype = 'real'
    
    ids_nodes = []
    
    for var in variables:
        if '=' in var:
            # Variable con asignación
            var_parts = var.split('=', 1)
            var_name = var_parts[0].strip()
            var_value = var_parts[1].strip()
            
            id_node = ASTNode('identificador', value=var_name)
            id_node.dtype = tipo_node.dtype  # Propagar tipo semántico
            
            value_node = ASTNode('valor', value=var_value)
            assign_node = ASTNode('asignacion', children=[id_node, value_node])
            ids_nodes.append(assign_node)
        else:
            # Variable simple
            id_node = ASTNode('identificador', value=var.strip())
            id_node.dtype = tipo_node.dtype  # Propagar tipo semántico
            ids_nodes.append(id_node)
    
    decl_node = ASTNode('declaracion', children=[tipo_node] + ids_nodes)
    return decl_node

def print_ast(node, title="", level=0):
    """Imprime el AST en consola"""
    if level == 0:
        print(f"\n{title}")
        print("=" * 50)
    
    indent = "  " * level
    node_info = f"{indent}{node.type}"
    
    if hasattr(node, 'value') and node.value:
        node_info += f": {node.value}"
    
    if hasattr(node, 'dtype'):
        node_info += f" [tipo: {node.dtype}]"
    
    print(node_info)
    
    if hasattr(node, 'children'):
        for child in node.children:
            print_ast(child, level=level + 1)

# Ejecutar pruebas si se corre directamente
if __name__ == "__main__":
    test_declarations()