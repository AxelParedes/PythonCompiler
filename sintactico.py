import ply.yacc as yacc
from lexico import tokens, lexer
import tempfile

# Definición de la gramática y las reglas de producción
# programa —> 		    MAIN LLAVE_I lista_declaracion LLAVE_D,
# lista_declaracion —> 	declaracion { declaracion },
# declaración -> 		    declaracion_variable | lista_sentencias,
# declaracion_variable ->	tipo identificador PUNTO_Y_COMA,
# identificador -> 	    IDENTIFICADOR { COMA IDENTIFICADOR },
# tipo —> 		        INTEGER | DOUBLE,
# lista_sentencias —> 	vacio { sentencia },
# sentencia -> 		    seleccion | iteracion | repeticion | sent_in | sent_out | asignacion | inc_dec_exp,
# inc_dec_exp ->		    IDENTIFICADOR inc_dec_op PUNTO_Y_COMA,
# inc_dec_op ->		    INCREMENTO | DECREMENTO,
# asignación -> 		    IDENTIFICADOR ASIGNACION sent_expresion,
# sent_expresion -> 	    expresion PUNTO_Y_COMA,
# seleccion -> 		    IF PARENTESIS_I expresion PARENTESIS_D LLAVE_I lista_sentencias LLAVE_D | IF PARENTESIS_I expresion PARENTESIS_D LLAVE_I lista_sentencias LLAVE_D ELSE LLAVE_I lista_sentencias LLAVE_D,
# iteracion -> 		    WHILE PARENTESIS_I expresion PARENTESIS_D LLAVE_I lista_sentencias LLAVE_D,
# repeticion -> 		    DO LLAVE_I lista_sentencias LLAVE_D WHILE PARENTESIS_I expresion PARENTESIS_D PUNTO_Y_COMA,
# sent_in -> 		        CIN INDENTIFICADOR PUNTO_Y_COMA,
# sent_out -> 		    COUT expresion PUNTO_Y_COMA,
# expresion -> 		    expresion_relacional logico_op expresion_relacional | expresion_relacional,
# logico_op ->		    AND | OR,
# expresion_relacional ->	expresion_simple relacion_op expresion_simple | expresion_simple,
# relacion_op -> 		    MENOR | MENOR_IGUAL | MAYOR | MAYOR_IGUAL | IGUAL | DIFERENTE,
# expresion_simple -> 	termino { suma_op termino },
# suma_op ->		        SUMA | RESTA,
# termino ->		        factor { mult_op factor },
# mult_op ->		        MULTIPLICACION | DIVISION | MODULO,
# factor ->		        componente { pot_op componente },
# pot_op ->		        POTENCIA,
# componente ->		    PARENTESIS_I expresion PARENTESIS_D | numero | IDENTIFICADOR,
# numero ->		        ENTERO | REAL | ENTERO_NEG | REAL_NEG,

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
    ('right', 'POWER'),
    ('left', 'MODULO'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'PLUS', 'MIN'),
    ('nonassoc', 'LT', 'LE', 'GT', 'GE', 'NE', 'EEQ'),
    ('left', 'AND', 'OR'),
)

