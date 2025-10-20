# sintactico.py - Sin importaciones circulares
import ply.yacc as yacc

# Importar solo tokens desde lexico
try:
    from lexico import tokens
except ImportError:
    # Definir tokens básicos por si falla la importación
    tokens = [
        'NUMBER', 'REAL', 'ID', 'ERROR', 'PLUS', 'MIN', 'TIMES', 'DIVIDE', 
        'MODULO', 'POWER', 'LT', 'LE', 'GT', 'GE', 'NE', 'EQ', 'EEQ', 
        'AND', 'OR', 'NOT', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 
        'COMMA', 'SEMICOLON', 'INCREMENT', 'DECREMENT', 'STRING'
    ]

# El lexer se inicializará después
lexer = None

class ASTNode:
    def __init__(self, type, children=None, value=None, lineno=None, lexpos=None):
        self.type = type
        self.children = children if children is not None else []
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos

    def __repr__(self):
        return f"{self.type}: {self.value}" if self.value else self.type

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EEQ', 'NE'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MIN'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'POWER', 'UMINUS'),
)

# GRAMÁTICA SIMPLIFICADA PERO FUNCIONAL

def p_programa(p):
    'programa : MAIN LBRACE lista_declaraciones RBRACE'
    p[0] = ASTNode('programa', children=[p[3]], lineno=p.lineno(1))
    
def p_function_declaration(p):
    '''declaracion : tipo ID LPAREN parameter_list RPAREN LBRACE lista_declaraciones RBRACE
                   | tipo ID LPAREN RPAREN LBRACE lista_declaraciones RBRACE'''
    if len(p) == 9:  # Con parámetros
        p[0] = ASTNode('function_declaration', children=[p[1], p[4], p[7]], value=p[1].value, lineno=p.lineno(2))
        p[0].func_name = p[2]
    else:  # Sin parámetros
        p[0] = ASTNode('function_declaration', children=[p[1], ASTNode('empty'), p[6]], value=p[1].value, lineno=p.lineno(2))
        p[0].func_name = p[2]
        
def p_parameter_list(p):
    '''parameter_list : parameter
                     | parameter_list COMMA parameter'''
    if len(p) == 2:
        p[0] = ASTNode('parameter_list', children=[p[1]], lineno=p.lineno(1))
    else:
        p[1].children.append(p[3])
        p[0] = p[1]
        
def p_parameter(p):
    'parameter : tipo ID'
    p[0] = ASTNode('parameter', children=[p[1], ASTNode('identificador', value=p[2])], lineno=p.lineno(1))

def p_expresion_function_call(p):
    'expresion : ID LPAREN argument_list RPAREN'
    p[0] = ASTNode('function_call', children=[ASTNode('identificador', value=p[1]), p[3]], lineno=p.lineno(1))


def p_function_call(p):
    'expresion : ID LPAREN argument_list RPAREN'
    func_name = ASTNode('identificador', value=p[1], lineno=p.lineno(1))
    p[0] = ASTNode('function_call', children=[func_name, p[3]], lineno=p.lineno(1))

def p_argument_list(p):
    '''argument_list : expresion
                    | argument_list COMMA expresion
                    | empty'''
    if len(p) == 2:
        if p[1] is None:  # empty
            p[0] = ASTNode('argument_list', children=[], lineno=p.lineno(1))
        else:
            p[0] = ASTNode('argument_list', children=[p[1]], lineno=p.lineno(1))
    else:
        p[1].children.append(p[3])
        p[0] = p[1]

def p_return_statement(p):
    'sentencia : RETURN expresion SEMICOLON'
    p[0] = ASTNode('return_statement', children=[p[2]], lineno=p.lineno(1))

def p_empty(p):
    'empty :'
    p[0] = ASTNode('empty', lineno=p.lineno(1))

