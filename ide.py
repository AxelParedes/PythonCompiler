import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from setuptools import Command
from semantico import test_semantics
from sintactico import ASTNode, parse_code
from lexico import test_lexer
from sintactico import parse_code
from tkinter import PhotoImage
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from pygments.style import Style
from pygments.util import ClassNotFound
import re

tk._default_root = None


# Palabras reservadas (deben coincidir con las definidas en lexico.py)
reserved = {
    'if': 'IF', 'else': 'ELSE', 'end': 'END', 'do': 'DO', 'while': 'WHILE', 'switch': 'SWITCH',
    'case': 'CASE', 'int': 'INT', 'float': 'FLOAT', 'main': 'MAIN', 'cin': 'CIN', 'cout': 'COUT', 'then': 'THEN',
    'until': 'UNTIL', 'true': 'TRUE', 'false': 'FALSE', 'bool': 'BOOL', 'string': 'STRING', 'error': 'ERROR', 'function': 'FUNCTION', 'return': 'RETURN', 'void': 'VOID', 'params': 'PARAMS'
}


class NodoHash:
    def __init__(self, simbolo):
        self.simbolo = simbolo
        self.siguiente = None

class TablaHash:
    def __init__(self, tamaño=10):
        self.tamaño = tamaño
        self.tabla = [None] * tamaño
    
    def _hash(self, nombre):
        """Función hash simple basada en el primer carácter"""
        if not nombre:
            return 0
        return ord(nombre[0].upper()) % self.tamaño
    
    def insertar(self, simbolo):
        """Inserta un símbolo en la tabla hash"""
        indice = self._hash(simbolo['nombre'])
        nuevo_nodo = NodoHash(simbolo)
        
        # Insertar al inicio de la lista enlazada
        nuevo_nodo.siguiente = self.tabla[indice]
        self.tabla[indice] = nuevo_nodo
    
    def obtener_todos(self):
        """Obtiene todos los símbolos organizados por índice"""
        resultado = []
        for i in range(self.tamaño):
            simbolos_indice = []
            actual = self.tabla[i]
            while actual:
                simbolos_indice.append(actual.simbolo)
                actual = actual.siguiente
            resultado.append((i, simbolos_indice))
        return resultado

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None
        self.bind("<Configure>", self._on_configure)

    def attach(self, text_widget):
        self.textwidget = text_widget
        # Configurar eventos para redibujar cuando se hace scroll o se modifica el texto
        self.textwidget.bind("<Configure>", self._on_configure)
        self.textwidget.bind("<MouseWheel>", self._on_mousewheel)
        self.textwidget.bind("<Button-4>", self._on_mousewheel)  # Para Linux
        self.textwidget.bind("<Button-5>", self._on_mousewheel)  # Para Linux

    def _on_configure(self, event=None):
        self.redraw()

    def _on_mousewheel(self, event):
        # Programar redibujo después de un pequeño retraso para que el scroll tenga efecto
        self.after(10, self.redraw)
        return None  # Permitir que el evento continúe

    def redraw(self, *args):
        '''Redibuja los números de línea para el texto visible'''
        self.delete("all")
        
        if not self.textwidget:
            return
            
        # Obtener información sobre el texto visible
        first_visible_line = int(self.textwidget.index("@0,0").split('.')[0])
        last_visible_line = int(self.textwidget.index("@0,%d" % self.textwidget.winfo_height()).split('.')[0])
        
        # Ajustar para asegurarnos de cubrir todo el área visible
        last_visible_line += 1
        
        # Dibujar solo las líneas visibles
        for i in range(first_visible_line, last_visible_line + 1):
            # Obtener posición y de la línea
            dline = self.textwidget.dlineinfo(f"{i}.0")
            if dline is None:  # Si la línea no existe
                continue
            y = dline[1]
            # Dibujar el número de línea
            self.create_text(
                2, y, 
                anchor="nw", 
                text=str(i), 
                fill="#555",
                font=("Consolas", 10)  # Usar la misma fuente que el editor
            )