def p_programa(p):
    '''programa : MAIN LBRACE lista_declaracion RBRACE'''
    p[0] = ASTNode('programa', children=[p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_lista_declaracion(p):
    '''lista_declaracion : lista_declaracion declaracion
                        | declaracion'''
    if len(p) == 3:
        p[0] = ASTNode('lista_declaracion', children=[p[1], p[2]], lineno=p[1].lineno, lexpos=p[1].lexpos)
    else:
        p[0] = ASTNode('lista_declaracion', children=[p[1]], lineno=p[1].lineno, lexpos=p[1].lexpos)

def p_declaracion(p):
    '''declaracion : declaracion_variable 
                  | lista_sentencias'''
    p[0] = p[1]
    
def p_lista_identificadores(p):
    '''lista_identificadores : ID
                            | ID COMMA lista_identificadores'''
    if len(p) == 2:
        p[0] = ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('lista_identificadores', children=[
            ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1)),
            p[3]
        ], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_declaracion_variable(p):
    '''declaracion_variable : tipo lista_identificadores SEMICOLON'''
    p[0] = ASTNode('declaracion_variable', children=[p[1], p[2]], lineno=p[1].lineno, lexpos=p[1].lexpos)

def p_identificador(p):
    '''identificador : ID
                    | ID COMMA identificador'''
    if len(p) == 2:
        p[0] = ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('identificador_lista', children=[
            ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1)),
            p[3]
        ], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_tipo(p):
    '''tipo : INT
           | FLOAT'''
    p[0] = ASTNode('tipo', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_lista_sentencias(p):
    '''lista_sentencias : lista_sentencias repeticion
                       | lista_sentencias seleccion
                       | lista_sentencias sentencia
                       | repeticion
                       | seleccion
                       | sentencia'''
    if len(p) == 3:
        p[0] = ASTNode('lista_sentencias', [p[1], p[2]], lineno=p[1].lineno, lexpos=p[1].lexpos)
    else:
        p[0] = ASTNode('lista_sentencias', [p[1]], lineno=p[1].lineno, lexpos=p[1].lexpos)

def p_sentencia(p):
    '''sentencia : seleccion
                | iteracion
                | repeticion
                | sent_in
                | sent_out
                | asignacion
                | inc_dec_exp'''
    p[0] = p[1]


def p_inc_dec_exp(p):
    '''inc_dec_exp : ID INCREMENT SEMICOLON
                  | ID DECREMENT SEMICOLON'''
    operador = '+' if p[2] == '++' else '-'
    id_node = ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    uno_node = ASTNode('numero', value='1', lineno=p.lineno(2), lexpos=p.lexpos(2))

    expr_node = ASTNode('expresion_binaria', value=operador, children=[id_node, uno_node], lineno=p.lineno(2), lexpos=p.lexpos(2))

    p[0] = ASTNode('asignacion', value='=', children=[id_node, expr_node], lineno=p.lineno(2), lexpos=p.lexpos(2))



def p_asignacion(p):
    '''asignacion : ID EQ expresion SEMICOLON'''
    p[0] = ASTNode('asignacion', 
                  children=[
                      ASTNode('identificador', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1)),
                      p[3]
                  ], 
                  value=p[2],  # Esto captura el '='
                  lineno=p.lineno(2), lexpos=p.lexpos(2))

def p_sent_expresion(p):
    '''sent_expresion : expresion SEMICOLON'''
    p[0] = p[1]

