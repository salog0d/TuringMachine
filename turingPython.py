"""
Resaltador de Sintaxis basado en Máquina de Turing
Implementación con estados explícitos y transiciones deterministas
"""

import string
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class EstadoMaquina(Enum):
    """Estados posibles de la Máquina de Turing"""
    INICIAL = "INICIAL"
    KEYWORD_CANDIDATO = "KEYWORD_CANDIDATO"
    KEYWORD_CONFIRMADO = "KEYWORD_CONFIRMADO"
    STRING_INICIADO = "STRING_INICIADO"
    STRING_ESCAPE = "STRING_ESCAPE"
    STRING_COMPLETO = "STRING_COMPLETO"
    NUMERO_INICIADO = "NUMERO_INICIADO"
    NUMERO_DECIMAL = "NUMERO_DECIMAL"
    NUMERO_COMPLETO = "NUMERO_COMPLETO"
    COMENTARIO_INICIADO = "COMENTARIO_INICIADO"
    COMENTARIO_COMPLETO = "COMENTARIO_COMPLETO"
    OPERADOR_INICIADO = "OPERADOR_INICIADO"
    OPERADOR_COMPLETO = "OPERADOR_COMPLETO"
    IDENTIFICADOR_INICIADO = "IDENTIFICADOR_INICIADO"
    IDENTIFICADOR_COMPLETO = "IDENTIFICADOR_COMPLETO"
    DELIMITADOR_DETECTADO = "DELIMITADOR_DETECTADO"
    ESPACIO_DETECTADO = "ESPACIO_DETECTADO"
    NO_ACEPTACION = "NO_ACEPTACION"
    ACEPTACION = "ACEPTACION"

class TipoToken(Enum):
    """Tipos de tokens reconocidos"""
    KEYWORD = "keyword"
    STRING = "string"
    NUMBER = "number"
    COMMENT = "comment"
    OPERATOR = "operator"
    IDENTIFIER = "identifier"
    DELIMITER = "delimiter"
    WHITESPACE = "whitespace"
    UNKNOWN = "unknown"

@dataclass
class Token:
    """Representación de un token procesado"""
    tipo: TipoToken
    valor: str
    posicion: int
    valido: bool = True