def p_lista_declaraciones(p):
    '''lista_declaraciones : lista_declaraciones declaracion
                          | declaracion'''
    if len(p) == 3:
        p[0] = ASTNode('lista_declaraciones', children=[p[1], p[2]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('lista_declaraciones', children=[p[1]], lineno=p.lineno(1))
    
# def p_switch_statement(p):
#     '''switch_statement : SWITCH LPAREN expresion RPAREN LBRACE case_list RBRACE
#                        | SWITCH LPAREN expresion RPAREN LBRACE case_list default_case RBRACE'''
#     if len(p) == 8:
#         p[0] = ASTNode('switch', children=[p[3], p[6]], lineno=p.lineno(1))
#     else:
#         p[0] = ASTNode('switch', children=[p[3], p[6], p[7]], lineno=p.lineno(1))
        
def p_case_list(p):
    '''case_list : case_list case
                | case'''
    if len(p) == 3:
        p[0] = ASTNode('case_list', children=[p[1], p[2]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('case_list', children=[p[1]], lineno=p.lineno(1))
        
def p_casos(p):
    '''casos : casos caso
             | caso
             | casos DEFAULT COLON LBRACE lista_declaraciones RBRACE
             | DEFAULT COLON LBRACE lista_declaraciones RBRACE'''
    
    if len(p) == 3:  # casos caso
        p[0] = ASTNode('casos', children=[p[1], p[2]], lineno=p.lineno(1))
    elif len(p) == 2:  # caso único
        p[0] = ASTNode('casos', children=[p[1]], lineno=p.lineno(1))
    elif len(p) == 7:  # casos con default
        default_node = ASTNode('default', children=[p[5]], lineno=p.lineno(2))
        p[0] = ASTNode('casos', children=[p[1], default_node], lineno=p.lineno(1))
    else:  # default único
        p[0] = ASTNode('casos', children=[ASTNode('default', children=[p[5]], lineno=p.lineno(1))], lineno=p.lineno(1))

def p_caso(p):
    'caso : CASE expresion COLON LBRACE lista_declaraciones RBRACE'
    p[0] = ASTNode('case', children=[p[2], p[5]], lineno=p.lineno(1))

def p_case(p):
    'case : CASE expresion COLON lista_declaraciones'
    p[0] = ASTNode('case', children=[p[2], p[4]], lineno=p.lineno(1))
    
def p_repeticion(p):
    '''repeticion : DO LBRACE lista_declaraciones RBRACE WHILE LPAREN expresion RPAREN SEMICOLON
                  | DO lista_declaraciones UNTIL expresion SEMICOLON'''
    if len(p) == 10:
        p[0] = ASTNode('do_while', children=[p[3], p[7]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('do_until', children=[p[2], p[4]], lineno=p.lineno(1))

def p_default_case(p):
    'default_case : DEFAULT COLON lista_declaraciones'
    p[0] = ASTNode('default', children=[p[3]], lineno=p.lineno(1))

def p_seleccion(p):
    '''seleccion : IF expresion THEN LBRACE lista_declaraciones RBRACE
                 | IF expresion THEN LBRACE lista_declaraciones RBRACE ELSE LBRACE lista_declaraciones RBRACE
                 | IF LPAREN expresion RPAREN LBRACE lista_declaraciones RBRACE
                 | IF LPAREN expresion RPAREN LBRACE lista_declaraciones RBRACE ELSE LBRACE lista_declaraciones RBRACE
                 | SWITCH LPAREN expresion RPAREN LBRACE casos RBRACE'''
    
    if len(p) == 7 and p[1] == 'if':  # if-then sin else
        p[0] = ASTNode('if_then', children=[p[2], p[5]], lineno=p.lineno(1))
    elif len(p) == 11:  # if-then con else
        p[0] = ASTNode('if_then_else', children=[p[2], p[5], p[9]], lineno=p.lineno(1))
    elif len(p) == 8 and p[1] == 'if':  # if con paréntesis sin else
        p[0] = ASTNode('if', children=[p[3], p[6]], lineno=p.lineno(1))
    elif len(p) == 10 and p[1] == 'if':  # if con paréntesis con else
        p[0] = ASTNode('if_else', children=[p[3], p[6], p[9]], lineno=p.lineno(1))
    else:  # switch
        p[0] = ASTNode('switch', children=[p[3], p[6]], lineno=p.lineno(1))

def p_iteracion(p):
    '''iteracion : WHILE LPAREN expresion RPAREN sentencia
                | for_loop'''
    if p[1] == 'while':
        p[0] = ASTNode('while', children=[p[3], p[5]], lineno=p.lineno(1))
    else:
        p[0] = p[1]  # for_loop
        
# def p_for_loop(p):
#     'for_loop : FOR LPAREN asignacion expresion SEMICOLON expresion RPAREN LBRACE lista_declaraciones RBRACE'
#     p[0] = ASTNode('for', children=[p[3], p[4], p[6], p[9]], lineno=p.lineno(1))
        
        


def p_declaracion(p):
    '''declaracion : declaracion_variable 
                  | sentencia'''
    p[0] = p[1]
    
# Después de las reglas existentes, agrega:

def p_function_definition(p):
    '''declaracion : FUNCTION tipo ID LPAREN parameters RPAREN LBRACE lista_declaraciones RBRACE
                   | FUNCTION VOID ID LPAREN parameters RPAREN LBRACE lista_declaraciones RBRACE'''
    if p[2] == 'void':
        func_type = 'void'
        func_name = p[3]
        func_body = p[7]
    else:
        func_type = p[2].value
        func_name = p[3]
        func_body = p[7]
    
    func_node = ASTNode('function_definition', children=[p[4], func_body], value=func_type, lineno=p.lineno(1))
    func_node.func_name = func_name
    p[0] = func_node

def p_parameters(p):
    '''parameters : parameter_list
                 | empty'''
    p[0] = ASTNode('parameters', children=[p[1]] if p[1] else [], lineno=p.lineno(1))

def p_parameter_list(p):
    '''parameter_list : parameter
                     | parameter_list COMMA parameter'''
    if len(p) == 2:
        p[0] = ASTNode('parameter_list', children=[p[1]], lineno=p.lineno(1))
    else:
        p[1].children.append(p[3])
        p[0] = p[1]

def p_parameter(p):
    'parameter : tipo ID'
    param_type = ASTNode('tipo', value=p[1].value, lineno=p.lineno(1))
    param_name = ASTNode('identificador', value=p[2], lineno=p.lineno(2))
    p[0] = ASTNode('parameter', children=[param_type, param_name], lineno=p.lineno(1))

def p_function_call(p):
    'expresion : ID LPAREN arguments RPAREN'
    func_name = ASTNode('identificador', value=p[1], lineno=p.lineno(1))
    p[0] = ASTNode('function_call', children=[func_name, p[3]], lineno=p.lineno(1))

def p_arguments(p):
    '''arguments : argument_list
                | empty'''
    p[0] = ASTNode('arguments', children=[p[1]] if p[1] else [], lineno=p.lineno(1))

def p_argument_list(p):
    '''argument_list : expresion
                    | argument_list COMMA expresion'''
    if len(p) == 2:
        p[0] = ASTNode('argument_list', children=[p[1]], lineno=p.lineno(1))
    else:
        p[1].children.append(p[3])
        p[0] = p[1]

def p_return_statement(p):
    'sentencia : RETURN expresion SEMICOLON'
    p[0] = ASTNode('return_statement', children=[p[2]], lineno=p.lineno(1))

def p_declaracion_variable(p):
    'declaracion_variable : tipo lista_ids SEMICOLON'
    p[0] = ASTNode('declaracion_variable', children=[p[1], p[2]], lineno=p.lineno(1))

def p_lista_ids(p):
    '''lista_ids : ID
                | lista_ids COMMA ID'''
    if len(p) == 2:
        p[0] = ASTNode('lista_ids', children=[ASTNode('identificador', value=p[1], lineno=p.lineno(1))], lineno=p.lineno(1))
    else:
        new_id = ASTNode('identificador', value=p[3], lineno=p.lineno(3))
        p[1].children.append(new_id)
        p[0] = p[1]

def p_tipo(p):
    '''tipo : INT
           | FLOAT
           | BOOL
           | STRING'''
    p[0] = ASTNode('tipo', value=p[1], lineno=p.lineno(1))

def p_sentencia(p):
    '''sentencia : asignacion
                | expresion SEMICOLON
                | seleccion
                | iteracion
                | repeticion
                | sent_in
                | sent_out
                | LBRACE lista_declaraciones RBRACE'''
    if len(p) == 4:  # Bloque { ... }
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_asignacion(p):
    'asignacion : ID EQ expresion SEMICOLON'
    id_node = ASTNode('identificador', value=p[1], lineno=p.lineno(1))
    p[0] = ASTNode('asignacion', children=[id_node, p[3]], value='=', lineno=p.lineno(2))

# EXPRESIONES
def p_expresion(p):
    '''expresion : expresion OR expresion_and
                | expresion_and
                | STRING_LITERAL
                | NOT expresion'''  # <- AGREGAR ESTA LINEA
    if len(p) == 2:
        p[0] = p[1]
    elif p[1] == '!':  # NOT expression
        p[0] = ASTNode('operacion_unaria', children=[p[2]], value='!', lineno=p.lineno(1))
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value='||', lineno=p.lineno(2))
        
def p_expresion_and(p):
    '''expresion_and : expresion_and AND expresion_rel
                    | expresion_rel'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value='&&', lineno=p.lineno(2))

def p_expresion_rel(p):
    '''expresion_rel : expresion_rel relacion expresion_add
                    | expresion_add'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_relacion(p):
    '''relacion : LT
               | LE
               | GT
               | GE
               | EEQ
               | NE'''
    p[0] = p[1]


def p_expresion_add(p):
    '''expresion_add : expresion_add suma termino
                    | termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_suma(p):
    '''suma : PLUS
           | MIN'''
    p[0] = p[1]

def p_termino(p):
    '''termino : termino mult factor
              | factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_mult(p):
    '''mult : TIMES
           | DIVIDE
           | MODULO'''
    p[0] = p[1]

def p_factor(p):
    '''factor : componente
             | MIN factor %prec UMINUS'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_unaria', children=[p[2]], value='-', lineno=p.lineno(1))
        


def p_componente(p):
    '''componente : ID
                 | numero
                 | booleano
                 | STRING_LITERAL
                 | LPAREN expresion RPAREN'''
    if len(p) == 2:
        if isinstance(p[1], str):  # ID o STRING_LITERAL
            if p.slice[1].type == 'STRING_LITERAL':
                p[0] = ASTNode('string_literal', value=p[1], lineno=p.lineno(1))
            else:
                p[0] = ASTNode('identificador', value=p[1], lineno=p.lineno(1))
        else:  # numero o booleano
            p[0] = p[1]
    else:
        p[0] = p[2]

    
def p_numero(p):
    '''numero : NUMBER
             | REAL'''
    p[0] = ASTNode('numero', value=p[1], lineno=p.lineno(1))
    
def p_booleano(p):
    '''booleano : TRUE
               | FALSE'''
    p[0] = ASTNode('booleano', value=p[1], lineno=p.lineno(1))

# ESTRUCTURAS DE CONTROL
def p_seleccion(p):
    '''seleccion : IF LPAREN expresion RPAREN sentencia
                | IF LPAREN expresion RPAREN sentencia ELSE sentencia'''
    if len(p) == 6:
        p[0] = ASTNode('if', children=[p[3], p[5]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('if_else', children=[p[3], p[5], p[7]], lineno=p.lineno(1))

def p_iteracion(p):
    'iteracion : WHILE LPAREN expresion RPAREN sentencia'
    p[0] = ASTNode('while', children=[p[3], p[5]], lineno=p.lineno(1))

def p_repeticion(p):
    'repeticion : DO sentencia WHILE LPAREN expresion RPAREN SEMICOLON'
    p[0] = ASTNode('do_while', children=[p[2], p[5]], lineno=p.lineno(1))

def p_sent_in(p):
    'sent_in : CIN OP_IN ID SEMICOLON'
    var_node = ASTNode('identificador', value=p[3], lineno=p.lineno(3))
    p[0] = ASTNode('input', children=[var_node], lineno=p.lineno(1))

def p_sent_out(p):
    'sent_out : COUT OP_OUT expresion SEMICOLON'
    p[0] = ASTNode('output', children=[p[3]], lineno=p.lineno(1))

def p_error(p):
    if p:
        error_msg = f"Error de sintaxis en '{p.value}' (línea {p.lineno})"
        if not hasattr(parser, 'errors'):
            parser.errors = []
        parser.errors.append({'type': 'sintactico', 'message': error_msg, 'line': p.lineno})
    else:
        error_msg = "Error de sintaxis: fin de archivo inesperado"
        if not hasattr(parser, 'errors'):
            parser.errors = []
        parser.errors.append({'type': 'sintactico', 'message': error_msg, 'line': 1})

# Construir el parser
parser = yacc.yacc()

def parse_code(input_text):
    # Importar aquí para evitar circularidad
    global lexer
    if lexer is None:
        try:
            from lexico import lexer as imported_lexer
            lexer = imported_lexer
        except ImportError:
            return {
                'ast': None,
                'errors': [{'type': 'fatal', 'message': 'No se pudo importar el lexer'}],
                'success': False
            }
    
    if lexer is None:
        return {
            'ast': None,
            'errors': [{'type': 'fatal', 'message': 'Lexer no disponible'}],
            'success': False
        }
    
    lexer.input(input_text)
    parser.errors = []
    
    try:
        ast = parser.parse(input_text, lexer=lexer, debug=False)
        return {
            'ast': ast,
            'errors': getattr(parser, 'errors', []),
            'success': len(getattr(parser, 'errors', [])) == 0
        }
    except Exception as e:
        return {
            'ast': None,
            'errors': [{'type': 'fatal', 'message': str(e)}],
            'success': False
        }