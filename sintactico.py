# sintactico.py - Sin importaciones circulares
import ply.yacc as yacc

# Importar desde lexico (sin circularidad)
try:
    from lexico import tokens, lexer
except ImportError:
    # Definir tokens básicos por si falla la importación
    tokens = []
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

def p_lista_declaraciones(p):
    '''lista_declaraciones : lista_declaraciones declaracion
                          | declaracion'''
    if len(p) == 3:
        p[0] = ASTNode('lista_declaraciones', children=[p[1], p[2]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('lista_declaraciones', children=[p[1]], lineno=p.lineno(1))
    
def p_switch_statement(p):
    '''switch_statement : SWITCH LPAREN expresion RPAREN LBRACE cases RBRACE
                       | SWITCH LPAREN expresion RPAREN LBRACE cases DEFAULT COLON lista_declaraciones RBRACE'''
    if len(p) == 8:
        p[0] = ASTNode('switch', children=[p[3], p[6]], lineno=p.lineno(1))
    else:
        default_node = ASTNode('default', children=[p[9]], lineno=p.lineno(7))
        p[6].children.append(default_node)
        p[0] = ASTNode('switch', children=[p[3], p[6]], lineno=p.lineno(1))
def p_cases(p):
    '''cases : cases case
            | case'''
    if len(p) == 3:
        p[0] = ASTNode('cases', children=[p[1], p[2]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('cases', children=[p[1]], lineno=p.lineno(1))

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


def p_seleccion(p):
    '''seleccion : IF expresion THEN LBRACE lista_declaraciones RBRACE
                 | IF expresion THEN LBRACE lista_declaraciones RBRACE ELSE LBRACE lista_declaraciones RBRACE'''
    if len(p) == 7:
        p[0] = ASTNode('if_then', children=[p[2], p[5]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('if_then_else', children=[p[2], p[5], p[9]], lineno=p.lineno(1))

def p_iteracion(p):
    '''iteracion : WHILE expresion LBRACE lista_declaraciones RBRACE
                 | WHILE expresion THEN lista_declaraciones END'''
    if len(p) == 6:
        p[0] = ASTNode('while', children=[p[2], p[4]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('while', children=[p[2], p[4]], lineno=p.lineno(1))
        
def p_for_loop(p):
    '''for_loop : FOR LPAREN asignacion expresion SEMICOLON expresion RPAREN LBRACE lista_declaraciones RBRACE
                | FOR asignacion expresion SEMICOLON expresion LBRACE lista_declaraciones RBRACE'''
    if len(p) == 11:
        p[0] = ASTNode('for', children=[p[3], p[4], p[6], p[9]], lineno=p.lineno(1))
    else:
        p[0] = ASTNode('for', children=[p[2], p[3], p[5], p[7]], lineno=p.lineno(1))
        
        


def p_declaracion(p):
    '''declaracion : declaracion_variable 
                  | sentencia'''
    p[0] = p[1]

def p_declaracion_variable(p):
    'declaracion_variable : tipo lista_ids SEMICOLON'
    p[0] = ASTNode('declaracion_variable', children=[p[1], p[2]], lineno=p.lineno(1))

def p_lista_ids(p):
    '''lista_ids : ID
                | lista_ids COMMA ID'''
    if len(p) == 2:
        p[0] = ASTNode('lista_ids', children=[ASTNode('identificador', value=p[1])], lineno=p.lineno(1))
    else:
        new_id = ASTNode('identificador', value=p[3])
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
                | expresion_and'''
    if len(p) == 2:
        p[0] = p[1]
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
                 | LPAREN expresion RPAREN'''
    if len(p) == 2:
        if isinstance(p[1], str):  # ID
            p[0] = ASTNode('identificador', value=p[1], lineno=p.lineno(1))
        else:  # numero
            p[0] = p[1]
    else:
        p[0] = p[2]

def p_numero(p):
    '''numero : NUMBER
             | REAL'''
    p[0] = ASTNode('numero', value=p[1], lineno=p.lineno(1))

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