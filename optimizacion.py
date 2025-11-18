# optimizacion.py - OPTIMIZADOR MEJORADO

class Optimizer:
    def __init__(self):
        self.optimizations_applied = []
    
    def optimize(self, intermediate_code):
        """Aplica optimizaciones al código intermedio"""
        if not intermediate_code:
            return intermediate_code
            
        print("INICIANDO OPTIMIZACIÓN")
        print(f"Cuádruplos originales: {len(intermediate_code)}")
        
        optimized_code = intermediate_code.copy()
        
        # Mostrar código original
        print("CÓDIGO ORIGINAL:")
        for i, quad in enumerate(intermediate_code):
            print(f"   {i}. {quad}")
        
        # Aplicar optimizaciones
        optimized_code = self._eliminate_unused_variables(optimized_code)
        optimized_code = self._constant_folding(optimized_code)
        optimized_code = self._constant_propagation(optimized_code)
        
        print(f"Cuádruplos optimizados: {len(optimized_code)}")
        print("OPTIMIZACIÓN COMPLETADA")
        return optimized_code
    
    def _eliminate_unused_variables(self, code):
        """Elimina variables que nunca se usan"""
        if not code:
            return code
        
        print("Buscando variables no utilizadas...")
        
        # PASO 1: Encontrar todas las variables USADAS
        used_vars = set()
        for instruction in code:
            if instruction['type'] == 'binary_op':
                left = instruction.get('left')
                right = instruction.get('right')
                if isinstance(left, str) and not left.startswith('t'):
                    used_vars.add(left)
                if isinstance(right, str) and not right.startswith('t'):
                    used_vars.add(right)
            elif instruction['type'] == 'output':
                value = instruction.get('value')
                if isinstance(value, str) and not value.startswith('"'):
                    used_vars.add(value)
            elif instruction['type'] == 'input':
                # Las variables de input se consideran usadas
                target = instruction.get('target')
                if isinstance(target, str):
                    used_vars.add(target)
        
        print(f"   Variables usadas: {used_vars}")
        
        # PASO 2: Encontrar todas las variables DECLARADAS
        declared_vars = set()
        for instruction in code:
            if instruction['type'] == 'assign':
                target = instruction.get('target')
                if isinstance(target, str):
                    declared_vars.add(target)
        
        print(f"   Variables declaradas: {declared_vars}")
        
        # PASO 3: Encontrar variables NO UTILIZADAS
        unused_vars = declared_vars - used_vars
        print(f"   Variables no utilizadas: {unused_vars}")
        
        # PASO 4: Eliminar asignaciones a variables no utilizadas
        if not unused_vars:
            print("   No hay variables no utilizadas")
            return code
        
        optimized = []
        removed_count = 0
        
        for instruction in code:
            if instruction['type'] == 'assign':
                target = instruction.get('target')
                if target in unused_vars:
                    removed_count += 1
                    self.optimizations_applied.append(f"Eliminada variable no usada: {target}")
                    print(f"   ELIMINANDO: {target} = {instruction.get('source')}")
                    continue
            
            optimized.append(instruction)
        
        if removed_count > 0:
            self.optimizations_applied.append(f"Total eliminadas: {removed_count} variables")
            print(f"Eliminadas {removed_count} variables no utilizadas")
        
        return optimized
    
    def _constant_folding(self, code):
        """Realiza operaciones con constantes"""
        optimized = []
        for instruction in code:
            if instruction['type'] == 'binary_op':
                left = instruction.get('left')
                right = instruction.get('right')
                operator = instruction.get('operator')
                
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    result = None
                    if operator == '+': result = left + right
                    elif operator == '-': result = left - right
                    elif operator == '*': result = left * right
                    elif operator == '/': result = left / right if right != 0 else left
                    
                    if result is not None:
                        optimized.append({
                            'type': 'assign',
                            'target': instruction['target'],
                            'source': result
                        })
                        self.optimizations_applied.append(f"Constant folding: {left} {operator} {right} = {result}")
                        print(f"   CONSTANT FOLDING: {left} {operator} {right} = {result}")
                        continue
            
            optimized.append(instruction)
        return optimized
    
    def _constant_propagation(self, code):
        """Propaga valores constantes"""
        constant_map = {}
        optimized = []
        
        for instruction in code:
            # Identificar constantes
            if (instruction['type'] == 'assign' and 
                isinstance(instruction.get('source'), (int, float))):
                constant_map[instruction['target']] = instruction['source']
                self.optimizations_applied.append(f"Constante identificada: {instruction['target']} = {instruction['source']}")
                print(f"   CONSTANTE: {instruction['target']} = {instruction['source']}")
            
            # Crear copia para modificar
            new_instruction = instruction.copy()
            
            # Reemplazar variables con constantes
            if instruction['type'] == 'binary_op':
                if instruction.get('left') in constant_map:
                    new_instruction['left'] = constant_map[instruction['left']]
                    print(f"   PROPAGACIÓN: {instruction['left']} -> {constant_map[instruction['left']]}")
                if instruction.get('right') in constant_map:
                    new_instruction['right'] = constant_map[instruction['right']]
                    print(f"   PROPAGACIÓN: {instruction['right']} -> {constant_map[instruction['right']]}")
            
            optimized.append(new_instruction)
            
            # Si se reasigna, remover de constantes
            if instruction['type'] == 'assign' and instruction['target'] in constant_map:
                del constant_map[instruction['target']]
        
        return optimized
    
    def get_optimization_report(self):
        """Genera reporte de optimizaciones"""
        if not self.optimizations_applied:
            return "No se aplicaron optimizaciones"
        
        report = "=== REPORTE DE OPTIMIZACIONES ===\n"
        for i, opt in enumerate(self.optimizations_applied, 1):
            report += f"{i}. {opt}\n"
        
        report += f"\nTotal de optimizaciones aplicadas: {len(self.optimizations_applied)}"
        return report

def optimize_intermediate_code(intermediate_code):
    optimizer = Optimizer()
    optimized_code = optimizer.optimize(intermediate_code)
    return optimized_code, optimizer.get_optimization_report()