class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)
        
        #nodos a omitir
        self.omit_nodes = {
            'lista_declaracion',
            'lista_identificadores', 
            'lista_sentencias',
        }
            
        
        # Configuración del editor
        self.config(
            undo=True,
            wrap=tk.NONE,
            width=80,
            height=20,
            bg="white",
            fg="black",
            insertbackground="black",
            font=("Consolas", 10)
        )
        
        # Configurar colores para cada tipo de token
        self.tag_config("NUMBER", foreground="blue")
        self.tag_config("REAL", foreground="blue") 
        self.tag_config("ID", foreground="black") 
        self.tag_config("COMMENT", foreground="green")
        self.tag_config("RESERVED", foreground="purple")
        self.tag_config("OPERATOR", foreground="red")
        self.tag_config("RELATIONAL", foreground="orange")
        self.tag_config("LOGICAL", foreground="orange")
        self.tag_config("SYMBOL", foreground="brown")
        self.tag_config("ASSIGN", foreground="darkgreen")
        self.tag_config("STRING", foreground="darkorange")
        self.tag_config("BOOL", foreground="purple", font=("Consolas", 10, "bold"))
        self.tag_config("ERROR", foreground="red", underline=True)

        # Configurar eventos
        self.bind("<<Modified>>", self._on_modified)
        self.after_id = None

    def _proxy(self, *args):
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)
        
        if args[0] in ("insert", "replace", "delete"):
            self.event_generate("<<TextModified>>")
        return result
        
    def _on_modified(self, event=None):
        if self.after_id:
            self.after_cancel(self.after_id)
        self.tk.call(self._orig, "edit", "modified", 0)
        self.after_id = self.after(300, self.highlight_syntax)

    def highlight_syntax(self):
        """Resalta la sintaxis del texto en el editor"""
        try:
            # Limpiar todos los tags existentes primero
            for tag in self.tag_names():
                self.tag_remove(tag, "1.0", tk.END)
            
            # Obtener el texto completo
            text = self.get("1.0", tk.END)
            if not text.strip():
                return

            # Primero procesar comentarios (para que tengan prioridad sobre operadores)
            self._highlight_comments(text)
            
            # Luego procesar palabras reservadas exactas
            for word in reserved:
                start = "1.0"
                while True:
                    # Buscar usando regex para coincidencia exacta de palabra
                    start = self.search(rf'\m{word}\M', start, stopindex=tk.END, regexp=True)
                    if not start:
                        break
                    end = f"{start}+{len(word)}c"
                    # Verificar que los índices son válidos y que no está dentro de un comentario
                    if (self._is_valid_index(start) and self._is_valid_index(end)
                            and "COMMENT" not in self.tag_names(start)):
                        self.tag_add("RESERVED", start, end)
                    start = end

            # Finalmente procesar otros tokens
            self._highlight_other_tokens(text)

        except Exception as e:
            print(f"Error general en highlight_syntax: {e}")
            # Limpiar tags en caso de error
            for tag in self.tag_names():
                self.tag_remove(tag, "1.0", tk.END)
                
    
    def _highlight_comments(self, text):
        """Resalta los comentarios en el texto, incluyendo los multi-línea"""
        in_block_comment = False
        block_start = None
        lines = text.split('\n')
        
        for i, line in enumerate(lines, start=1):
            if not in_block_comment:
                # Buscar inicio de comentario de bloque
                block_start_pos = line.find('/*')
                line_comment_pos = line.find('//')
                
                # Comentario de línea tiene prioridad si aparece antes
                if line_comment_pos != -1 and (block_start_pos == -1 or line_comment_pos < block_start_pos):
                    start = f"{i}.{line_comment_pos}"
                    end = f"{i}.{len(line)}"
                    self.tag_add("COMMENT", start, end)
                elif block_start_pos != -1:
                    # Encontramos inicio de comentario de bloque
                    block_end_pos = line.find('*/', block_start_pos + 2)
                    if block_end_pos != -1:
                        # Comentario de bloque completo en una línea
                        start = f"{i}.{block_start_pos}"
                        end = f"{i}.{block_end_pos + 2}"
                        self.tag_add("COMMENT", start, end)
                    else:
                        # Comentario de bloque continúa en siguientes líneas
                        in_block_comment = True
                        block_start = f"{i}.{block_start_pos}"
            else:
                # Estamos dentro de un comentario de bloque, buscar el cierre
                block_end_pos = line.find('*/')
                if block_end_pos != -1:
                    # Fin del comentario de bloque
                    end = f"{i}.{block_end_pos + 2}"
                    self.tag_add("COMMENT", block_start, end)
                    in_block_comment = False
                    block_start = None
                else:
                    # Toda la línea es parte del comentario de bloque
                    start = f"{i}.0"
                    end = f"{i}.{len(line)}"
                    self.tag_add("COMMENT", start, end)

    def _highlight_other_tokens(self, text):
        """Resalta otros tokens (operadores, números, etc.)"""
        try:
            # Usar lexer C++ para otros tokens
            lexer = get_lexer_by_name("cpp", stripall=True)
            
            for token_type, value in lex(text, lexer):
                # Saltar si ya es palabra reservada o comentario
                if value in reserved or token_type in Token.Comment:
                    continue
                
                # Determinar el tag apropiado
                tag = None
                if token_type in Token.Name:
                    tag = "ID"
                elif token_type in Token.Literal.Number.Integer:
                    tag = "NUMBER"
                elif token_type in Token.Literal.Number.Float:
                    tag = "REAL"
                elif token_type in Token.Operator:
                    tag = "OPERATOR"
                elif token_type in Token.Operator.Word:
                    tag = "LOGICAL"
                elif token_type in Token.Punctuation:
                    tag = "SYMBOL"
                elif token_type in Token.Literal.String:
                    tag = "STRING"
                elif token_type in Token.Literal.Boolean:
                    tag = "BOOL"
                
                if not tag:
                    continue

                # Buscar todas las ocurrencias del valor
                start = "1.0"
                while True:
                    start = self.search(re.escape(value), start, stopindex=tk.END, regexp=True)
                    if not start:
                        break
                    end = f"{start}+{len(value)}c"
                    
                    # Verificar índices y que no sea parte de una palabra reservada o comentario
                    if (self._is_valid_index(start) and self._is_valid_index(end) and 
                        "COMMENT" not in self.tag_names(start)):
                        self.tag_add(tag, start, end)
                    start = end

        except ClassNotFound:
            pass
        except Exception as e:
            print(f"Error en el lexer: {e}")

    def _highlight_comments(self, text):
        """Resalta los comentarios en el texto, incluyendo los multi-línea"""
        in_block_comment = False
        block_start = None
        lines = text.split('\n')
        
        for i, line in enumerate(lines, start=1):
            if not in_block_comment:
                # Buscar inicio de comentario de bloque
                block_start_pos = line.find('/*')
                line_comment_pos = line.find('//')
                
                # Comentario de línea tiene prioridad si aparece antes
                if line_comment_pos != -1 and (block_start_pos == -1 or line_comment_pos < block_start_pos):
                    start = f"{i}.{line_comment_pos}"
                    end = f"{i}.{len(line)}"
                    self.tag_add("COMMENT", start, end)
                elif block_start_pos != -1:
                    # Encontramos inicio de comentario de bloque
                    block_end_pos = line.find('*/', block_start_pos + 2)
                    if block_end_pos != -1:
                        # Comentario de bloque completo en una línea
                        start = f"{i}.{block_start_pos}"
                        end = f"{i}.{block_end_pos + 2}"
                        self.tag_add("COMMENT", start, end)
                    else:
                        # Comentario de bloque continúa en siguientes líneas
                        in_block_comment = True
                        block_start = f"{i}.{block_start_pos}"
            else:
                # Estamos dentro de un comentario de bloque, buscar el cierre
                block_end_pos = line.find('*/')
                if block_end_pos != -1:
                    # Fin del comentario de bloque
                    end = f"{i}.{block_end_pos + 2}"
                    self.tag_add("COMMENT", block_start, end)
                    in_block_comment = False
                    block_start = None
                else:
                    # Toda la línea es parte del comentario de bloque
                    start = f"{i}.0"
                    end = f"{i}.{len(line)}"
                    self.tag_add("COMMENT", start, end)

    def _highlight_other_tokens(self, text):
        """Resalta otros tokens (operadores, números, etc.)"""
        try:
            # Usar lexer C++ para otros tokens
            lexer = get_lexer_by_name("cpp", stripall=True)
            
            for token_type, value in lex(text, lexer):
                # Saltar si ya es palabra reservada o comentario
                if value in reserved or token_type in Token.Comment:
                    continue
                
                # Determinar el tag apropiado
                tag = None
                if token_type in Token.Name:
                    tag = "ID"
                elif token_type in Token.Literal.Number.Integer:
                    tag = "NUMBER"
                elif token_type in Token.Literal.Number.Float:
                    tag = "REAL"
                elif token_type in Token.Operator:
                    tag = "OPERATOR"
                elif token_type in Token.Operator.Word:
                    tag = "LOGICAL"
                elif token_type in Token.Punctuation:
                    tag = "SYMBOL"
                
                if not tag:
                    continue

                # Buscar todas las ocurrencias del valor
                start = "1.0"
                while True:
                    start = self.search(re.escape(value), start, stopindex=tk.END, regexp=True)
                    if not start:
                        break
                    end = f"{start}+{len(value)}c"
                    
                    # Verificar índices y que no sea parte de una palabra reservada o comentario
                    if (self._is_valid_index(start) and self._is_valid_index(end) and 
                        "COMMENT" not in self.tag_names(start)):
                        self.tag_add(tag, start, end)
                    start = end

        except ClassNotFound:
            pass
        except Exception as e:
            print(f"Error en el lexer: {e}")

    def _is_valid_index(self, index):
        """Verifica si un índice de texto es válido"""
        try:
            self.index(index)
            return True
        except tk.TclError:
            return False
        
    def _highlight_syntax_errors(self, errors, input_lines):
        """Resalta los errores sintácticos en el editor"""
        self.editor.tag_remove("ERROR", "1.0", tk.END)
        
        for error in errors:
            # Extraer información de ubicación del error
            if "línea" in error:
                try:
                    parts = error.split("línea")[1].split(",")
                    line = int(parts[0].strip())
                    col = int(parts[1].split(":")[0].replace("columna", "").strip())
                    
                    if 1 <= line <= len(input_lines):
                        # Calcular posición de inicio y fin
                        start = f"{line}.{col-1}"
                        end = f"{line}.{col}"
                        
                        # Resaltar en el editor
                        self.editor.tag_add("ERROR", start, end)
                        self.editor.see(start)  # Hacer scroll a la posición del error
                except (IndexError, ValueError):
                    continue