class TuringMachine:
    """Máquina de Turing para análisis léxico de Python"""
    
    def __init__(self):
        # Estados de la máquina
        self.estados = {
            EstadoMaquina.INICIAL,
            EstadoMaquina.KEYWORD_CANDIDATO,
            EstadoMaquina.KEYWORD_CONFIRMADO,
            EstadoMaquina.STRING_INICIADO,
            EstadoMaquina.STRING_ESCAPE,
            EstadoMaquina.STRING_COMPLETO,
            EstadoMaquina.NUMERO_INICIADO,
            EstadoMaquina.NUMERO_DECIMAL,
            EstadoMaquina.NUMERO_COMPLETO,
            EstadoMaquina.COMENTARIO_INICIADO,
            EstadoMaquina.COMENTARIO_COMPLETO,
            EstadoMaquina.OPERADOR_INICIADO,
            EstadoMaquina.OPERADOR_COMPLETO,
            EstadoMaquina.IDENTIFICADOR_INICIADO,
            EstadoMaquina.IDENTIFICADOR_COMPLETO,
            EstadoMaquina.DELIMITADOR_DETECTADO,
            EstadoMaquina.ESPACIO_DETECTADO,
            EstadoMaquina.NO_ACEPTACION,
            EstadoMaquina.ACEPTACION
        }
        
        # Estado actual de la máquina
        self.estado_actual = EstadoMaquina.INICIAL
        
        # Alfabeto válido para Python
        self.alfabeto = set(string.ascii_letters + string.digits + '_."\'#\t\n\r+-*/<>=!()[]{},:; ')
        
        # Palabras reservadas de Python
        self.keywords = {
            'False', 'None', 'True', 'and', 'as', 'assert', 'break',
            'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
            'return', 'try', 'while', 'with', 'yield', 'async', 'await'
        }
        
        # Operadores de Python (CORREGIDO: Lista completa)
        self.operadores = {
            # Aritméticos
            '+', '-', '*', '/', '//', '%', '**',
            # Asignación
            '=', '+=', '-=', '*=', '/=', '//=', '%=', '**=',
            # Comparación  
            '==', '!=', '<', '>', '<=', '>=', '<>',
            # Lógicos (se manejan como keywords)
            # Bitwise
            '&', '|', '^', '~', '<<', '>>', '&=', '|=', '^=', '<<=', '>>=',
            # Otros
            '!', '@', '@='
        }
        
        # Delimitadores
        self.delimitadores = {'(', ')', '[', ']', '{', '}', ',', ':', ';', '.'}
        
        # Cinta de la máquina (buffer de caracteres)
        self.cinta = []
        self.posicion_cinta = 0
        self.buffer_token = ""
        self.tokens_procesados = []
    
    def es_caracter_valido(self, caracter: str) -> bool:
        """Verifica si un carácter pertenece al alfabeto válido"""
        return caracter in self.alfabeto
    
    def reiniciar_estado(self):
        """Reinicia la máquina al estado inicial"""
        self.estado_actual = EstadoMaquina.INICIAL
        self.buffer_token = ""
    
    def transicion(self, caracter: str) -> Tuple[EstadoMaquina, str]:
        """
        Función de transición de la Máquina de Turing
        Retorna (nuevo_estado, acción)
        """
        
        # Verificar si el carácter es válido
        if not self.es_caracter_valido(caracter):
            return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        estado_actual = self.estado_actual
        
        # Estado INICIAL - Punto de partida
        if estado_actual == EstadoMaquina.INICIAL:
            if caracter.isalpha() or caracter == '_':
                # Podría ser keyword o identificador
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            elif caracter.isdigit():
                return EstadoMaquina.NUMERO_INICIADO, "LEER"
            elif caracter in ['"', "'"]:
                return EstadoMaquina.STRING_INICIADO, "LEER"
            elif caracter == '#':
                return EstadoMaquina.COMENTARIO_INICIADO, "LEER"
            elif caracter in '+-*/<>=!&|^~':
                return EstadoMaquina.OPERADOR_INICIADO, "LEER"
            elif caracter in self.delimitadores:
                return EstadoMaquina.DELIMITADOR_DETECTADO, "ACEPTAR"
            elif caracter in ' \t\n\r':
                return EstadoMaquina.ESPACIO_DETECTADO, "ACEPTAR"
            else:
                return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        # Estado KEYWORD_CANDIDATO - Leyendo posible keyword/identificador
        elif estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            if caracter.isalnum() or caracter == '_':
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            else:
                # Fin del token, verificar si es keyword
                if self.buffer_token in self.keywords:
                    return EstadoMaquina.KEYWORD_CONFIRMADO, "ACEPTAR_RETROCEDER"
                else:
                    return EstadoMaquina.IDENTIFICADOR_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_INICIADO - Leyendo número
        elif estado_actual == EstadoMaquina.NUMERO_INICIADO:
            if caracter.isdigit():
                return EstadoMaquina.NUMERO_INICIADO, "LEER"
            elif caracter == '.':
                return EstadoMaquina.NUMERO_DECIMAL, "LEER"
            else:
                return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_DECIMAL - Leyendo parte decimal
        elif estado_actual == EstadoMaquina.NUMERO_DECIMAL:
            if caracter.isdigit():
                return EstadoMaquina.NUMERO_DECIMAL, "LEER"
            else:
                return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado STRING_INICIADO - Leyendo string
        elif estado_actual == EstadoMaquina.STRING_INICIADO:
            if caracter == '\\':
                return EstadoMaquina.STRING_ESCAPE, "LEER"
            elif caracter in ['"', "'"]:
                # Verificar si coincide con el carácter de apertura
                return EstadoMaquina.STRING_COMPLETO, "ACEPTAR"
            else:
                return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado STRING_ESCAPE - Carácter de escape en string
        elif estado_actual == EstadoMaquina.STRING_ESCAPE:
            return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado COMENTARIO_INICIADO - Leyendo comentario
        elif estado_actual == EstadoMaquina.COMENTARIO_INICIADO:
            if caracter in '\n\r':
                return EstadoMaquina.COMENTARIO_COMPLETO, "ACEPTAR_RETROCEDER"
            else:
                return EstadoMaquina.COMENTARIO_INICIADO, "LEER"
        
        # Estado OPERADOR_INICIADO - Leyendo operador
        elif estado_actual == EstadoMaquina.OPERADOR_INICIADO:
            # Verificar operadores compuestos
            operador_candidato = self.buffer_token + caracter
            if operador_candidato in self.operadores:
                return EstadoMaquina.OPERADOR_INICIADO, "LEER"
            elif self.buffer_token in self.operadores:
                return EstadoMaquina.OPERADOR_COMPLETO, "ACEPTAR_RETROCEDER"
            else:
                return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        # Estados de aceptación - no deberían recibir más entrada
        else:
            return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
    
    def procesar_token_individual(self, token_texto: str, posicion: int) -> Token:
        """
        Procesa un token individual usando la máquina de Turing
        CORREGIDO: Mejor clasificación de tokens
        """
        self.reiniciar_estado()
        self.buffer_token = ""
        
        # Verificaciones directas primero (más eficiente)
        
        # 1. Strings (completos con comillas)
        if ((token_texto.startswith('"') and token_texto.endswith('"')) or 
            (token_texto.startswith("'") and token_texto.endswith("'")) or
            (token_texto.startswith('f"') and token_texto.endswith('"')) or
            (token_texto.startswith("f'") and token_texto.endswith("'"))):
            return Token(TipoToken.STRING, token_texto, posicion, True)
        
        # 2. Comentarios
        if token_texto.startswith('#'):
            return Token(TipoToken.COMMENT, token_texto, posicion, True)
        
        # 3. Números (incluyendo todas las variantes)
        if self._es_numero(token_texto):
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        
        # 4. Operadores (verificación directa)
        if token_texto in self.operadores:
            return Token(TipoToken.OPERATOR, token_texto, posicion, True)
        
        # 5. Delimitadores
        if token_texto in self.delimitadores:
            return Token(TipoToken.DELIMITER, token_texto, posicion, True)
        
        # 6. Keywords
        if token_texto in self.keywords:
            return Token(TipoToken.KEYWORD, token_texto, posicion, True)
        
        # 7. Espacios en blanco
        if token_texto.isspace():
            return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
        
        # 8. Identificadores (nombres de variables, funciones, etc.)
        if self._es_identificador_valido(token_texto):
            return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        
        # 9. Si no coincide con nada, usar la máquina de Turing como respaldo
        return self._procesar_con_maquina_turing(token_texto, posicion)
    
    def _es_numero(self, texto: str) -> bool:
        """Verifica si un texto es un número válido en Python"""
        try:
            # Intentar convertir a int o float
            if '.' in texto or 'e' in texto.lower():
                float(texto)
            else:
                int(texto, 0)  # Soporta hex, oct, bin automáticamente
            return True
        except ValueError:
            return False
    
    def _es_identificador_valido(self, texto: str) -> bool:
        """Verifica si un texto es un identificador válido"""
        if not texto:
            return False
        
        # Debe empezar con letra o guión bajo
        if not (texto[0].isalpha() or texto[0] == '_'):
            return False
        
        # El resto deben ser letras, números o guiones bajos
        return all(c.isalnum() or c == '_' for c in texto[1:])
    
    def _procesar_con_maquina_turing(self, token_texto: str, posicion: int) -> Token:
        """
        Procesamiento con Máquina de Turing como respaldo
        """
        # Agregar carácter centinela para forzar finalización
        texto_con_centinela = token_texto + " "
        
        for i, caracter in enumerate(texto_con_centinela):
            self.buffer_token += caracter
            nuevo_estado, accion = self.transicion(caracter)
            
            if accion == "RECHAZAR":
                return Token(TipoToken.UNKNOWN, token_texto, posicion, False)
            
            elif accion == "ACEPTAR" or accion == "ACEPTAR_RETROCEDER":
                # Determinar tipo de token basado en el estado
                if nuevo_estado == EstadoMaquina.KEYWORD_CONFIRMADO:
                    return Token(TipoToken.KEYWORD, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.IDENTIFICADOR_COMPLETO:
                    return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
                elif nuevo_estado in [EstadoMaquina.NUMERO_COMPLETO, EstadoMaquina.NUMERO_INICIADO]:
                    return Token(TipoToken.NUMBER, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.STRING_COMPLETO:
                    return Token(TipoToken.STRING, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.COMENTARIO_COMPLETO:
                    return Token(TipoToken.COMMENT, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.OPERADOR_COMPLETO:
                    return Token(TipoToken.OPERATOR, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.DELIMITADOR_DETECTADO:
                    return Token(TipoToken.DELIMITER, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.ESPACIO_DETECTADO:
                    return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
                
                break
            
            elif accion == "LEER":
                self.estado_actual = nuevo_estado
                continue
        
        # Si llegamos aquí sin aceptación explícita, clasificar por estado final
        if self.estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            if token_texto in self.keywords:
                return Token(TipoToken.KEYWORD, token_texto, posicion, True)
            else:
                return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        elif self.estado_actual in [EstadoMaquina.NUMERO_INICIADO, EstadoMaquina.NUMERO_DECIMAL]:
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        
        return Token(TipoToken.UNKNOWN, token_texto, posicion, False)
    
    def tokenizar_archivo(self, contenido_archivo: str) -> List[Token]:
        """
        Paso 1: Cargar archivo
        Paso 2: Separar por tokens (espacios como delimitadores)
        Paso 3: Procesar cada token individualmente
        """
        
        # Paso 1: Cargar archivo (ya recibido como parámetro)
        print(f"📁 Paso 1: Archivo cargado ({len(contenido_archivo)} caracteres)")
        
        # Paso 2: Separación inteligente por tokens
        tokens_texto = self._separar_tokens(contenido_archivo)
        print(f"🔍 Paso 2: Separados en {len(tokens_texto)} tokens")
        
        # Paso 3: Procesar cada token con la máquina de Turing
        tokens_procesados = []
        tokens_rechazados = []
        
        print("⚙️  Paso 3: Procesando tokens con Máquina de Turing...")
        
        for i, (texto_token, posicion) in enumerate(tokens_texto):
            # Descartar automáticamente tokens vacíos o solo espacios
            if not texto_token.strip():
                if texto_token:  # Si contiene espacios/tabs
                    token = Token(TipoToken.WHITESPACE, texto_token, posicion, True)
                    tokens_procesados.append(token)
                continue
            
            # Procesar token con la máquina de Turing
            token = self.procesar_token_individual(texto_token, posicion)
            tokens_procesados.append(token)
            
            if not token.valido:
                tokens_rechazados.append(token)
                print(f"❌ Token rechazado: '{token.valor}' en posición {token.posicion}")
        
        print(f"✅ Procesamiento completado:")
        print(f"   - Tokens válidos: {len(tokens_procesados) - len(tokens_rechazados)}")
        print(f"   - Tokens rechazados: {len(tokens_rechazados)}")
        
        return tokens_procesados
    
    def _separar_tokens(self, texto: str) -> List[Tuple[str, int]]:
        """
        Separación inteligente de tokens respetando strings, comentarios, etc.
        CORREGIDO: Mejor manejo de operadores y strings
        """
        tokens = []
        i = 0
        
        while i < len(texto):
            # Saltar espacios en blanco y capturarlos como tokens
            if texto[i] in ' \t':
                inicio = i
                while i < len(texto) and texto[i] in ' \t':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Saltos de línea como tokens separados
            if texto[i] in '\n\r':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Strings - capturar completos (CORREGIDO)
            if texto[i] in '"\'':
                inicio = i
                quote = texto[i]
                i += 1
                while i < len(texto) and texto[i] != quote:
                    if texto[i] == '\\':  # Escape
                        i += 2 if i + 1 < len(texto) else 1
                    else:
                        i += 1
                if i < len(texto):
                    i += 1  # Incluir quote de cierre
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # f-strings - capturar completos
            if i < len(texto) - 1 and texto[i] == 'f' and texto[i + 1] in '"\'':
                inicio = i
                i += 1  # Saltar 'f'
                quote = texto[i]
                i += 1
                while i < len(texto) and texto[i] != quote:
                    if texto[i] == '\\':  # Escape
                        i += 2 if i + 1 < len(texto) else 1
                    else:
                        i += 1
                if i < len(texto):
                    i += 1  # Incluir quote de cierre
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Comentarios - capturar hasta fin de línea
            if texto[i] == '#':
                inicio = i
                while i < len(texto) and texto[i] not in '\n\r':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Delimitadores - cada uno es un token individual
            if texto[i] in '()[]{},:;.':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Operadores - MEJORADO: manejo más preciso
            if texto[i] in '+-*/<>=!&|^~':
                inicio = i
                # Verificar operadores compuestos específicos
                if i < len(texto) - 1:
                    operador_doble = texto[i:i+2]
                    if operador_doble in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '//', '**', '<<', '>>', '&=', '|=', '^=', '<>']:
                        tokens.append((operador_doble, inicio))
                        i += 2
                        continue
                    # Verificar operadores triple
                    if i < len(texto) - 2:
                        operador_triple = texto[i:i+3]
                        if operador_triple in ['//=', '**=', '<<=', '>>=']:
                            tokens.append((operador_triple, inicio))
                            i += 3
                            continue
                
                # Operador simple
                tokens.append((texto[i], inicio))
                i += 1
                continue
            
            # Números - capturar completos incluyendo decimales, hex, etc.
            if texto[i].isdigit() or (texto[i] == '.' and i + 1 < len(texto) and texto[i + 1].isdigit()):
                inicio = i
                
                # Números hexadecimales, octales, binarios
                if i < len(texto) - 1 and texto[i] == '0' and texto[i + 1] in 'xXoObB':
                    i += 2
                    while i < len(texto) and (texto[i].isalnum()):
                        i += 1
                    tokens.append((texto[inicio:i], inicio))
                    continue
                
                # Números decimales normales
                while i < len(texto) and (texto[i].isdigit() or texto[i] == '.'):
                    i += 1
                
                # Notación científica
                if i < len(texto) and texto[i] in 'eE':
                    i += 1
                    if i < len(texto) and texto[i] in '+-':
                        i += 1
                    while i < len(texto) and texto[i].isdigit():
                        i += 1
                
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Identificadores/Keywords - letras, números, guiones bajos
            if texto[i].isalpha() or texto[i] == '_':
                inicio = i
                while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Carácter individual no reconocido
            tokens.append((texto[i], i))
            i += 1
        
        return tokens

class HTMLGenerator:
    """Generador de HTML para el resaltado de sintaxis con colores específicos por símbolo"""
    
    # Mapeo específico de operadores a clases CSS únicas
    OPERATOR_CSS_MAP = {
        '+': 'op-plus',
        '-': 'op-minus', 
        '*': 'op-multiply',
        '/': 'op-divide',
        '//': 'op-divide',
        '%': 'op-modulo',
        '**': 'op-power',
        '=': 'op-assign',
        '==': 'op-equal',
        '!=': 'op-not-equal',
        '<>': 'op-not-equal',
        '<': 'op-less',
        '>': 'op-greater',
        '<=': 'op-less-equal',
        '>=': 'op-greater-equal',
        '+=': 'op-plus-assign',
        '-=': 'op-minus-assign',
        '*=': 'op-multiply-assign',
        '/=': 'op-divide-assign',
        '//=': 'op-divide-assign',
        '%=': 'op-modulo',
        '**=': 'op-power',
        '&': 'op-bitwise-and',
        '|': 'op-bitwise-or',
        '^': 'op-bitwise-xor',
        '~': 'op-bitwise-not',
        '<<': 'op-left-shift',
        '>>': 'op-right-shift',
        '&=': 'op-bitwise-and',
        '|=': 'op-bitwise-or',
        '^=': 'op-bitwise-xor',
        '<<=': 'op-left-shift',
        '>>=': 'op-right-shift',
        '!': 'op-not'
    }
    
    # Mapeo específico de delimitadores a clases CSS únicas
    DELIMITER_CSS_MAP = {
        '(': 'del-paren-open',
        ')': 'del-paren-close',
        '[': 'del-bracket-open',
        ']': 'del-bracket-close',
        '{': 'del-brace-open',
        '}': 'del-brace-close',
        ',': 'del-comma',
        ':': 'del-colon',
        ';': 'del-semicolon',
        '.': 'del-dot'
    }
    
    # Mapeo específico de keywords lógicos
    LOGICAL_KEYWORDS = {
        'and': 'op-and',
        'or': 'op-or', 
        'not': 'op-not'
    }
    
    # Funciones built-in de Python
    BUILTINS = {
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
        'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
        'open', 'input', 'abs', 'max', 'min', 'sum', 'all', 'any', 'enumerate',
        'zip', 'map', 'filter', 'sorted', 'reversed', 'round', 'pow', 'divmod'
    }
    
    def generar_css(self) -> str:
        """CSS para el resaltado de sintaxis con colores únicos por símbolo"""
        return """
        <style>
        .code-container {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            overflow-x: auto;
            line-height: 1.6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Keywords - Azules */
        .keyword { color: #0066cc; font-weight: bold; }
        
        /* Strings - Verdes */
        .string { color: #228B22; background-color: #f0fff0; }
        
        /* Números - Naranjas/Rojos */
        .number { color: #FF6347; font-weight: bold; }
        
        /* Comentarios - Grises */
        .comment { color: #708090; font-style: italic; background-color: #f5f5f5; }
        
        /* Identificadores - Negro */
        .identifier { color: #2F4F4F; }
        
        /* Operadores Aritméticos - Violetas */
        .op-plus { color: #8A2BE2; font-weight: bold; }
        .op-minus { color: #9932CC; font-weight: bold; }
        .op-multiply { color: #BA55D3; font-weight: bold; }
        .op-divide { color: #DA70D6; font-weight: bold; }
        .op-modulo { color: #DDA0DD; font-weight: bold; }
        .op-power { color: #EE82EE; font-weight: bold; }
        
        /* Operadores de Comparación - Azules oscuros */
        .op-equal { color: #191970; font-weight: bold; }
        .op-not-equal { color: #000080; font-weight: bold; }
        .op-less { color: #0000CD; font-weight: bold; }
        .op-greater { color: #4169E1; font-weight: bold; }
        .op-less-equal { color: #4682B4; font-weight: bold; }
        .op-greater-equal { color: #6495ED; font-weight: bold; }
        
        /* Operadores de Asignación - Marrones */
        .op-assign { color: #8B4513; font-weight: bold; }
        .op-plus-assign { color: #A0522D; font-weight: bold; }
        .op-minus-assign { color: #CD853F; font-weight: bold; }
        .op-multiply-assign { color: #D2691E; font-weight: bold; }
        .op-divide-assign { color: #DEB887; font-weight: bold; }
        
        /* Operadores Lógicos - Rojos oscuros */
        .op-and { color: #B22222; font-weight: bold; }
        .op-or { color: #DC143C; font-weight: bold; }
        .op-not { color: #FF0000; font-weight: bold; }
        
        /* Operadores Bitwise - Cian/Turquesa */
        .op-bitwise-and { color: #008B8B; font-weight: bold; }
        .op-bitwise-or { color: #20B2AA; font-weight: bold; }
        .op-bitwise-xor { color: #48D1CC; font-weight: bold; }
        .op-bitwise-not { color: #00CED1; font-weight: bold; }
        .op-left-shift { color: #40E0D0; font-weight: bold; }
        .op-right-shift { color: #AFEEEE; font-weight: bold; }
        
        /* Delimitadores - Diferentes tonos */
        .del-paren-open { color: #FF1493; font-weight: bold; font-size: 1.1em; }
        .del-paren-close { color: #FF1493; font-weight: bold; font-size: 1.1em; }
        .del-bracket-open { color: #FF4500; font-weight: bold; font-size: 1.1em; }
        .del-bracket-close { color: #FF4500; font-weight: bold; font-size: 1.1em; }
        .del-brace-open { color: #FF6347; font-weight: bold; font-size: 1.1em; }
        .del-brace-close { color: #FF6347; font-weight: bold; font-size: 1.1em; }
        .del-comma { color: #32CD32; font-weight: bold; }
        .del-colon { color: #00FF00; font-weight: bold; }
        .del-semicolon { color: #ADFF2F; font-weight: bold; }
        .del-dot { color: #9ACD32; font-weight: bold; }
        
        /* Espacios en blanco */
        .whitespace { background-color: transparent; }
        
        /* Tokens desconocidos */
        .unknown { 
            color: #FF0000; 
            background-color: #FFE4E1; 
            border: 2px solid #FF6347;
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        /* Valores especiales */
        .boolean-true { color: #006400; font-weight: bold; background-color: #F0FFF0; }
        .boolean-false { color: #8B0000; font-weight: bold; background-color: #FFF0F0; }
        .none-value { color: #4B0082; font-weight: bold; background-color: #F8F8FF; }
        
        /* Funciones built-in */
        .builtin { color: #800080; font-weight: bold; text-decoration: underline; }
        
        .stats {
            background-color: #e8f4f8;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
        }
        
        .stats h3 {
            margin-top: 0;
            color: #0066cc;
        }
        
        /* Leyenda de colores */
        .color-legend {
            background-color: #f0f8ff;
            border: 1px solid #b0c4de;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        
        .legend-category {
            margin-bottom: 10px;
        }
        
        .legend-item {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }
        </style>
        """
    
    def tokens_a_html(self, tokens: List[Token]) -> str:
        """Convierte tokens a HTML resaltado con colores específicos por símbolo"""
        html_parts = []
        
        for token in tokens:
            valor_escapado = (token.valor.replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;')
                                        .replace('"', '&quot;'))
            
            # Determinar clase CSS específica basada en el tipo y valor del token
            css_class = self._determinar_clase_css(token)
            
            if token.tipo == TipoToken.WHITESPACE:
                # Preservar espacios y tabs
                valor_escapado = valor_escapado.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                html_parts.append(valor_escapado)
            else:
                html_parts.append(f'<span class="{css_class}">{valor_escapado}</span>')
        
        return ''.join(html_parts)
    
    def _determinar_clase_css(self, token: Token) -> str:
        """Determina la clase CSS específica para cada token basada en su valor exacto"""
        
        if token.tipo == TipoToken.KEYWORD:
            # Keywords lógicos tienen colores especiales
            if token.valor in self.LOGICAL_KEYWORDS:
                return self.LOGICAL_KEYWORDS[token.valor]
            return 'keyword'
        
        elif token.tipo == TipoToken.STRING:
            return 'string'
        
        elif token.tipo == TipoToken.NUMBER:
            return 'number'
        
        elif token.tipo == TipoToken.COMMENT:
            return 'comment'
        
        elif token.tipo == TipoToken.OPERATOR:
            # Cada operador tiene su propio color
            return self.OPERATOR_CSS_MAP.get(token.valor, 'operator')
        
        elif token.tipo == TipoToken.IDENTIFIER:
            # Verificar si es un built-in
            if token.valor in self.BUILTINS:
                return 'builtin'
            # Verificar valores especiales
            elif token.valor == 'True':
                return 'boolean-true'
            elif token.valor == 'False':
                return 'boolean-false'
            elif token.valor == 'None':
                return 'none-value'
            return 'identifier'
        
        elif token.tipo == TipoToken.DELIMITER:
            # Cada delimitador tiene su propio color
            return self.DELIMITER_CSS_MAP.get(token.valor, 'delimiter')
        
        elif token.tipo == TipoToken.WHITESPACE:
            return 'whitespace'
        
        else:
            return 'unknown'

class ResaltadorSintaxis:
    """Clase principal del resaltador de sintaxis basado en Máquina de Turing"""
    
    def __init__(self):
        self.maquina_turing = TuringMachine()
        self.generador_html = HTMLGenerator()
    
    def procesar_archivo(self, archivo_entrada: str, archivo_salida: str):
        """Procesa un archivo TXT con código Python y genera HTML resaltado"""
        
        try:
            # Verificar que el archivo de entrada sea .txt
            if not archivo_entrada.lower().endswith('.txt'):
                print(f"❌ Error: Se esperaba un archivo .txt, recibido: {archivo_entrada}")
                return
            
            # Paso 1: Cargar archivo TXT
            print(f"🚀 Iniciando procesamiento de archivo TXT: {archivo_entrada}")
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            print(f"📄 Archivo TXT cargado exitosamente ({len(contenido)} caracteres)")
            print(f"🔍 Analizando código Python contenido en el archivo...")
            
            # Procesar con la Máquina de Turing
            tokens = self.maquina_turing.tokenizar_archivo(contenido)
            
            # Generar estadísticas
            stats = self._generar_estadisticas(tokens)
            
            # Generar HTML
            css = self.generador_html.generar_css()
            html_codigo = self.generador_html.tokens_a_html(tokens)
            
            # Documento HTML completo
            html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Léxico - {archivo_entrada}</title>
    {css}
</head>
<body>
    <h1>🔍 Análisis Léxico con Máquina de Turing</h1>
    <h2>Archivo TXT procesado: {archivo_entrada}</h2>
    <p><em>Código Python analizado desde archivo de texto</em></p>
    
    <div class="color-legend">
        <h3>🎨 Leyenda de Colores por Símbolo</h3>
        
        <div class="legend-category">
            <strong>Keywords:</strong>
            <span class="legend-item"><span class="keyword">def if else for while</span> (Azul)</span>
            <span class="legend-item"><span class="op-and">and</span> <span class="op-or">or</span> <span class="op-not">not</span> (Rojo)</span>
        </div>
        
        <div class="legend-category">
            <strong>Operadores Aritméticos:</strong>
            <span class="legend-item"><span class="op-plus">+</span></span>
            <span class="legend-item"><span class="op-minus">-</span></span>
            <span class="legend-item"><span class="op-multiply">*</span></span>
            <span class="legend-item"><span class="op-divide">/</span></span>
            <span class="legend-item"><span class="op-power">**</span></span>
            <span class="legend-item"><span class="op-modulo">%</span></span>
        </div>
        
        <div class="legend-category">
            <strong>Operadores de Comparación:</strong>
            <span class="legend-item"><span class="op-equal">==</span></span>
            <span class="legend-item"><span class="op-not-equal">!=</span></span>
            <span class="legend-item"><span class="op-less">&lt;</span></span>
            <span class="legend-item"><span class="op-greater">&gt;</span></span>
            <span class="legend-item"><span class="op-less-equal">&lt;=</span></span>
            <span class="legend-item"><span class="op-greater-equal">&gt;=</span></span>
        </div>
        
        <div class="legend-category">
            <strong>Delimitadores:</strong>
            <span class="legend-item"><span class="del-paren-open">(</span><span class="del-paren-close">)</span> Paréntesis</span>
            <span class="legend-item"><span class="del-bracket-open">[</span><span class="del-bracket-close">]</span> Corchetes</span>
            <span class="legend-item"><span class="del-brace-open">{{</span><span class="del-brace-close">}}</span> Llaves</span>
            <span class="legend-item"><span class="del-comma">,</span> <span class="del-colon">:</span> <span class="del-dot">.</span></span>
        </div>
        
        <div class="legend-category">
            <strong>Tipos de Datos:</strong>
            <span class="legend-item"><span class="string">"strings"</span></span>
            <span class="legend-item"><span class="number">123</span></span>
            <span class="legend-item"><span class="boolean-true">True</span></span>
            <span class="legend-item"><span class="boolean-false">False</span></span>
            <span class="legend-item"><span class="none-value">None</span></span>
        </div>
        
        <div class="legend-category">
            <strong>Otros:</strong>
            <span class="legend-item"><span class="builtin">print() len()</span> Built-ins</span>
            <span class="legend-item"><span class="comment"># comentarios</span></span>
            <span class="legend-item"><span class="identifier">variables</span></span>
        </div>
    </div>
    
    <div class="stats">
        <h3>📊 Estadísticas del Análisis</h3>
        {stats}
    </div>
    
    <div class="code-container">
        {html_codigo}
    </div>
    
    <div style="margin-top: 20px; color: #666; font-size: 12px; text-align: center;">
        <p>Generado por Resaltador de Sintaxis - Máquina de Turing</p>
        <p>Implementación basada en Estados y Transiciones Deterministas</p>
        <p>Entrada: Archivo TXT → Salida: HTML con sintaxis resaltada</p>
        <p><strong>🎨 Cada símbolo tiene un color único para máxima claridad visual</strong></p>
    </div>
</body>
</html>"""
            
            # Guardar archivo HTML
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write(html_completo)
            
            print(f"✅ Procesamiento completado exitosamente!")
            print(f"📄 Archivo TXT procesado: {archivo_entrada}")
            print(f"🌐 Archivo HTML generado: {archivo_salida}")
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo TXT: {archivo_entrada}")
        except Exception as e:
            print(f"❌ Error durante el procesamiento del archivo TXT: {e}")
    
    def _generar_estadisticas(self, tokens: List[Token]) -> str:
        """Genera estadísticas del análisis de tokens"""
        conteo_tipos = {}
        tokens_invalidos = []
        
        for token in tokens:
            if token.tipo not in conteo_tipos:
                conteo_tipos[token.tipo] = 0
            conteo_tipos[token.tipo] += 1
            
            if not token.valido:
                tokens_invalidos.append(token)
        
        stats_html = f"<p><strong>Total de tokens procesados:</strong> {len(tokens)}</p>"
        stats_html += "<p><strong>Distribución por tipo:</strong></p><ul>"
        
        for tipo, cantidad in sorted(conteo_tipos.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / len(tokens)) * 100
            stats_html += f"<li>{tipo.value}: {cantidad} ({porcentaje:.1f}%)</li>"
        
        stats_html += "</ul>"
        
        if tokens_invalidos:
            stats_html += f"<p><strong>⚠️ Tokens inválidos encontrados:</strong> {len(tokens_invalidos)}</p>"
            stats_html += "<ul>"
            for token in tokens_invalidos[:5]:  # Mostrar solo los primeros 5
                stats_html += f"<li>'{token.valor}' en posición {token.posicion}</li>"
            if len(tokens_invalidos) > 5:
                stats_html += f"<li>... y {len(tokens_invalidos) - 5} más</li>"
            stats_html += "</ul>"
        
        return stats_html

def main():
    """Función principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Uso: python turing_highlighter.py <archivo.txt> [salida.html]")
        print("📝 Ejemplo: python turing_highlighter.py codigo_python.txt resultado.html")
        print("📄 El archivo de entrada debe ser un .txt que contenga código Python")
        return
    
    archivo_entrada = sys.argv[1]
    
    # Verificar que la entrada sea un archivo .txt
    if not archivo_entrada.lower().endswith('.txt'):
        print("❌ Error: El archivo de entrada debe ser un archivo .txt")
        print("📝 Ejemplo: python turing_highlighter.py mi_codigo.txt")
        return
    
    # Generar nombre de salida basado en el archivo .txt
    if len(sys.argv) > 2:
        archivo_salida = sys.argv[2]
    else:
        # Cambiar .txt por _highlighted.html
        archivo_salida = archivo_entrada.replace('.txt', '_highlighted.html')
    
    resaltador = ResaltadorSintaxis()
    resaltador.procesar_archivo(archivo_entrada, archivo_salida)
   

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
   