# optimizacion.py - Optimizaciones de código intermedio
class Optimizer:
    def __init__(self):
        self.optimizations_applied = []
    
    def optimize(self, intermediate_code):
        """Aplica optimizaciones al código intermedio"""
        if not intermediate_code:
            return intermediate_code
            
        optimized_code = intermediate_code.copy()
        
        # Aplicar optimizaciones en secuencia
        optimized_code = self._remove_redundant_assignments(optimized_code)
        optimized_code = self._constant_folding(optimized_code)
        optimized_code = self._constant_propagation(optimized_code)
        optimized_code = self._dead_code_elimination(optimized_code)
        optimized_code = self._strength_reduction(optimized_code)
        
        return optimized_code
    
    def _remove_redundant_assignments(self, code):
        """Elimina asignaciones redundantes como a = a"""
        optimized = []
        for instruction in code:
            if (instruction['type'] == 'assign' and 
                'target' in instruction and 'source' in instruction and
                instruction['target'] == instruction['source']):
                self.optimizations_applied.append(f"Eliminada asignación redundante: {instruction}")
                continue
            optimized.append(instruction)
        return optimized
    
    def _constant_folding(self, code):
        """Realiza operaciones con constantes en tiempo de compilación"""
        optimized = []
        for instruction in code:
            if instruction['type'] == 'binary_op':
                # Verificar si ambos operandos son constantes
                left_const = self._is_constant(instruction.get('left'))
                right_const = self._is_constant(instruction.get('right'))
                
                if left_const and right_const:
                    result = self._evaluate_constant_expression(
                        instruction['left'], 
                        instruction['operator'], 
                        instruction['right']
                    )
                    if result is not None:
                        # Reemplazar con asignación directa
                        new_instruction = {
                            'type': 'assign',
                            'target': instruction['target'],
                            'source': result
                        }
                        optimized.append(new_instruction)
                        self.optimizations_applied.append(f"Constant folding: {instruction} -> {new_instruction}")
                        continue
            
            optimized.append(instruction)
        return optimized
    
    def _constant_propagation(self, code):
        """Propaga valores constantes a través del código"""
        constant_map = {}
        optimized = []
        
        for instruction in code:
            optimized_instruction = instruction.copy()
            
            # Actualizar mapa de constantes
            if instruction['type'] == 'assign' and self._is_constant(instruction.get('source')):
                constant_map[instruction['target']] = instruction['source']
            
            # Reemplazar usos de variables con sus valores constantes
            if 'left' in optimized_instruction and optimized_instruction['left'] in constant_map:
                optimized_instruction['left'] = constant_map[optimized_instruction['left']]
                self.optimizations_applied.append(f"Constant propagation: {instruction['left']} -> {constant_map[instruction['left']]}")
            
            if 'right' in optimized_instruction and optimized_instruction['right'] in constant_map:
                optimized_instruction['right'] = constant_map[optimized_instruction['right']]
                self.optimizations_applied.append(f"Constant propagation: {instruction['right']} -> {constant_map[instruction['right']]}")
            
            # Si una variable es reasignada, remover del mapa de constantes
            if instruction['type'] == 'assign' and instruction['target'] in constant_map:
                del constant_map[instruction['target']]
            
            optimized.append(optimized_instruction)
        
        return optimized
    
    def _dead_code_elimination(self, code):
        """Elimina código que no tiene efecto en el programa"""
        used_vars = set()
        optimized = []
        
        # Primera pasada: identificar variables usadas
        for instruction in reversed(code):
            if 'target' in instruction:
                if instruction['target'] not in used_vars and instruction['type'] != 'output':
                    # Esta asignación podría ser código muerto
                    continue
                else:
                    # Marcar variables usadas en el lado derecho
                    if 'left' in instruction and not self._is_constant(instruction['left']):
                        used_vars.add(instruction['left'])
                    if 'right' in instruction and not self._is_constant(instruction['right']):
                        used_vars.add(instruction['right'])
                    if 'source' in instruction and not self._is_constant(instruction['source']):
                        used_vars.add(instruction['source'])
                    optimized.append(instruction)
            else:
                optimized.append(instruction)
        
        return list(reversed(optimized))
    
    def _strength_reduction(self, code):
        """Reemplaza operaciones costosas por equivalentes más eficientes"""
        optimized = []
        
        for instruction in code:
            if instruction['type'] == 'binary_op':
                operator = instruction['operator']
                left = instruction.get('left')
                right = instruction.get('right')
                
                # Reemplazar multiplicación por 2 con shift left
                if operator == '*' and right == 2:
                    new_instruction = {
                        'type': 'binary_op',
                        'target': instruction['target'],
                        'operator': '<<',
                        'left': left,
                        'right': 1
                    }
                    optimized.append(new_instruction)
                    self.optimizations_applied.append(f"Strength reduction: *2 -> <<1")
                    continue
                
                # Reemplazar división por 2 con shift right
                elif operator == '/' and right == 2:
                    new_instruction = {
                        'type': 'binary_op',
                        'target': instruction['target'],
                        'operator': '>>',
                        'left': left,
                        'right': 1
                    }
                    optimized.append(new_instruction)
                    self.optimizations_applied.append(f"Strength reduction: /2 -> >>1")
                    continue
            
            optimized.append(instruction)
        
        return optimized
    
    def _is_constant(self, value):
        """Verifica si un valor es constante"""
        return isinstance(value, (int, float, bool)) or (isinstance(value, str) and value.replace('.', '').isdigit())
    
    def _evaluate_constant_expression(self, left, operator, right):
        """Evalúa una expresión con constantes"""
        try:
            if operator == '+': return left + right
            elif operator == '-': return left - right
            elif operator == '*': return left * right
            elif operator == '/': 
                if right != 0: return left / right
                else: return None
            elif operator == '%': 
                if right != 0: return left % right
                else: return None
            elif operator == '^': return left ** right
            elif operator == '&&': return left and right
            elif operator == '||': return left or right
            elif operator == '==': return left == right
            elif operator == '!=': return left != right
            elif operator == '<': return left < right
            elif operator == '<=': return left <= right
            elif operator == '>': return left > right
            elif operator == '>=': return left >= right
        except:
            return None
        return None
    
    def get_optimization_report(self):
        """Genera un reporte de las optimizaciones aplicadas"""
        if not self.optimizations_applied:
            return "No se aplicaron optimizaciones"
        
        report = "=== REPORTE DE OPTIMIZACIONES ===\n"
        for i, opt in enumerate(self.optimizations_applied, 1):
            report += f"{i}. {opt}\n"
        return report

def optimize_intermediate_code(intermediate_code):
    """Función principal de optimización"""
    optimizer = Optimizer()
    optimized_code = optimizer.optimize(intermediate_code)
    return optimized_code, optimizer.get_optimization_report()