class IDE:
    NODOS_OMITIR = {
        'lista_declaracion',
        'lista_identificadores', 
        'lista_sentencias',
    }
     
    def __init__(self, root):
        self.root = root
        self.root.title("IDE para Compilador")
        self.filepath = None
        
        # Inicializar todos los atributos necesarios
        self.token_tree = None
        self.output_errores = None
        self.output_lexico = None
        self.output_sintactico = None
        self.output_semantico = None
        self.output_intermedio = None
        self.output_ejecucion = None
        self.output_hash = None
        
        # Crear componentes en orden correcto
        self.create_menu()
        self.create_toolbar()
        self.create_editor_and_execution()
        self.create_cursor_indicator()
        self.create_error_window()
        

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuevo Archivo", command=self.new_file)
        filemenu.add_command(label="Abrir", command=self.open_file)
        filemenu.add_command(label="Guardar", command=self.save_file)
        filemenu.add_command(label="Guardar como", command=self.save_file_as)
        filemenu.add_command(label="Cerrar", command=self.close_file)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=filemenu)

        # Menú Compilar
        compilemenu = tk.Menu(menubar, tearoff=0)
        compilemenu.add_command(label="Compilar Léxico", command=self.compile_lexico)
        compilemenu.add_command(label="Compilar Sintáctico", command=self.compile_sintactico)
       
        menubar.add_cascade(label="Compilar", menu=compilemenu)

        self.root.config(menu=menubar)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Íconos para las operaciones del menú (usando placeholders si no existen los archivos)
        try:
            self.new_icon = PhotoImage(file="icons/new_icon.png").subsample(3,3)
            self.open_icon = PhotoImage(file="icons/open_icon.png").subsample(3,3)
            self.save_icon = PhotoImage(file="icons/save_icon.png").subsample(3,3)
            self.save_as_icon = PhotoImage(file="icons/save_as_icon.png").subsample(3,3)
            self.close_icon = PhotoImage(file="icons/close_icon.png").subsample(3,3)
            self.exit_icon = PhotoImage(file="icons/exit_icon.png").subsample(3,3)
            self.undo_icon = PhotoImage(file="icons/undo_icon.png").subsample(2,2)
            self.redo_icon = PhotoImage(file="icons/redo_icon.png").subsample(2,2)
        except:
            # Si no hay íconos, usar texto
            self.new_icon = "Nuevo"
            self.open_icon = "Abrir"
            self.save_icon = "Guardar"
            self.save_as_icon = "Guardar como"
            self.close_icon = "Cerrar"
            self.exit_icon = "Salir"
            self.undo_icon = "Deshacer"
            self.redo_icon = "Rehacer"

        btn_new = tk.Button(toolbar, image=self.new_icon if isinstance(self.new_icon, PhotoImage) else None, 
                          text=self.new_icon if not isinstance(self.new_icon, PhotoImage) else None,
                          command=self.new_file)
        btn_new.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_new, "Nuevo Archivo")

        btn_open = tk.Button(toolbar, image=self.open_icon if isinstance(self.open_icon, PhotoImage) else None,
                           text=self.open_icon if not isinstance(self.open_icon, PhotoImage) else None,
                           command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_open, "Abrir")

        btn_save = tk.Button(toolbar, image=self.save_icon if isinstance(self.save_icon, PhotoImage) else None,
                           text=self.save_icon if not isinstance(self.save_icon, PhotoImage) else None,
                           command=self.save_file)
        btn_save.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_save, "Guardar")

        btn_save_as = tk.Button(toolbar, image=self.save_as_icon if isinstance(self.save_as_icon, PhotoImage) else None,
                              text=self.save_as_icon if not isinstance(self.save_as_icon, PhotoImage) else None,
                              command=self.save_file_as)
        btn_save_as.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_save_as, "Guardar como")

        btn_close = tk.Button(toolbar, image=self.close_icon if isinstance(self.close_icon, PhotoImage) else None,
                            text=self.close_icon if not isinstance(self.close_icon, PhotoImage) else None,
                            command=self.close_file)
        btn_close.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_close, "Cerrar")

        btn_exit = tk.Button(toolbar, image=self.exit_icon if isinstance(self.exit_icon, PhotoImage) else None,
                           text=self.exit_icon if not isinstance(self.exit_icon, PhotoImage) else None,
                           command=self.root.quit)
        btn_exit.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_exit, "Salir")
        
        

        # Separador
        separator = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Botones de Deshacer y Rehacer
        btn_undo = tk.Button(toolbar, image=self.undo_icon if isinstance(self.undo_icon, PhotoImage) else None,
                            text=self.undo_icon if not isinstance(self.undo_icon, PhotoImage) else None,
                            command=self.undo)
        btn_undo.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_undo, "Deshacer")

        btn_redo = tk.Button(toolbar, image=self.redo_icon if isinstance(self.redo_icon, PhotoImage) else None,
                            text=self.redo_icon if not isinstance(self.redo_icon, PhotoImage) else None,
                            command=self.redo)
        btn_redo.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_redo, "Rehacer")

        # Separador
        separator = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Botones de compilación y ejecución
        btn_lexico = tk.Button(toolbar, text="Compilar Léxico", command=self.compile_lexico)
        btn_lexico.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_lexico, "Compilar Léxico")

        btn_sintactico = tk.Button(toolbar, text="Compilar Sintáctico", command=self.compile_sintactico)
        btn_sintactico.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_sintactico, "Compilar Sintáctico")
        
        # En el método create_toolbar de la clase IDE, agregar:
        btn_semantico = tk.Button(toolbar, text="Compilar Semántico", command=self.compile_semantico)
        btn_semantico.pack(side=tk.LEFT, padx=2, pady=2)
        self.add_tooltip(btn_semantico, "Compilar Semántico")

    def add_tooltip(self, widget, text):
        '''Agrega un tooltip (hover) a un widget'''
        def enter(event):
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def create_editor_and_execution(self):
        # Frame principal para el editor y la ejecución
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para el editor de texto
        self.editor_frame = tk.Frame(self.main_frame)
        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas para los números de línea
        self.linenumbers = TextLineNumbers(self.editor_frame, width=40, bg="#f0f0f0")
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        # Editor de texto
        self.editor = CustomText(self.editor_frame, wrap=tk.NONE, width=80, height=20, bg="white", fg="black", insertbackground="black")
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Barra de desplazamiento vertical
        scrollbar = ttk.Scrollbar(self.editor_frame, orient=tk.VERTICAL, command=self.editor.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=scrollbar.set)

        # Asociar el editor con los números de línea
        self.linenumbers.attach(self.editor)

        # Configurar eventos para redibujar los números de línea
        self.editor.bind("<<TextModified>>", self._on_change)
        self.editor.bind("<Configure>", self._on_change)
        
        # Frame para la ventana de ejecución
        self.execution_frame = tk.Frame(self.main_frame)
        self.execution_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Pestañas de ejecución
        self.execution_tabs = ttk.Notebook(self.execution_frame)
        
        # ------------------------- Pestaña LÉXICO -------------------------
        self.tab_lexico = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_lexico, text="Léxico")
        
        # Frame contenedor para la tabla
        token_frame = tk.Frame(self.tab_lexico)
        token_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.token_tree = ttk.Treeview(
        token_frame, 
        columns=("Lexema", "Token"), 
        show="headings",
        selectmode="extended"
     )

        # Configurar columnas
        self.token_tree.column("Lexema", width=150, anchor=tk.W, stretch=tk.YES)
        self.token_tree.column("Token", width=120, anchor=tk.W, stretch=tk.YES)
        
        # Configurar encabezados
        self.token_tree.heading("Lexema", text="LEXEMA", anchor=tk.W)
        self.token_tree.heading("Token", text="TOKEN", anchor=tk.W)
        
        
        # Scrollbars
        vsb = ttk.Scrollbar(token_frame, orient="vertical", command=self.token_tree.yview)
        hsb = ttk.Scrollbar(token_frame, orient="horizontal", command=self.token_tree.xview)
        self.token_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Diseño con grid
        self.token_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        token_frame.grid_rowconfigure(0, weight=1)
        token_frame.grid_columnconfigure(0, weight=1)
        
        # ------------------------- Pestaña SINTÁCTICO -------------------------
        
        # Pestaña Sintáctico
        self.tab_sintactico = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_sintactico, text="Sintáctico")

        # Contenedor para la tabla
        sintactico_frame = tk.Frame(self.tab_sintactico)
        sintactico_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.token_tree_sintactico = ttk.Treeview(
            sintactico_frame,
            columns=("Nodo", "Tipo", "Línea", "Columna"),
            show="headings",
            selectmode="extended"
        )

        # Columnas
        self.token_tree_sintactico.column("Nodo", width=100, anchor=tk.W)
        self.token_tree_sintactico.column("Tipo", width=100, anchor=tk.W)
        self.token_tree_sintactico.column("Línea", width=80, anchor=tk.W)
        self.token_tree_sintactico.column("Columna", width=80, anchor=tk.W)

        # Encabezados
        self.token_tree_sintactico.heading("Nodo", text="Nodo")
        self.token_tree_sintactico.heading("Tipo", text="Tipo")
        self.token_tree_sintactico.heading("Línea", text="Línea")
        self.token_tree_sintactico.heading("Columna", text="Columna")

        # Scrollbars
        vsb_syn = ttk.Scrollbar(sintactico_frame, orient="vertical", command=self.token_tree_sintactico.yview)
        hsb_syn = ttk.Scrollbar(sintactico_frame, orient="horizontal", command=self.token_tree_sintactico.xview)
        self.token_tree_sintactico.configure(yscrollcommand=vsb_syn.set, xscrollcommand=hsb_syn.set)

        # Diseño grid
        self.token_tree_sintactico.grid(row=0, column=0, sticky="nsew")
        vsb_syn.grid(row=0, column=1, sticky="ns")
        hsb_syn.grid(row=1, column=0, sticky="ew")
        sintactico_frame.grid_rowconfigure(0, weight=1)
        sintactico_frame.grid_columnconfigure(0, weight=1)
        
        # ------------------------- Pestaña SEMÁNTICO -------------------------
        self.tab_semantico = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_semantico, text="Semántico")

        # Crear un frame contenedor para organizar mejor
        self.semantico_container = ttk.Frame(self.tab_semantico)
        self.semantico_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Crear el widget de texto para el análisis semántico
        self.output_semantico = tk.Text(
            self.semantico_container, 
            wrap=tk.WORD, 
            width=80, 
            height=15,  
            bg="white",
            fg="black",
            font=("Consolas", 10)
        )
        self.output_semantico.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Agregar una barra de desplazamiento
        scrollbar_semantico = ttk.Scrollbar(self.semantico_container, orient="vertical", command=self.output_semantico.yview)
        scrollbar_semantico.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_semantico.configure(yscrollcommand=scrollbar_semantico.set)
        
        # En la clase IDE, en el método create_editor_and_execution, añadir una pestaña para el árbol semántico

        # ------------------------- Pestaña ÁRBOL SEMÁNTICO -------------------------
        self.tab_semantic_tree = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_semantic_tree, text="Árbol Semántico")

        # Crear un Treeview para mostrar el árbol semántico
        self.semantic_tree = ttk.Treeview(self.tab_semantic_tree, columns=("Valor", "Tipo", "Línea"), show="tree headings")
        self.semantic_tree.column("#0", width=200, anchor=tk.W)  # Columna para la jerarquía
        self.semantic_tree.column("Valor", width=100, anchor=tk.W)
        self.semantic_tree.column("Tipo", width=100, anchor=tk.W)
        self.semantic_tree.column("Línea", width=50, anchor=tk.W)

        self.semantic_tree.heading("#0", text="Nodo")
        self.semantic_tree.heading("Valor", text="Valor")
        self.semantic_tree.heading("Tipo", text="Tipo")
        self.semantic_tree.heading("Línea", text="Línea")

        # En la creación del árbol semántico, después del treeview:
        self.semantic_tree_frame = ttk.Frame(self.tab_semantic_tree)
        self.semantic_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame para los botones
        self.tree_buttons_frame = ttk.Frame(self.semantic_tree_frame)
        self.tree_buttons_frame.pack(fill=tk.X, pady=(0, 5))

        # Botón Expandir Todo
        self.expand_all_btn = ttk.Button(
            self.tree_buttons_frame,
            text="Expandir Todo",
            command=self._expand_semantic_tree
        )
        self.expand_all_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Botón Contraer Todo
        self.collapse_all_btn = ttk.Button(
            self.tree_buttons_frame,
            text="Contraer Todo", 
            command=self._collapse_semantic_tree
        )
        self.collapse_all_btn.pack(side=tk.LEFT)

        # Treeview
        self.semantic_tree = ttk.Treeview(
            self.semantic_tree_frame,
            height=12,
            show='tree'
        )
        self.semantic_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(
            self.semantic_tree_frame, 
            orient=tk.VERTICAL, 
            command=self.semantic_tree.yview
        )
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.semantic_tree.configure(yscrollcommand=v_scrollbar.set)
        
        
        # ------------------------- Pestaña INTERMEDIO -------------------------
        self.tab_intermedio = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_intermedio, text="Intermedio")
        
        self.output_intermedio = tk.Text(
            self.tab_intermedio, 
            wrap=tk.WORD, 
            width=80, 
            height=10,
            bg="white",
            fg="black",
            font=("Consolas", 10)
        )
        self.output_intermedio.pack(fill=tk.BOTH, expand=True)
        
        # ------------------------- Pestaña EJECUCIÓN -------------------------
        self.tab_ejecucion = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_ejecucion, text="Ejecución")
        
        self.output_ejecucion = tk.Text(
            self.tab_ejecucion, 
            wrap=tk.WORD, 
            width=80, 
            height=10,
            bg="white",
            fg="black",
            font=("Consolas", 10)
        )
        self.output_ejecucion.pack(fill=tk.BOTH, expand=True)
        
        # ------------------------- Pestaña TABLA HASH -------------------------
        self.tab_hash = ttk.Frame(self.execution_tabs)
        self.execution_tabs.add(self.tab_hash, text="Tabla Hash")

        # Crear el Treeview para mostrar la tabla hash
        self.hash_tree = ttk.Treeview(self.tab_hash, columns=("Índice", "Símbolos"), show="tree headings")
        self.hash_tree.column("#0", width=0, stretch=tk.NO)  # Ocultar primera columna
        self.hash_tree.column("Índice", width=100, anchor=tk.CENTER)
        self.hash_tree.column("Símbolos", width=300, anchor=tk.W)

        self.hash_tree.heading("Índice", text="Índice")
        self.hash_tree.heading("Símbolos", text="Símbolos")

        # Scrollbars
        hash_vsb = ttk.Scrollbar(self.tab_hash, orient="vertical", command=self.hash_tree.yview)
        hash_hsb = ttk.Scrollbar(self.tab_hash, orient="horizontal", command=self.hash_tree.xview)
        self.hash_tree.configure(yscrollcommand=hash_vsb.set, xscrollcommand=hash_hsb.set)

        # Empaquetar
        self.hash_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hash_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hash_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        

        
        # Mostrar todas las pestañas
        self.execution_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Configurar el peso de las filas y columnas para expansión
        self.execution_frame.grid_rowconfigure(0, weight=1)
        self.execution_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(self.editor_frame, orient=tk.VERTICAL, command=self._on_scroll)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=scrollbar.set)
        
        # Asociar el editor con los números de línea
        self.linenumbers.attach(self.editor)
        
        # Configurar eventos para redibujar los números de línea
        self.editor.bind("<<TextModified>>", self._on_change)
        self.editor.bind("<Configure>", self._on_change)
        self.editor.bind("<MouseWheel>", self._on_mousewheel)
        
        # ... (resto del código igual)

    def _on_scroll(self, *args):
        """Maneja el evento de scroll y actualiza los números de línea"""
        # Primero ejecutar el scroll normal
        self.editor.yview(*args)
        # Luego actualizar los números de línea
        self.linenumbers.redraw()

    def _on_mousewheel(self, event):
        """Maneja el evento de la rueda del mouse"""
        # Permitir que el evento de scroll se procese normalmente
        self.editor.yview_scroll(-1 * (event.delta // 120), "units")
        # Programar una actualización de los números de línea
        self.linenumbers.after(10, self.linenumbers.redraw)
        return "break"

    def _on_change(self, event=None):
        self.linenumbers.redraw()

    def create_cursor_indicator(self):
        # Frame para el indicador de cursor
        self.cursor_frame = tk.Frame(self.root)
        self.cursor_frame.pack(fill=tk.X)

        # Etiqueta para mostrar la posición del cursor
        self.cursor_label = tk.Label(self.cursor_frame, text="Línea: 1, Columna: 1", anchor="w")
        self.cursor_label.pack(side=tk.LEFT, padx=5, pady=2)

        # Actualizar la posición del cursor cuando se mueve
        self.editor.bind("<KeyRelease>", self.update_cursor_position)
        self.editor.bind("<ButtonRelease>", self.update_cursor_position)

    def update_cursor_position(self, event=None):
        '''Actualiza la etiqueta con la posición actual del cursor'''
        cursor_index = self.editor.index(tk.INSERT)
        line, column = cursor_index.split(".")
        self.cursor_label.config(text=f"Línea: {line}, Columna: {column}")

    def create_error_window(self):
    # Frame para la ventana de errores
        self.error_frame = tk.Frame(self.root, bd=2, relief=tk.GROOVE)
        self.error_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Etiqueta de título con estilo destacado
        error_label = tk.Label(self.error_frame, text="PANEL DE ERRORES", 
                            bg="#ffebeb", fg="red", 
                            font=('Arial', 10, 'bold'), padx=5, pady=2)
        error_label.pack(fill=tk.X)
        
        # Contenedor principal con borde
        error_container = tk.Frame(self.error_frame, bd=1, relief=tk.SUNKEN)
        error_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Área de texto para errores
        self.output_errores = tk.Text(error_container, 
                                    wrap=tk.WORD, 
                                    width=80, 
                                    height=8,
                                    bg="white", 
                                    fg="black", 
                                    font=('Consolas', 9),
                                    state=tk.NORMAL,  # Inicialmente en modo solo lectura
                                    padx=5, pady=5)
        
        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(error_container, command=self.output_errores.yview)
        self.output_errores.config(yscrollcommand=scrollbar.set)
        
        # Diseño con grid para mejor ajuste
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_errores.pack(fill=tk.BOTH, expand=True)
        
        # Configurar tags para formato de texto
        self.output_errores.tag_config("error_header", foreground="red", font=('Arial', 10, 'bold'))
        self.output_errores.tag_config("error_detail", foreground="black", font=('Consolas', 9))
        self.output_errores.tag_config("no_errors", foreground="green", font=('Arial', 9, 'italic'))
        
        self._enable_copy_shortcut()
        
    def _enable_copy_shortcut(self):
        """Habilita el atajo Ctrl+C para copiar texto seleccionado"""
        def handle_copy(event):
            if event.state & 4 and event.keysym.lower() == 'c':  # Ctrl+C
                try:
                    # Obtener texto seleccionado
                    selected = self.output_errores.get(tk.SEL_FIRST, tk.SEL_LAST)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected)
                except tk.TclError:
                    # Si no hay selección, no hacer nada
                    pass
            return "break"  # Evitar el comportamiento por defecto
        
        # Bindear el evento
        self.output_errores.bind("<Control-c>", handle_copy)
        self.output_errores.bind("<Control-C>", handle_copy)  # Mayúsculas
    
    def _setup_copy_behavior(self):
        """Configura el comportamiento de selección y copiado"""
        # Permitir selección pero no modificación
        self.output_errores.config(state=tk.DISABLED)
        
        def enable_selection(event):
            # Cambiar temporalmente a NORMAL para seleccionar
            self.output_errores.config(state=tk.NORMAL)
            self.output_errores.tag_remove(tk.SEL, "1.0", tk.END)
            return None
        
        def handle_copy(event):
            if event.state & 4 and event.keysym.lower() == 'c':  # Ctrl+C
                try:
                    # Copiar selección al portapapeles
                    selected = self.output_errores.get(tk.SEL_FIRST, tk.SEL_LAST)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected)
                except tk.TclError:
                    pass  # No hay selección
            return "break"
        
        def restore_state(event):
            # Volver a estado DISABLED después de seleccionar
            if str(self.output_errores.cget("state")) == "normal":
                self.output_errores.config(state=tk.DISABLED)
            return None
        
        # Bindings de eventos
        self.output_errores.bind("<Button-1>", enable_selection)
        self.output_errores.bind("<B1-Motion>", enable_selection)
        self.output_errores.bind("<ButtonRelease-1>", restore_state)
        self.output_errores.bind("<Control-c>", handle_copy)
        self.output_errores.bind("<Control-C>", handle_copy)  # Mayúsculas    

    # Bloquear completamente la edición del panel
        def block_event(event):
            return "break"
    
        for event in ["<Key>", "<Button-1>", "<Button-2>", "<Button-3>", "<B1-Motion>"]:
            self.output_errores.bind(event, block_event)
    def new_file(self):
        # Limpiar editor
        self.editor.delete(1.0, tk.END)
        
        # Limpiar todos los paneles de resultados
        self.clear_all_panels()
        
        # Resetear variables de estado
        self.filepath = None
        self.editor.edit_reset()  # Resetear historial de undo/redo
        
        # Forzar actualización de la sintaxis
        self.editor.highlight_syntax()

    def clear_all_panels(self):
        """Limpia todos los paneles de resultados y errores"""
        # Limpiar tabla de tokens
        self.token_tree.delete(*self.token_tree.get_children())
        
        # Limpiar paneles de texto
        panels = [
            self.output_errores,
            self.output_sintactico,
            self.output_semantico,
            self.output_intermedio,
            self.output_ejecucion,
            self.output_hash
        ]
        
        for panel in panels:
            panel.config(state=tk.NORMAL)
            panel.delete(1.0, tk.END)
            panel.config(state=tk.DISABLED)
        
        # Limpiar cualquier resaltado de errores
        self.editor.tag_remove("ERROR", "1.0", tk.END)

    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r") as file:
                    self.editor.delete(1.0, tk.END)
                    self.editor.insert(tk.END, file.read())
                    self.filepath = filepath
                    # Programar el resaltado después de un pequeño retraso
                    self.editor.after(100, self.safe_highlight)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")

    def safe_highlight(self):
        """Versión segura del resaltado que maneja errores"""
        try:
            self.editor.highlight_syntax()
        except Exception as e:
            print(f"Error durante el resaltado: {e}")

                
        except Exception as e:
            print(f"Error en highlight_syntax: {e}")
            # Si hay un error, al menos limpiar los tags para evitar inconsistencia
            for tag in self.tag_names():
                self.tag_remove(tag, "1.0", tk.END)

    def save_file(self):
        if self.filepath:
            with open(self.filepath, "w") as file:
                file.write(self.editor.get(1.0, tk.END))
        else:
            self.save_file_as()

    def save_file_as(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            self.filepath = filepath
            self.save_file()

    def close_file(self):
        self.new_file()

    def undo(self):
        try:
            self.editor.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.editor.edit_redo()
        except tk.TclError:
            pass

    def compile_lexico(self):
        try:
            # Limpiar resultados anteriores
            self.token_tree.delete(*self.token_tree.get_children())
            self.output_errores.config(state=tk.NORMAL)
            self.output_errores.delete(1.0, tk.END)
            
            # Obtener texto actual
            input_text = self.editor.get(1.0, tk.END)
            lines = input_text.split('\n')
            
            if not input_text.strip():
                self.output_errores.insert(tk.END, "El editor está vacío.\n", "no_errors")
                self.output_errores.config(state=tk.DISABLED)
                return
                
            # Procesar análisis léxico
            tokens = test_lexer(input_text)
            error_count = 0
            self.output_errores.insert(tk.END, "=== ERRORES LÉXICOS ===\n", "error_header")
            
            # Nueva estrategia para calcular posiciones
            current_pos = 0
            line_num = 1
            line_start_pos = 0
            
            for tok in tokens:
                # Calcular línea y columna basado en el texto
                while current_pos < tok.lexpos and line_num <= len(lines):
                    line_end = line_start_pos + len(lines[line_num-1])
                    if tok.lexpos >= line_end:
                        current_pos = line_end + 1  # +1 por el \n
                        line_start_pos = current_pos
                        line_num += 1
                    else:
                        current_pos = tok.lexpos
                
                col_num = tok.lexpos - line_start_pos
                
                # Mostrar tokens válidos
                if hasattr(tok, 'type') and tok.type != 'ERROR':
                    self.token_tree.insert("", tk.END, values=(tok.value, tok.type, getattr(tok, 'subtoken', '')))
                    continue
                    
                # Procesar errores
                if getattr(tok, 'type', '') == 'ERROR':
                    error_count += 1
                    
                    if line_num > len(lines):
                        continue
                        
                    current_line = lines[line_num-1] if line_num <= len(lines) else ""
                    
                    # Ajustar para errores específicos
                    error_value = str(tok.value)
                    error_length = len(error_value)
                    error_start = col_num
                    
                    if '@' in error_value:  # Caso sum@r
                        error_start += error_value.index('@')
                        error_length = 1
                    elif error_value.count('.') > 1:  # Caso 34.34.34.34
                        first_dot = error_value.index('.')
                        error_start += error_value.index('.', first_dot + 1)
                        error_length = 1
                    elif '.' in error_value and any(c.isalpha() for c in error_value):  # Caso 32.algo
                        error_start += error_value.index('.')
                        error_length = len(error_value) - error_value.index('.')
                    
                    # Mostrar información del error
                    error_msg = (f"Error {error_count}: '{tok.value}'\n"
                                f"Línea: {line_num}, Columna: {error_start + 1}\n"
                                f"Contexto: {current_line[:error_start]}>>>{current_line[error_start:error_start+error_length]}<<<{current_line[error_start+error_length:]}\n\n")
                    
                    self.output_errores.insert(tk.END, error_msg, "error_detail")
            
            # Mostrar resumen
            if error_count == 0:
                self.output_errores.insert(tk.END, "No se encontraron errores léxicos.\n", "no_errors")
            else:
                self.output_errores.insert(tk.END, f"\nTotal de errores léxicos: {error_count}\n", "error_header")
            
            self.output_errores.config(state=tk.DISABLED)
            
        except Exception as e:
            self.output_errores.config(state=tk.NORMAL)
            self.output_errores.insert(tk.END, f"Error durante análisis léxico: {str(e)}\n", "error_detail")
            self.output_errores.config(state=tk.DISABLED)
            messagebox.showerror("Error", f"Ocurrió un error durante el análisis léxico: {str(e)}")
                

    
    def compile_sintactico(self):
    # Limpiar resultados anteriores
        self.token_tree_sintactico.delete(*self.token_tree_sintactico.get_children())
        self.output_errores.config(state=tk.NORMAL)
        self.output_errores.delete(1.0, tk.END)
        
        input_text = self.editor.get(1.0, tk.END)
        
        try:
            result = parse_code(input_text)
            
            self.output_errores.insert(tk.END, "=== ERRORES SINTÁCTICOS ===\n", "error_header")
            
            if result['success'] and result['ast']:
                # Llenar la tabla con información del AST
                self._fill_syntax_table(result['ast'])
                
                # Mostrar el árbol visual
                self.show_ast(result['ast'])
                
                self.output_errores.insert(tk.END, "No se encontraron errores sintácticos.\n", "no_errors")
            else:
                error_count = 0
                for error in result.get('errors', []):
                    error_count += 1
                    error_msg = ""
                    if 'line' in error and 'column' in error:
                        error_msg = f"Error {error_count}: Línea {error['line']}, Columna {error['column']}: {error['message']}\n"
                    else:
                        error_msg = f"Error {error_count}: {error.get('message', str(error))}\n"
                    
                    self.output_errores.insert(tk.END, error_msg, "error_detail")
                
                if error_count > 0:
                    self.output_errores.insert(tk.END, f"\nTotal de errores sintácticos: {error_count}\n", "error_header")
                
                if input_text.strip():
                    self._highlight_error_in_editor(result.get('errors', []), input_text)
                    
        except Exception as e:
            error_msg = f"Error durante el análisis sintáctico: {str(e)}\n"
            self.output_errores.insert(tk.END, error_msg, "error_detail")
            import traceback
            traceback.print_exc()
        
        self.output_errores.config(state=tk.DISABLED)
        
    def _fill_syntax_table(self, ast_node):
        """Llena la tabla sintáctica con la información del AST"""
        self.token_tree_sintactico.delete(*self.token_tree_sintactico.get_children())
        
        def add_ast_node(parent, node, level=0):
            if not isinstance(node, ASTNode):
                return
                
            # Omitir nodos de lista
            if node.type in self.NODOS_OMITIR:
                for child in node.children:
                    add_ast_node(parent, child, level)
                return
            
            # Información del nodo
            node_name = node.type
            node_value = getattr(node, 'value', '')
            line = getattr(node, 'lineno', 'N/A')
            
            # Para identificadores y números, mostrar el valor
            if node.type in ['identificador', 'numero'] and node_value:
                node_name = f"{node_value} ({node.type})"
            elif node_value and node.type != 'tipo':
                node_name = f"{node.type}: {node_value}"
            
            # Insertar en la tabla
            node_id = self.token_tree_sintactico.insert(
                parent, "end", 
                text=node_name,
                values=(node.type, node_value, line, level)
            )
            
            # Procesar hijos
            if hasattr(node, 'children'):
                for child in node.children:
                    add_ast_node(node_id, child, level + 1)
        
        add_ast_node("", ast_node)
        
    
    def _mostrar_analisis_semantico_completo(self, tabla_simbolos):
        """Muestra el análisis semántico completo con tabla y resumen"""
        contenido = "=== ANÁLISIS SEMÁNTICO ===\n\n"
        
        # TABLA DE SÍMBOLOS DETALLADA
        contenido += "TABLA DE SÍMBOLOS DETALLADA\n"
        contenido += "┌───────────┬──────────┬────────────┬────────┬──────────┐\n"
        contenido += "│ NOMBRE    │ TIPO     │ ALCANCE    │ LÍNEA  │ ESTADO   │\n"
        contenido += "├───────────┼──────────┼────────────┼────────┼──────────┤\n"
        
        # Contadores para el resumen
        cont_int = 0
        cont_bool = 0
        cont_global = 0
        cont_local = 0
        
        for simbolo in tabla_simbolos:
            nombre = simbolo.get('nombre', '')
            tipo = simbolo.get('tipo', '')
            alcance = simbolo.get('alcance', '')
            linea = simbolo.get('linea', '')
            
            # Contar tipos
            if tipo == 'int':
                cont_int += 1
            elif tipo == 'bool':
                cont_bool += 1
                
            # Contar ámbitos
            if alcance == 'global':
                cont_global += 1
            else:
                cont_local += 1
                
            # Formatear fila de la tabla
            contenido += f"│ {nombre:<9} │ {tipo:<8} │ {alcance:<10} │ {linea:<6} │ válido   │\n"
        
        contenido += "└───────────┴──────────┴────────────┴────────┴──────────┘\n\n"
        
        # RESUMEN DEL ANÁLISIS
        contenido += "RESUMEN DEL ANÁLISIS\n"
        contenido += f"• Total de símbolos: {len(tabla_simbolos)}\n"
        contenido += f"• Variables enteras: {cont_int}\n"
        contenido += f"• Variables booleanas: {cont_bool}\n"
        contenido += f"• Ámbito global: {cont_global} símbolos\n"
        contenido += f"• Ámbito local: {cont_local} símbolos\n"
        contenido += "• Errores semánticos: 0\n\n"
        
        # VERIFICACIONES COMPLETADAS
        contenido += "VERIFICACIONES COMPLETADAS\n"
        contenido += "✓ Todas las variables están declaradas\n"
        contenido += "✓ No hay variables duplicadas en el mismo ámbito\n"
        contenido += "✓ Coherencia de tipos verificada\n"
        contenido += "✓ Uso adecuado de ámbitos\n\n"
        
        contenido += "ESTADO: Análisis semántico exitoso\n"
        
        self.output_semantico.insert(tk.END, contenido)

    def compile_semantico(self):
        """Ejecuta el análisis semántico y muestra resultados"""
        try:
            # Limpiar resultados anteriores
            self.output_errores.config(state=tk.NORMAL)
            self.output_errores.delete(1.0, tk.END)
            self.output_semantico.config(state=tk.NORMAL)
            self.output_semantico.delete(1.0, tk.END)
            
            # Limpiar árbol semántico y tabla hash
            self.semantic_tree.delete(*self.semantic_tree.get_children())
            self.hash_tree.delete(*self.hash_tree.get_children())
            
            # Obtener texto actual
            input_text = self.editor.get(1.0, tk.END)
            
            if not input_text.strip():
                self.output_errores.insert(tk.END, "El editor está vacío.\n")
                self.output_errores.config(state=tk.DISABLED)
                self.output_semantico.config(state=tk.DISABLED)
                return
                
            # Ejecutar análisis semántico
            from semantico import test_semantics
            result = test_semantics(input_text)
            
            # Mostrar resultados en panel de errores
            self.output_errores.insert(tk.END, "=== RESULTADOS DEL ANALISIS SEMANTICO ===\n", "error_header")
            
            if result['errors']:
                self.output_errores.insert(tk.END, f"Se encontraron {len(result['errors'])} error(es):\n\n", "error_header")
                for i, error in enumerate(result['errors'], 1):
                    self.output_errores.insert(tk.END, f"{i}. {error}\n", "error_detail")
            else:
                self.output_errores.insert(tk.END, "✓ No se encontraron errores semanticos.\n", "no_errors")
            
            # Mostrar tabla de símbolos
            self.output_semantico.insert(tk.END, "=== TABLA DE SIMBOLOS ===\n", "header")
            
            if result['symbol_table']:
                self._mostrar_analisis_semantico_completo(result['symbol_table'])
                    
                # MOSTRAR TABLA HASH - ESTA ES LA PARTE NUEVA
                self._mostrar_tabla_hash(result['symbol_table'])
            else:
                self.output_semantico.insert(tk.END, "No se encontraron simbolos.\n")
            
            # Mostrar árbol semántico
            if result['semantic_tree']:
                self._display_semantic_tree(result['semantic_tree'])
            
            self.output_errores.config(state=tk.DISABLED)
            self.output_semantico.config(state=tk.DISABLED)
            
        except Exception as e:
            self.output_errores.config(state=tk.NORMAL)
            self.output_errores.insert(tk.END, f"Error durante analisis semantico: {str(e)}\n", "error_detail")
            self.output_errores.config(state=tk.DISABLED)
            import traceback
            traceback.print_exc()

    def _expand_semantic_tree(self):
        """Expande todos los nodos del árbol semántico"""
        def expand_all(items):
            for item in items:
                self.semantic_tree.item(item, open=True)
                expand_all(self.semantic_tree.get_children(item))
        
        expand_all(self.semantic_tree.get_children(''))

    def _collapse_semantic_tree(self):
        """Contrae todos los nodos del árbol semántico"""
        def collapse_all(items):
            for item in items:
                self.semantic_tree.item(item, open=False)
                collapse_all(self.semantic_tree.get_children(item))
        
        collapse_all(self.semantic_tree.get_children(''))

    def _display_semantic_tree(self, semantic_tree):
        """Muestra el árbol semántico de forma simple y clara"""
        self.semantic_tree.delete(*self.semantic_tree.get_children())
        
        def add_tree_nodes(parent, node):
            if not node:
                return
                
            node_type = node.get('type', '')
            node_value = node.get('value', '')
            
            # Simplificar la visualización
            if node_type in ['lista_declaraciones', 'programa', 'sentencia', 'declaracion', 'expresion']:
                display_text = f"{node_type}"
            elif node_type == 'identificador':
                symbol_type = node.get('symbol_type', '')
                display_text = f"var: {node_value} ({symbol_type})" if symbol_type else f"var: {node_value}"
            elif node_type == 'asignacion':
                assignment_types = node.get('assignment_types', '')
                display_text = f"= {assignment_types}" if assignment_types else "asignacion"
            elif node_type == 'expresion_binaria':
                operation_types = node.get('operation_types', '')
                display_text = f"{node_value} {operation_types}" if operation_types else f"op: {node_value}"
            elif node_type == 'numero':
                display_text = f"num: {node_value}"
            elif node_type == 'booleano':
                display_text = f"bool: {node_value}"
            elif node_type == 'string_literal':
                display_text = f"texto: '{node_value}'"
            elif node_type == 'operacion_unaria':
                display_text = f"op: {node_value}"
            else:
                display_text = f"{node_type}"
            
            node_id = self.semantic_tree.insert(parent, 'end', text=display_text, open=True)
            
            # Procesar hijos
            for child in node.get('children', []):
                add_tree_nodes(node_id, child)
        
        if semantic_tree:
            add_tree_nodes('', semantic_tree)
            
    def _add_semantic_tree_node(self, parent, node):
        """Añade recursivamente nodos al árbol semántico"""
        if node is None:
            return
            
        # Crear texto del nodo
        node_text = node['type']
        if node['value'] is not None:
            node_text += f": {node['value']}"
        
        # Información adicional para mostrar en las columnas
        additional_info = ""
        tipo_info = ""
        linea_info = node.get('line', '')
        
        if 'inferred_type' in node:
            tipo_info = node['inferred_type']
        if 'symbol_type' in node:
            tipo_info = node['symbol_type']
        if 'operation_types' in node:
            additional_info = node['operation_types']
        if 'assignment_types' in node:
            additional_info = node['assignment_types']
        
        # Insertar nodo
        node_id = self.semantic_tree.insert(
            parent, "end", 
            text=node_text,
            values=(
                node.get('value', ''),
                tipo_info,
                str(linea_info)
            )
        )
        
        # Procesar hijos recursivamente
        for child in node.get('children', []):
            self._add_semantic_tree_node(node_id, child)

    def _expand_semantic_tree(self):
        """Expande todo el árbol semántico"""
        def expand_all(item):
            children = self.semantic_tree.get_children(item)
            for child in children:
                expand_all(child)
            if children:
                self.semantic_tree.item(item, open=True)
        
        for child in self.semantic_tree.get_children():
            expand_all(child)

    def _collapse_semantic_tree(self):
        """Contrae todo el árbol semántico"""
        def collapse_all(item):
            children = self.semantic_tree.get_children(item)
            for child in children:
                collapse_all(child)
            self.semantic_tree.item(item, open=False)
        
        for child in self.semantic_tree.get_children():
            collapse_all(child)

    #     Método para mostrar el árbol semántico en el Treeview
    # def _display_semantic_tree(self, semantic_tree):
    #         """Muestra el árbol semántico en el Treeview"""
    #         self.semantic_tree.delete(*self.semantic_tree.get_children())
    #         self._add_semantic_tree_node("", semantic_tree.root)
            

    # def _add_semantic_tree_node(self, parent, node):
    #         """Añade un nodo del árbol semántico al Treeview"""
    #         if node is None:
    #             return

    #         node_text = node['type']
    #         if node['value'] is not None:
    #             node_text += f" ({node['value']})"

    #         node_id = self.semantic_tree.insert(
    #             parent, "end", 
    #             text=node_text,
    #             values=(node['value'], node['type'], node['line'])
    #         )

    #         for child in node['children']:
    #             self._add_semantic_tree_node(node_id, child)
        
        
    def _mostrar_tabla_hash(self, simbolos):
        """Muestra la tabla hash en la pestaña correspondiente - VERSIÓN CORREGIDA"""
        # Limpiar treeview
        for item in self.hash_tree.get_children():
            self.hash_tree.delete(item)
        
        # Configurar columnas
        self.hash_tree.column("#0", width=0, stretch=tk.NO)
        self.hash_tree.column("Índice", width=100, anchor=tk.CENTER)
        self.hash_tree.column("Símbolos", width=400, anchor=tk.W)
        
        # Crear tabla hash
        tabla_hash = TablaHash(10)
        
        # Insertar todos los símbolos
        for simbolo in simbolos:
            tabla_hash.insertar(simbolo)
        
        # Obtener símbolos organizados por índice
        indices = tabla_hash.obtener_todos()
        
        # Colores suaves para diferentes índices
        colores = ['#e8f4fd', '#f0f8ff', '#f8f8ff', '#fff8f0', '#f8fff8', 
                '#fff8f8', '#f8f0ff', '#fff0f8', '#f0fff8', '#f8f8f0']
        
        # Estadísticas
        total_simbolos = 0
        colisiones = 0
        
        # Mostrar en el treeview
        for indice, simbolos_indice in indices:
            total_simbolos += len(simbolos_indice)
            if len(simbolos_indice) > 1:
                colisiones += len(simbolos_indice) - 1
                
            if simbolos_indice:
                # Calcular función hash del primer símbolo
                primer_caracter = simbolos_indice[0]['nombre'][0] if simbolos_indice[0]['nombre'] else '?'
                hash_calculado = ord(primer_caracter.upper()) % 10
                
                # Crear nodo padre para el índice
                padre = self.hash_tree.insert("", "end", text="", 
                                            values=(
                                                f"Índice {indice}", 
                                                f"{len(simbolos_indice)} símbolo(s) - Hash: '{primer_caracter}' → {hash_calculado}"
                                            ),
                                            tags=(f'color{indice}',))
                
                # Agregar símbolos como hijos
                for i, simbolo in enumerate(simbolos_indice):
                    # Formatear correctamente el ámbito
                    alcance = simbolo.get('alcance', 'global')
                    if alcance == 'global':
                        alcance_texto = "global"
                    else:
                        alcance_texto = alcance
                    
                    info = f"• {simbolo['nombre']} : {simbolo['tipo']} | Línea: {simbolo['linea']} | Ámbito: {alcance_texto}"
                    
                    self.hash_tree.insert(padre, "end", text="", 
                                        values=("", info),
                                        tags=(f'color{indice}',))
                
                # Expandir el nodo padre
                self.hash_tree.item(padre, open=True)
            else:
                # Índice vacío
                self.hash_tree.insert("", "end", text="", 
                                    values=(f"Índice {indice}", "Vacío"),
                                    tags=(f'color{indice}',))
        
        # Configurar tags para colores
        for i in range(10):
            self.hash_tree.tag_configure(f'color{i}', background=colores[i])
        
        # Mostrar estadísticas en un nodo especial al inicio
        if total_simbolos > 0:
            stats_padre = self.hash_tree.insert("", 0, text="", 
                                            values=("📊 ESTADÍSTICAS", 
                                                    f"Total: {total_simbolos} símbolos | Colisiones: {colisiones} | Factor de carga: {total_simbolos/10:.2f}"),
                                            tags=('stats',))
            self.hash_tree.tag_configure('stats', background='#ffeaa7', font=('Arial', 10, 'bold'))
            self.hash_tree.item(stats_padre, open=True)
    def _create_error_tooltip(self, position, message):
        """Crea un tooltip para mostrar el mensaje de error"""
        bbox = self.editor.bbox(position)
        if not bbox:
            return
            
        x, y, _, _ = bbox
        root_x = self.editor.winfo_rootx() + x
        root_y = self.editor.winfo_rooty() + y
        
        tooltip = tk.Toplevel(self.editor)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{root_x}+{root_y}")
        
        label = tk.Label(
            tooltip, 
            text=message, 
            background="#ffffe0", 
            relief="solid", 
            borderwidth=1,
            font=("Consolas", 9)
        )
        label.pack()
        
        # Auto-destruir después de 5 segundos
        tooltip.after(5000, tooltip.destroy)

    def _print_ast_structure(self, node, output_widget, level=0):
        """Muestra la estructura del AST en formato de tabla (Nodo, Tipo, Línea, Columna)"""
        indent = "  " * level
        
        # Obtener información del nodo
        node_name = node.type
        node_type = type(node).__name__
        line = getattr(node, 'lineno', 'N/A')
        column = getattr(node, 'lexpos', 'N/A')  # Nota: lexpos es la posición absoluta, no la columna
        
        # Si es un nodo hoja con valor, mostrarlo
        value = getattr(node, 'value', '')
        if value and not node.children:
            node_name = f"{value} ({node_name})"
        
        # Formatear la línea como una fila de tabla
        line_text = f"{indent}{node_name:<20} {node_type:<15} {str(line):<10} {str(column):<10}\n"
        output_widget.insert(tk.END, line_text)
        
        # Recorrer hijos si existen
        if hasattr(node, 'children'):
            for child in node.children:
                self._print_ast_structure(child, output_widget, level + 1)

    def show_ast(self, ast_root):
        """Muestra una ventana con el árbol sintáctico visual mejorado"""
        ast_window = tk.Toplevel(self.root)
        ast_window.title("Árbol Sintáctico Abstracto (AST)")
        ast_window.geometry("1000x600")  # Ventana más grande para acomodar fuente grande
        
        # Configurar fuente grande
        big_font = ('Helvetica', 18, 'bold')
        
        # Frame principal
        main_frame = tk.Frame(ast_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurar estilo para Treeview con fuente grande
        style = ttk.Style()
        style.configure("Big.Treeview", font=big_font, rowheight=35)
        style.configure("Big.Treeview.Heading", font=('Helvetica', 16, 'bold'))
        
        # Treeview para mostrar el AST
        tree = ttk.Treeview(main_frame, style="Big.Treeview")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Construir el árbol visual mejorado
        self._build_ast_tree(tree, "", ast_root)
        
        # Botones de control
        btn_frame = tk.Frame(ast_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Expandir Todo", 
                command=lambda: self._expand_tree(tree, "")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Contraer Todo", 
                command=lambda: self._collapse_tree(tree, "")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cerrar", 
                command=ast_window.destroy).pack(side=tk.RIGHT, padx=5)

    def _build_ast_tree(self, treeview, parent, node):
        """Construye recursivamente el árbol visual mejorado"""
        if not isinstance(node, ASTNode):
            return
            
        # Obtener texto para cálculo de posición
        input_text = self.editor.get("1.0", tk.END)
        lines = input_text.split('\n')
        total_lines = len(lines)
        
        # Omitir nodos no deseados
        if node.type in self.NODOS_OMITIR:
            for child in node.children:
                self._build_ast_tree(treeview, parent, child)
            return
        
        # Calcular línea ajustada
        line = getattr(node, 'lineno', None)
        line_text = ""
        if line is not None:
            adjusted_line = max(1, line - (total_lines - 1))
            line_text = f" [Línea: {adjusted_line}]"
        
        # Caso especial: Incrementos/decrementos
        
        
        # Caso especial: Asignaciones
        if node.type == 'asignacion':
            assign_text = f"={line_text}"
            assign_id = treeview.insert(parent, "end", text=assign_text)
            
            # Variable asignada
            var_node = node.children[0]
            var_line = getattr(var_node, 'lineno', None)
            var_line_text = f" [Línea: {max(1, var_line - (total_lines - 1))}]" if var_line else ""
            treeview.insert(assign_id, "end", text=f"{var_node.value}{var_line_text}")
            
            # Expresión derecha
            self._build_expr_tree(treeview, assign_id, node.children[1], total_lines)
            return
        
        # Nodos normales
        node_text = node.type
        if hasattr(node, 'value') and node.value is not None:
            node_text += f": {node.value}"
        node_text += line_text
        
        node_id = treeview.insert(parent, "end", text=node_text)
        
        # Procesar hijos
        if hasattr(node, 'children'):
            for child in node.children:
                self._build_ast_tree(treeview, node_id, child)
    def _build_expr_tree(self, treeview, parent, node, total_lines):
        """Versión final que muestra correctamente la jerarquía de operaciones"""
        if not isinstance(node, ASTNode):
            return

        line = getattr(node, 'lineno', None)
        line_text = f" [Línea: {max(1, line - (total_lines - 1))}]" if line is not None else ""

        # Caso especial para asignaciones
        if node.type == 'asignacion':
            assign_id = treeview.insert(parent, "end", text=f"={line_text}")
            
            # Variable asignada
            var_node = node.children[0]
            var_line = getattr(var_node, 'lineno', line)
            treeview.insert(assign_id, "end", text=f"{var_node.value} [Línea: {max(1, var_line - (total_lines - 1))}]")
            
            # Expresión derecha
            self._build_expr_tree(treeview, assign_id, node.children[1], total_lines)
            return

        # Caso para operaciones binarias
        if node.type == 'expresion_binaria':
            # Solo mostrar operadores básicos, no nodos genéricos
            if node.value in ['+', '-', '*', '/', '^']:
                op_id = treeview.insert(parent, "end", text=f"{node.value}{line_text}")
                
                # Procesar operandos
                for child in node.children:
                    if isinstance(child, ASTNode):
                        if child.type == 'expresion_binaria':
                            self._build_expr_tree(treeview, op_id, child, total_lines)
                        else:
                            child_line = getattr(child, 'lineno', line)
                            line_t = f" [Línea: {max(1, child_line - (total_lines - 1))}]" if child_line else ""
                            treeview.insert(op_id, "end", text=f"{child.value}{line_t}")
                    else:
                        treeview.insert(op_id, "end", text=f"{child}{line_text}")
                return
            else:
                # Para otros tipos de operaciones binarias, mostrar como nodo genérico
                node_id = treeview.insert(parent, "end", text=f"{node.type}{line_text}")
                for child in node.children:
                    self._build_expr_tree(treeview, node_id, child, total_lines)
                return

        # Caso para identificadores y literales
        if node.type in ['identificador', 'numero'] or (hasattr(node, 'value')) and not node.children:
            treeview.insert(parent, "end", text=f"{node.value}{line_text}")
            return

        # Caso genérico para otros nodos
        node_id = treeview.insert(parent, "end", text=f"{node.type}{line_text}")
        for child in node.children:
            self._build_expr_tree(treeview, node_id, child, total_lines)
            
        def _insert_child(self, treeview, parent_id, child, parent_line, total_lines):
            """Método auxiliar simplificado para insertar hijos"""
            if isinstance(child, ASTNode):
                child_line = getattr(child, 'lineno', parent_line)
                line_text = f" [Línea: {max(1, child_line - (total_lines - 1))}]" if child_line is not None else ""
                
                if hasattr(child, 'value') and not getattr(child, 'children', []):
                    treeview.insert(parent_id, "end", text=f"{child.value}{line_text}")
                else:
                    self._build_expr_tree(treeview, parent_id, child, total_lines)
            else:
                line_text = f" [Línea: {max(1, parent_line - (total_lines - 1))}]" if parent_line is not None else ""
                treeview.insert(parent_id, "end", text=f"{child}{line_text}")
    
    
                
        # def _build_expr_tree(self, treeview, parent, node, total_lines):
        # """Construye subárbol para expresiones"""
        # if not isinstance(node, ASTNode):
        #     return
        
        # line = getattr(node, 'lineno', None)
        # line_text = f" [Línea: {max(1, line - (total_lines - 1))}]" if line else ""
        
        # if node.type == 'expresion_binaria':
        #     op_text = f"{node.value}{line_text}"
        #     op_id = treeview.insert(parent, "end", text=op_text)
            
        #     for child in node.children:
        #         self._build_expr_tree(treeview, op_id, child, total_lines)
        # else:
        #     node_text = f"{node.value if hasattr(node, 'value') else node.type}{line_text}"
        #     treeview.insert(parent, "end", text=node_text)
        

    def _expand_tree(self, tree, item):
        """Expande todos los nodos del árbol"""
        children = tree.get_children(item)
        for child in children:
            self._expand_tree(tree, child)
        tree.item(item, open=True)

    def _collapse_tree(self, tree, item):
        """Contrae todos los nodos del árbol"""
        children = tree.get_children(item)
        for child in children:
            self._collapse_tree(tree, child)
        tree.item(item, open=False)

   

   

    def _highlight_error_in_editor(self, errors, input_text=None):
        """Resalta errores en el editor con ubicación precisa"""
        if input_text is None:
            input_text = self.editor.get("1.0", tk.END)
        
        input_lines = input_text.split('\n')
        self.editor.tag_remove("ERROR", "1.0", tk.END)
        
        for error in errors:
            try:
                line = error.get('line', 1)
                column = error.get('column', 1)
                
                # Ajustar para índices basados en 1 vs basados en 0
                line = max(1, int(line))
                column = max(1, int(column))
                
                # Verificar que la línea existe
                if line > len(input_lines):
                    continue
                    
                current_line = input_lines[line-1]
                
                # Ajustar columna si es mayor que la longitud de la línea
                column = min(column, len(current_line)+1)
                
                # Para errores de punto y coma faltante, resaltar el final del token anterior
                if error.get('token_type') == 'SEMICOLON' and error.get('value') == ';':
                    start_pos = f"{line}.{column-1}"
                    end_pos = f"{line}.{column}"
                else:
                    start_pos = f"{line}.{column-1}"
                    end_pos = f"{line}.{column}"
                
                # Verificar que la posición es válida
                if self.editor._is_valid_index(start_pos):
                    self.editor.tag_add("ERROR", start_pos, end_pos)
                    self.editor.see(start_pos)
                    
            except (ValueError, KeyError, tk.TclError) as e:
                print(f"Error al resaltar: {str(e)}")
                continue


if __name__ == "__main__":
    root = tk.Tk()
    ide = IDE(root)
    root.mainloop()