def p_seleccion(p):
    '''seleccion : IF condicion THEN bloque_condicional
                | IF condicion THEN bloque_condicional ELSE bloque_condicional'''
    if len(p) == 5:
        p[0] = ASTNode('if_then', children=[p[2], p[4]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('if_then_else', children=[p[2], p[4], p[6]], lineno=p.lineno(1), lexpos=p.lexpos(1))
        
def p_condicion(p):
    '''condicion : expresion
                | expresion_relacional
                | expresion_logica'''
    p[0] = p[1]
        
def p_bloque(p):
    '''bloque : LBRACE lista_sentencias RBRACE
             | sentencia'''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = ASTNode('bloque', children=[p[1]], lineno=p[1].lineno, lexpos=p[1].lexpos)
        
def p_bloque_condicional(p):
    '''bloque_condicional : LBRACE lista_sentencias RBRACE
                         | sentencia
                         | lista_sentencias END'''
    if len(p) == 4:
        p[0] = p[2]
    elif len(p) == 3:
        p[0] = p[1]
    else:
        p[0] = ASTNode('bloque', children=[p[1]], lineno=p[1].lineno, lexpos=p[1].lexpos)

def p_empty(p):
    'empty :'
    p[0] = ASTNode('empty')

def p_iteracion(p):
    '''iteracion : WHILE LPAREN expresion RPAREN LBRACE lista_sentencias RBRACE
                 | WHILE expresion lista_sentencias END'''
    if len(p) == 8:
        p[0] = ASTNode('while', children=[p[3], p[6]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('while', children=[p[2], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_repeticion(p):
    '''repeticion : DO lista_sentencias bloque_while_opcional UNTIL expresion
                  | WHILE expresion lista_sentencias END'''
    if p[1] == 'do':
        p[0] = ASTNode('do_until', [p[2], p[3], p[5]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('while', [p[2], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
        
def p_bloque_while_opcional(p):
    '''bloque_while_opcional : WHILE expresion lista_sentencias END
                            | empty'''
    if len(p) > 2:
        p[0] = ASTNode('while_anidado', [p[2], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('empty')
        
def p_anidados_while(p):
    '''anidados_while : WHILE expresion lista_sentencias END
                     | empty'''
    if len(p) > 2:
        p[0] = ASTNode('while_anidado', [p[2], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = p[1]
        
def p_bloque_repeticion(p):
    '''bloque_repeticion : LBRACE lista_sentencias RBRACE
                        | sentencia
                        | lista_sentencias END'''
    if len(p) == 4:
        p[0] = p[2]
    elif len(p) == 3:
        p[0] = p[1]
    else:
        p[0] = ASTNode('bloque', [p[1]], lineno=p[1].lineno, lexpos=p[1].lexpos)

def p_sent_in(p):
    '''sent_in : CIN OP_IN ID SEMICOLON
              | CIN OP_IN ID OP_IN ID SEMICOLON'''
    if len(p) == 5:
        p[0] = ASTNode('input', [
            ASTNode('variable', value=p[3], lineno=p.lineno(3), lexpos=p.lexpos(3))
        ], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('input', [
            ASTNode('variable', value=p[3], lineno=p.lineno(3), lexpos=p.lexpos(3)),
            ASTNode('variable', value=p[5], lineno=p.lineno(5), lexpos=p.lexpos(5))
        ], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_sent_out(p):
    '''sent_out : COUT OP_OUT expresion SEMICOLON
               | COUT OP_OUT expresion OP_OUT expresion SEMICOLON'''
    if len(p) == 5:
        p[0] = ASTNode('output', [p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('output', [p[3], p[5]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    
def p_expresion_simple(p):
    '''expresion_simple : termino
                       | expresion_simple suma_op termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_expresion(p):
    '''expresion : expresion_relacional
                | expresion logico_op expresion_relacional'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_logica', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))

def p_expresion_condicion(p):
    '''expresion_condicion : expresion_relacional
                          | expresion'''
    p[0] = p[1]
        
def p_expresion_logica(p):
    '''expresion_logica : expresion_relacional
                       | expresion_logica AND expresion_relacional
                       | expresion_logica OR expresion_relacional
                       | NOT expresion_relacional'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ASTNode('not_expr', children=[p[2]], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('logica_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))

def p_componente(p):
    '''componente : LPAREN expresion RPAREN
                 | numero
                 | ID'''
    if len(p) == 4:
        p[0] = p[2]
    elif len(p) == 2:
        # Para números e identificadores, usamos el nodo directamente
        p[0] = p[1]

def p_logico_op(p):
    '''logico_op : AND
                | OR'''
    p[0] = p[1]

def p_expresion_relacional(p):
    '''expresion_relacional : expresion_simple
                           | expresion_simple relacion_op expresion_simple'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_relacional', 
                      children=[p[1], p[3]], 
                      value=p[2],
                      lineno=p.lineno(2), lexpos=p.lexpos(2))

def p_relacion_op(p):
    '''relacion_op : LT
                  | LE
                  | GT
                  | GE
                  | NE
                  | EEQ'''
    p[0] = p[1]

def p_suma_op(p):
    '''suma_op : PLUS
              | MIN'''
    p[0] = p[1]


def p_termino(p):
    '''termino : factor
              | termino mult_op factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_mult_op(p):
    '''mult_op : TIMES
              | DIVIDE
              | MODULO'''
    p[0] = p[1]


def p_factor(p):
    '''factor : componente
             | componente pot_op componente'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode('expresion_binaria', children=[p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_pot_op(p):
    '''pot_op : POWER'''
    p[0] = p[1]

def p_numero(p):
    '''numero : NUMBER
             | REAL
             | MIN NUMBER %prec MIN
             | MIN REAL %prec MIN'''
    if len(p) == 2:
        p[0] = ASTNode('numero', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:
        p[0] = ASTNode('numero_negativo', value=f"-{p[2]}", lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_error(p):
    if p:
        line = find_line(p)
        column = find_column(p)
        
        if p.type in ['FLOAT', 'INT'] and column > 1:
            prev_token = find_previous_token(p)
            if prev_token and prev_token.type == 'ID':
                error_line = find_line(prev_token)
                error_col = find_column(prev_token) + len(prev_token.value)
                message = f"Falta ';' después de '{prev_token.value}'"
                
                error_msg = {
                    'type': 'sintactico',
                    'value': ';',
                    'token_type': 'SEMICOLON',
                    'line': error_line,
                    'column': error_col,
                    'message': message,
                    'lexpos': prev_token.lexpos + len(prev_token.value)
                }
                
                if not hasattr(parser, 'errors'):
                    parser.errors = []
                parser.errors.append(error_msg)
                
                parser.errok()
                return p
            else:
                message = f"Token inesperado '{p.value}'"
        else:
            message = f"Token inesperado '{p.value}'"
        
        error_msg = {
            'type': 'sintactico',
            'value': p.value,
            'token_type': p.type,
            'line': line,
            'column': column,
            'message': message,
            'lexpos': p.lexpos
        }
        
        if not hasattr(parser, 'errors'):
            parser.errors = []
        parser.errors.append(error_msg)
        
        while True:
            tok = parser.token()
            if not tok or tok.type in ['SEMICOLON', 'RBRACE', 'LBRACE']:
                parser.errok()
                return tok
    else:
        error_msg = {
            'type': 'sintactico',
            'message': "Fin de archivo inesperado",
            'line': 1,
            'column': 1
        }
        if not hasattr(parser, 'errors'):
            parser.errors = []
        parser.errors.append(error_msg)

def find_previous_token(p):
    if not hasattr(p, 'lexer') or not hasattr(p.lexer, 'lexstat'):
        return None
    
    tokens = []
    while True:
        tok = p.lexer.token()
        if not tok:
            break
        tokens.append(tok)
    
    for tok in reversed(tokens):
        if tok.type not in ['WS', 'NEWLINE']:
            return tok
    return None
        
def find_column(p):
    if not hasattr(p, 'lexer') or not hasattr(p.lexer, 'lexdata'):
        return 1
    
    last_cr = p.lexer.lexdata.rfind('\n', 0, p.lexpos)
    if last_cr < 0:
        last_cr = -1
    column = (p.lexpos - last_cr)
    return max(1, column)

def find_line(p):
    if not hasattr(p, 'lexer') or not hasattr(p.lexer, 'lexdata'):
        return 1

    return p.lexer.lexdata.count('\n', 0, p.lexpos) + 1

def read_tokens_from_file(file_path):
    tokens = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith("TOKENS"):
                parts = line.split()
                if len(parts) >= 2:
                    token_type = parts[0]
                    token_value = parts[1]
                    tokens.append((token_type, token_value))
    return tokens

parser = yacc.yacc()

def parse_code(input_text):
    lexer.input(input_text)
    temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False)
    temp_file.write("TOKENS GENERADOS:\n")
    temp_file.write("----------------\n")
    
    tokens_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens_list.append(tok)
        temp_file.write(f"{tok.type:<10} {tok.value:<10} linea {tok.lineno} pos {tok.lexpos}\n")
    
    temp_file.close()
    print(f"Tokens guardados en archivo temporal: {temp_file.name}")
    
    parser.errors = []
    try:
        ast = parser.parse(input_text, lexer=lexer, debug=False)
        return {
            'ast': ast,
            'errors': parser.errors,
            'success': len(parser.errors) == 0
        }
    except Exception as e:
        error_msg = {
            'type': 'fatal',
            'message': str(e),
            'line': 'desconocida',
            'column': 'desconocida'
        }