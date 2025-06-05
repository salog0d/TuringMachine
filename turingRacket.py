"""
Resaltador de Sintaxis Racket basado en Máquina de Turing
Implementación con estados explícitos y transiciones deterministas
Especializado para el lenguaje funcional Racket (dialecto de Lisp/Scheme)
"""

import string
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class EstadoMaquina(Enum):
    """Estados posibles de la Máquina de Turing para Racket"""
    INICIAL = "INICIAL"
    KEYWORD_CANDIDATO = "KEYWORD_CANDIDATO"
    KEYWORD_CONFIRMADO = "KEYWORD_CONFIRMADO"
    STRING_INICIADO = "STRING_INICIADO"
    STRING_ESCAPE = "STRING_ESCAPE"
    STRING_COMPLETO = "STRING_COMPLETO"
    NUMERO_INICIADO = "NUMERO_INICIADO"
    NUMERO_DECIMAL = "NUMERO_DECIMAL"
    NUMERO_FRACCION = "NUMERO_FRACCION"
    NUMERO_COMPLEJO = "NUMERO_COMPLEJO"
    NUMERO_COMPLETO = "NUMERO_COMPLETO"
    COMENTARIO_LINEA_INICIADO = "COMENTARIO_LINEA_INICIADO"
    COMENTARIO_BLOQUE_INICIADO = "COMENTARIO_BLOQUE_INICIADO"
    COMENTARIO_BLOQUE_PIPE = "COMENTARIO_BLOQUE_PIPE"
    COMENTARIO_COMPLETO = "COMENTARIO_COMPLETO"
    SIMBOLO_INICIADO = "SIMBOLO_INICIADO"
    SIMBOLO_COMPLETO = "SIMBOLO_COMPLETO"
    CARACTER_LITERAL_INICIADO = "CARACTER_LITERAL_INICIADO"
    CARACTER_LITERAL_COMPLETO = "CARACTER_LITERAL_COMPLETO"
    BOOLEAN_LITERAL_INICIADO = "BOOLEAN_LITERAL_INICIADO"
    BOOLEAN_LITERAL_COMPLETO = "BOOLEAN_LITERAL_COMPLETO"
    IDENTIFICADOR_INICIADO = "IDENTIFICADOR_INICIADO"
    IDENTIFICADOR_COMPLETO = "IDENTIFICADOR_COMPLETO"
    DELIMITADOR_DETECTADO = "DELIMITADOR_DETECTADO"
    ESPACIO_DETECTADO = "ESPACIO_DETECTADO"
    OPERADOR_DETECTADO = "OPERADOR_DETECTADO"
    NO_ACEPTACION = "NO_ACEPTACION"
    ACEPTACION = "ACEPTACION"

class TipoToken(Enum):
    """Tipos de tokens reconocidos en Racket"""
    KEYWORD = "keyword"
    STRING = "string"
    NUMBER = "number"
    COMMENT = "comment"
    SYMBOL = "symbol"
    CHARACTER = "character"
    BOOLEAN = "boolean"
    IDENTIFIER = "identifier"
    DELIMITER = "delimiter"
    OPERATOR = "operator"
    BUILTIN = "builtin"
    SPECIAL_FORM = "special_form"
    WHITESPACE = "whitespace"
    UNKNOWN = "unknown"

@dataclass
class Token:
    """Representación de un token procesado"""
    tipo: TipoToken
    valor: str
    posicion: int
    valido: bool = True

class RacketTuringMachine:
    """Máquina de Turing para análisis léxico de Racket"""
    
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
            EstadoMaquina.NUMERO_FRACCION,
            EstadoMaquina.NUMERO_COMPLEJO,
            EstadoMaquina.NUMERO_COMPLETO,
            EstadoMaquina.COMENTARIO_LINEA_INICIADO,
            EstadoMaquina.COMENTARIO_BLOQUE_INICIADO,
            EstadoMaquina.COMENTARIO_BLOQUE_PIPE,
            EstadoMaquina.COMENTARIO_COMPLETO,
            EstadoMaquina.SIMBOLO_INICIADO,
            EstadoMaquina.SIMBOLO_COMPLETO,
            EstadoMaquina.CARACTER_LITERAL_INICIADO,
            EstadoMaquina.CARACTER_LITERAL_COMPLETO,
            EstadoMaquina.BOOLEAN_LITERAL_INICIADO,
            EstadoMaquina.BOOLEAN_LITERAL_COMPLETO,
            EstadoMaquina.IDENTIFICADOR_INICIADO,
            EstadoMaquina.IDENTIFICADOR_COMPLETO,
            EstadoMaquina.DELIMITADOR_DETECTADO,
            EstadoMaquina.ESPACIO_DETECTADO,
            EstadoMaquina.OPERADOR_DETECTADO,
            EstadoMaquina.NO_ACEPTACION,
            EstadoMaquina.ACEPTACION
        }
        
        # Estado actual de la máquina
        self.estado_actual = EstadoMaquina.INICIAL
        
        # Alfabeto válido para Racket (más permisivo que otros lenguajes)
        self.alfabeto = set(string.ascii_letters + string.digits + 
                           '_-+*/<>=!?:$%&^~@#|\\\'\"()[]{}.,; \t\n\r`')
        
        # Keywords/Special Forms de Racket
        self.keywords = {
            # Definiciones básicas
            'define', 'define-values', 'define-syntax', 'define-struct',
            'define-macro', 'define-for-syntax',
            
            # Control de flujo
            'if', 'cond', 'case', 'when', 'unless', 'and', 'or', 'not',
            
            # Funciones y procedimientos
            'lambda', 'λ', 'procedure?', 'apply', 'curry', 'compose',
            
            # Binding/Scope
            'let', 'let*', 'letrec', 'let-values', 'let*-values',
            'parameterize', 'with-handlers',
            
            # Iteración
            'for', 'for/list', 'for/vector', 'for/hash', 'for/sum',
            'for/fold', 'for*', 'for*/list', 'do', 'map', 'filter',
            'foldl', 'foldr', 'andmap', 'ormap',
            
            # Evaluación y compilación
            'eval', 'compile', 'expand', 'syntax-e', 'syntax->datum',
            'datum->syntax', 'quote', 'quasiquote', 'unquote', 'unquote-splicing',
            
            # Módulos
            'module', 'module*', 'module+', 'require', 'provide',
            'only-in', 'except-in', 'prefix-in', 'rename-in',
            
            # Macros y sintaxis
            'syntax-rules', 'syntax-case', 'syntax', 'with-syntax',
            'syntax-parameter', 'syntax-parameterize',
            
            # Contratos
            'contract', 'define/contract', 'provide/contract',
            
            # Clases y objetos
            'class', 'class*', 'interface', 'mixin', 'new', 'instantiate',
            'send', 'send*', 'send/apply', 'super', 'inner',
            
            # Excepciones
            'raise', 'raise-argument-error', 'raise-type-error',
            'raise-arity-error', 'raise-syntax-error',
            
            # Continuaciones
            'call/cc', 'call-with-current-continuation',
            'call/ec', 'call-with-escape-continuation',
            
            # I/O
            'with-input-from-file', 'with-output-to-file',
            'call-with-input-file', 'call-with-output-file',
            
            # Otros
            'begin', 'begin0', 'set!', 'values', 'void', 'time',
            'match', 'match-lambda', 'match-let'
        }
        
        # Funciones built-in de Racket
        self.builtins = {
            # Listas
            'cons', 'car', 'cdr', 'caar', 'cadr', 'cdar', 'cddr',
            'caaar', 'caadr', 'cadar', 'caddr', 'cdaar', 'cdadr',
            'cddar', 'cdddr', 'list', 'list*', 'append', 'reverse',
            'length', 'list-ref', 'list-tail', 'member', 'memq', 'memv',
            'assoc', 'assq', 'assv', 'null?', 'pair?', 'list?',
            
            # Números
            'number?', 'complex?', 'real?', 'rational?', 'integer?',
            'exact?', 'inexact?', 'zero?', 'positive?', 'negative?',
            'odd?', 'even?', 'max', 'min', 'abs', 'quotient',
            'remainder', 'modulo', 'gcd', 'lcm', 'numerator', 'denominator',
            'floor', 'ceiling', 'truncate', 'round', 'exp', 'log',
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sqrt',
            'expt', 'make-rectangular', 'make-polar', 'real-part', 'imag-part',
            'magnitude', 'angle', 'exact->inexact', 'inexact->exact',
            
            # Strings
            'string?', 'string-length', 'string-ref', 'string-set!',
            'string=?', 'string<?', 'string>?', 'string<=?', 'string>=?',
            'string-ci=?', 'string-ci<?', 'string-ci>?', 'string-ci<=?', 'string-ci>=?',
            'substring', 'string-append', 'string->list', 'list->string',
            'string-copy', 'string-fill!', 'string->number', 'number->string',
            'string->symbol', 'symbol->string', 'string-upcase', 'string-downcase',
            
            # Caracteres
            'char?', 'char=?', 'char<?', 'char>?', 'char<=?', 'char>=?',
            'char-ci=?', 'char-ci<?', 'char-ci>?', 'char-ci<=?', 'char-ci>=?',
            'char-alphabetic?', 'char-numeric?', 'char-whitespace?',
            'char-upper-case?', 'char-lower-case?', 'char->integer',
            'integer->char', 'char-upcase', 'char-downcase',
            
            # Vectores
            'vector?', 'make-vector', 'vector', 'vector-length',
            'vector-ref', 'vector-set!', 'vector->list', 'list->vector',
            'vector-fill!',
            
            # Símbolos
            'symbol?', 'symbol->string', 'string->symbol', 'gensym',
            
            # Booleanos
            'boolean?', 'not',
            
            # Tipos y predicados
            'eq?', 'eqv?', 'equal?', 'procedure?', 'symbol?', 'number?',
            'string?', 'char?', 'vector?', 'port?', 'input-port?', 'output-port?',
            
            # I/O
            'read', 'read-char', 'peek-char', 'eof-object?', 'char-ready?',
            'write', 'display', 'newline', 'write-char', 'load',
            'open-input-file', 'open-output-file', 'close-input-port',
            'close-output-port', 'current-input-port', 'current-output-port',
            
            # Conversiones
            'number->string', 'string->number', 'char->integer', 'integer->char',
            'symbol->string', 'string->symbol', 'list->vector', 'vector->list',
            
            # Error handling
            'error', 'raise', 'with-handlers'
        }
        
        # Operadores aritméticos y de comparación
        self.operadores = {
            '+', '-', '*', '/', '=', '<', '>', '<=', '>=',
            'quotient', 'remainder', 'modulo', 'gcd', 'lcm'
        }
        
        # Delimitadores (estructura fundamental de Lisp)
        self.delimitadores = {'(', ')', '[', ']', '{', '}'}
        
        # Caracteres especiales de Racket
        self.caracteres_especiales = {
            "'", "`", ",", ",@", "#", ".", ";"
        }
        
        # Inicialización de atributos de la máquina
        self.cinta = []
        self.posicion_cinta = 0
        self.buffer_token = ""
        self.tokens_procesados = []
    
    def es_caracter_valido(self, caracter: str) -> bool:
        """Verifica si un carácter pertenece al alfabeto válido de Racket"""
        return caracter in self.alfabeto
    
    def reiniciar_estado(self):
        """Reinicia la máquina al estado inicial"""
        self.estado_actual = EstadoMaquina.INICIAL
        self.buffer_token = ""
    
    def transicion(self, caracter: str) -> Tuple[EstadoMaquina, str]:
        """
        Función de transición de la Máquina de Turing para Racket
        Retorna (nuevo_estado, acción)
        """
        
        # Verificar si el carácter es válido
        if not self.es_caracter_valido(caracter):
            return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        estado_actual = self.estado_actual
        
        # Estado INICIAL - Punto de partida
        if estado_actual == EstadoMaquina.INICIAL:
            if caracter == ';':  # Comentario de línea
                return EstadoMaquina.COMENTARIO_LINEA_INICIADO, "LEER"
            elif caracter == '#':  # Inicio de varios literales especiales
                return EstadoMaquina.BOOLEAN_LITERAL_INICIADO, "LEER"
            elif caracter == "'":  # Símbolo citado
                return EstadoMaquina.SIMBOLO_INICIADO, "LEER"
            elif caracter == '"':  # String
                return EstadoMaquina.STRING_INICIADO, "LEER"
            elif caracter.isdigit() or caracter in '+-':  # Número
                return EstadoMaquina.NUMERO_INICIADO, "LEER"
            elif caracter in self.delimitadores:  # Delimitadores
                return EstadoMaquina.DELIMITADOR_DETECTADO, "ACEPTAR"
            elif caracter in ' \t\n\r':  # Espacios
                return EstadoMaquina.ESPACIO_DETECTADO, "ACEPTAR"
            elif self._es_inicio_identificador(caracter):  # Identificador/keyword
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            else:
                return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        # Estado KEYWORD_CANDIDATO - Leyendo posible keyword/identificador
        elif estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            if self._es_caracter_identificador(caracter):
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            else:
                # Fin del token, verificar tipo
                if self.buffer_token.rstrip() in self.keywords:
                    return EstadoMaquina.KEYWORD_CONFIRMADO, "ACEPTAR_RETROCEDER"
                else:
                    return EstadoMaquina.IDENTIFICADOR_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_INICIADO - Leyendo número
        elif estado_actual == EstadoMaquina.NUMERO_INICIADO:
            if caracter.isdigit():
                return EstadoMaquina.NUMERO_INICIADO, "LEER"
            elif caracter == '.':
                return EstadoMaquina.NUMERO_DECIMAL, "LEER"
            elif caracter == '/':
                return EstadoMaquina.NUMERO_FRACCION, "LEER"
            elif caracter in 'iI':  # Número complejo
                return EstadoMaquina.NUMERO_COMPLEJO, "LEER"
            else:
                return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_DECIMAL - Leyendo parte decimal
        elif estado_actual == EstadoMaquina.NUMERO_DECIMAL:
            if caracter.isdigit():
                return EstadoMaquina.NUMERO_DECIMAL, "LEER"
            elif caracter in 'iI':  # Complejo decimal
                return EstadoMaquina.NUMERO_COMPLEJO, "LEER"
            else:
                return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_FRACCION - Leyendo fracción
        elif estado_actual == EstadoMaquina.NUMERO_FRACCION:
            if caracter.isdigit():
                return EstadoMaquina.NUMERO_FRACCION, "LEER"
            else:
                return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estado NUMERO_COMPLEJO - Número complejo
        elif estado_actual == EstadoMaquina.NUMERO_COMPLEJO:
            return EstadoMaquina.NUMERO_COMPLETO, "ACEPTAR"
        
        # Estado STRING_INICIADO - Leyendo string
        elif estado_actual == EstadoMaquina.STRING_INICIADO:
            if caracter == '\\':
                return EstadoMaquina.STRING_ESCAPE, "LEER"
            elif caracter == '"':
                return EstadoMaquina.STRING_COMPLETO, "ACEPTAR"
            else:
                return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado STRING_ESCAPE - Carácter de escape en string
        elif estado_actual == EstadoMaquina.STRING_ESCAPE:
            return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado COMENTARIO_LINEA_INICIADO - Comentario de línea
        elif estado_actual == EstadoMaquina.COMENTARIO_LINEA_INICIADO:
            if caracter in '\n\r':
                return EstadoMaquina.COMENTARIO_COMPLETO, "ACEPTAR_RETROCEDER"
            else:
                return EstadoMaquina.COMENTARIO_LINEA_INICIADO, "LEER"
        
        # Estado BOOLEAN_LITERAL_INICIADO - Después de #
        elif estado_actual == EstadoMaquina.BOOLEAN_LITERAL_INICIADO:
            if caracter in 'tf':  # #t o #f (booleanos)
                return EstadoMaquina.BOOLEAN_LITERAL_COMPLETO, "ACEPTAR"
            elif caracter == '\\':  # #\ (carácter literal)
                return EstadoMaquina.CARACTER_LITERAL_INICIADO, "LEER"
            elif caracter == '|':  # #| (comentario de bloque)
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
            else:
                return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        # Estado CARACTER_LITERAL_INICIADO - Después de #\
        elif estado_actual == EstadoMaquina.CARACTER_LITERAL_INICIADO:
            # Cualquier carácter después de #\ es válido
            return EstadoMaquina.CARACTER_LITERAL_COMPLETO, "ACEPTAR"
        
        # Estado COMENTARIO_BLOQUE_INICIADO - Comentario #| ... |#
        elif estado_actual == EstadoMaquina.COMENTARIO_BLOQUE_INICIADO:
            if caracter == '|':
                return EstadoMaquina.COMENTARIO_BLOQUE_PIPE, "LEER"
            else:
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
        
        # Estado COMENTARIO_BLOQUE_PIPE - Después de | en comentario de bloque
        elif estado_actual == EstadoMaquina.COMENTARIO_BLOQUE_PIPE:
            if caracter == '#':  # |# cierra comentario
                return EstadoMaquina.COMENTARIO_COMPLETO, "ACEPTAR"
            elif caracter == '|':
                return EstadoMaquina.COMENTARIO_BLOQUE_PIPE, "LEER"
            else:
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
        
        # Estado SIMBOLO_INICIADO - Después de '
        elif estado_actual == EstadoMaquina.SIMBOLO_INICIADO:
            if self._es_caracter_identificador(caracter) or caracter == '(':
                return EstadoMaquina.SIMBOLO_INICIADO, "LEER"
            else:
                return EstadoMaquina.SIMBOLO_COMPLETO, "ACEPTAR_RETROCEDER"
        
        # Estados de aceptación - no deberían recibir más entrada
        else:
            return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
    
    def _es_inicio_identificador(self, caracter: str) -> bool:
        """Verifica si un carácter puede iniciar un identificador en Racket"""
        return (caracter.isalpha() or 
                caracter in '+-*/<>=!?:$%&^~@_λ')
    
    def _es_caracter_identificador(self, caracter: str) -> bool:
        """Verifica si un carácter puede ser parte de un identificador en Racket"""
        return (caracter.isalnum() or 
                caracter in '+-*/<>=!?:$%&^~@_-λ')
    
    def procesar_token_individual(self, token_texto: str, posicion: int) -> Token:
        """Procesa un token individual usando la máquina de Turing"""
        self.reiniciar_estado()
        self.buffer_token = ""
        
        # Verificaciones directas primero para optimización
        
        # 1. Strings
        if token_texto.startswith('"') and token_texto.endswith('"'):
            return Token(TipoToken.STRING, token_texto, posicion, True)
        
        # 2. Comentarios
        if token_texto.startswith(';') or (token_texto.startswith('#|') and token_texto.endswith('|#')):
            return Token(TipoToken.COMMENT, token_texto, posicion, True)
        
        # 3. Booleanos literales
        if token_texto in ['#t', '#f', '#true', '#false']:
            return Token(TipoToken.BOOLEAN, token_texto, posicion, True)
        
        # 4. Caracteres literales
        if token_texto.startswith('#\\') and len(token_texto) >= 3:
            return Token(TipoToken.CHARACTER, token_texto, posicion, True)
        
        # 5. Símbolos citados
        if token_texto.startswith("'"):
            return Token(TipoToken.SYMBOL, token_texto, posicion, True)
        
        # 6. Números
        if self._es_numero_racket(token_texto):
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        
        # 7. Delimitadores
        if token_texto in self.delimitadores:
            return Token(TipoToken.DELIMITER, token_texto, posicion, True)
        
        # 8. Keywords
        if token_texto in self.keywords:
            return Token(TipoToken.KEYWORD, token_texto, posicion, True)
        
        # 9. Built-ins
        if token_texto in self.builtins:
            return Token(TipoToken.BUILTIN, token_texto, posicion, True)
        
        # 10. Operadores
        if token_texto in self.operadores:
            return Token(TipoToken.OPERATOR, token_texto, posicion, True)
        
        # 11. Espacios en blanco
        if token_texto.isspace():
            return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
        
        # 12. Identificadores
        if self._es_identificador_valido_racket(token_texto):
            return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        
        # 13. Usar la máquina de Turing como respaldo
        return self._procesar_con_maquina_turing(token_texto, posicion)
    
    def _es_numero_racket(self, texto: str) -> bool:
        """Verifica si un texto es un número válido en Racket"""
        try:
            # Números complejos (terminan en i o I)
            if texto.endswith('i') or texto.endswith('I'):
                numero_parte = texto[:-1]
                if numero_parte:
                    float(numero_parte)
                return True
            
            # Fracciones (contienen /)
            if '/' in texto and not texto.startswith('/'):
                partes = texto.split('/')
                if len(partes) == 2:
                    int(partes[0])
                    int(partes[1])
                    return True
            
            # Números decimales y enteros
            if '.' in texto:
                float(texto)
            else:
                int(texto)
            return True
        except ValueError:
            return False
    
    def _es_identificador_valido_racket(self, texto: str) -> bool:
        """Verifica si un texto es un identificador válido en Racket"""
        if not texto:
            return False
        
        # Primer carácter
        if not self._es_inicio_identificador(texto[0]):
            return False
        
        # Resto de caracteres
        return all(self._es_caracter_identificador(c) for c in texto[1:])
    
    def _procesar_con_maquina_turing(self, token_texto: str, posicion: int) -> Token:
        """Procesamiento con Máquina de Turing como respaldo"""
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
                    # Verificar si es built-in
                    if token_texto in self.builtins:
                        return Token(TipoToken.BUILTIN, token_texto, posicion, True)
                    elif token_texto in self.operadores:
                        return Token(TipoToken.OPERATOR, token_texto, posicion, True)
                    else:
                        return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
                elif nuevo_estado in [EstadoMaquina.NUMERO_COMPLETO, EstadoMaquina.NUMERO_INICIADO, 
                                     EstadoMaquina.NUMERO_COMPLEJO]:
                    return Token(TipoToken.NUMBER, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.STRING_COMPLETO:
                    return Token(TipoToken.STRING, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.COMENTARIO_COMPLETO:
                    return Token(TipoToken.COMMENT, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.SIMBOLO_COMPLETO:
                    return Token(TipoToken.SYMBOL, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.CARACTER_LITERAL_COMPLETO:
                    return Token(TipoToken.CHARACTER, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.BOOLEAN_LITERAL_COMPLETO:
                    return Token(TipoToken.BOOLEAN, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.DELIMITADOR_DETECTADO:
                    return Token(TipoToken.DELIMITER, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.ESPACIO_DETECTADO:
                    return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
                
                break
            
            elif accion == "LEER":
                self.estado_actual = nuevo_estado
                continue
        
        # Clasificar por estado final si no hay aceptación explícita
        if self.estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            if token_texto in self.keywords:
                return Token(TipoToken.KEYWORD, token_texto, posicion, True)
            elif token_texto in self.builtins:
                return Token(TipoToken.BUILTIN, token_texto, posicion, True)
            elif token_texto in self.operadores:
                return Token(TipoToken.OPERATOR, token_texto, posicion, True)
            else:
                return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        
        return Token(TipoToken.UNKNOWN, token_texto, posicion, False)
    
    def tokenizar_archivo(self, contenido_archivo: str) -> List[Token]:
        """
        Proceso completo de tokenización Racket:
        1. Cargar archivo
        2. Separar por tokens respetando S-expresiones
        3. Procesar cada token con la máquina de Turing
        """
        
        print(f"📁 Paso 1: Archivo Racket cargado ({len(contenido_archivo)} caracteres)")
        
        # Separación inteligente por tokens
        tokens_texto = self._separar_tokens_racket(contenido_archivo)
        print(f"🔍 Paso 2: Separados en {len(tokens_texto)} tokens Racket")
        
        # Procesar cada token con la máquina de Turing
        tokens_procesados = []
        tokens_rechazados = []
        
        print("⚙️  Paso 3: Procesando tokens Racket con Máquina de Turing...")
        
        for i, (texto_token, posicion) in enumerate(tokens_texto):
            if not texto_token.strip():
                if texto_token:
                    token = Token(TipoToken.WHITESPACE, texto_token, posicion, True)
                    tokens_procesados.append(token)
                continue
            
            token = self.procesar_token_individual(texto_token, posicion)
            tokens_procesados.append(token)
            
            if not token.valido:
                tokens_rechazados.append(token)
                print(f"❌ Token Racket rechazado: '{token.valor}' en posición {token.posicion}")
        
        print(f"✅ Procesamiento Racket completado:")
        print(f"   - Tokens válidos: {len(tokens_procesados) - len(tokens_rechazados)}")
        print(f"   - Tokens rechazados: {len(tokens_rechazados)}")
        
        return tokens_procesados
    
    def _separar_tokens_racket(self, texto: str) -> List[Tuple[str, int]]:
        """Separación inteligente de tokens específica para Racket"""
        tokens = []
        i = 0
        
        while i < len(texto):
            # Espacios en blanco
            if texto[i] in ' \t':
                inicio = i
                while i < len(texto) and texto[i] in ' \t':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Saltos de línea
            if texto[i] in '\n\r':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Strings
            if texto[i] == '"':
                inicio = i
                i += 1
                while i < len(texto) and texto[i] != '"':
                    if texto[i] == '\\':  # Escape
                        i += 2 if i + 1 < len(texto) else 1
                    else:
                        i += 1
                if i < len(texto):
                    i += 1  # Incluir quote de cierre
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Comentarios de línea ;
            if texto[i] == ';':
                inicio = i
                while i < len(texto) and texto[i] not in '\n\r':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Comentarios de bloque #| |#
            if i < len(texto) - 1 and texto[i:i+2] == '#|':
                inicio = i
                i += 2
                while i < len(texto) - 1:
                    if texto[i:i+2] == '|#':
                        i += 2
                        break
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Literales especiales que empiezan con #
            if texto[i] == '#':
                inicio = i
                i += 1
                if i < len(texto):
                    if texto[i] in 'tf':  # #t #f
                        i += 1
                        # Verificar #true #false
                        if texto[inicio:i] == '#t' and i < len(texto) - 3 and texto[i:i+3] == 'rue':
                            i += 3
                        elif texto[inicio:i] == '#f' and i < len(texto) - 4 and texto[i:i+4] == 'alse':
                            i += 4
                    elif texto[i] == '\\':  # #\c (carácter literal)
                        i += 1
                        if i < len(texto):
                            # Caracteres especiales como #\newline, #\space
                            if texto[i:i+7] == 'newline':
                                i += 7
                            elif texto[i:i+5] == 'space':
                                i += 5
                            elif texto[i:i+3] == 'tab':
                                i += 3
                            else:
                                i += 1  # Un solo carácter
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Símbolos citados '
            if texto[i] == "'":
                inicio = i
                i += 1
                # Leer el símbolo que sigue
                while i < len(texto) and (self._es_caracter_identificador(texto[i]) or texto[i] == '('):
                    i += 1
                    if texto[i-1] == '(':  # 'lista citada
                        nivel_parentesis = 1
                        while i < len(texto) and nivel_parentesis > 0:
                            if texto[i] == '(':
                                nivel_parentesis += 1
                            elif texto[i] == ')':
                                nivel_parentesis -= 1
                            i += 1
                        break
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Delimitadores
            if texto[i] in '()[]{}':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Números (incluyendo negativos, decimales, fracciones, complejos)
            if (texto[i].isdigit() or 
                (texto[i] in '+-' and i + 1 < len(texto) and texto[i + 1].isdigit())):
                inicio = i
                if texto[i] in '+-':
                    i += 1
                
                # Parte entera
                while i < len(texto) and texto[i].isdigit():
                    i += 1
                
                # Parte decimal
                if i < len(texto) and texto[i] == '.':
                    i += 1
                    while i < len(texto) and texto[i].isdigit():
                        i += 1
                
                # Fracción
                elif i < len(texto) and texto[i] == '/':
                    i += 1
                    while i < len(texto) and texto[i].isdigit():
                        i += 1
                
                # Número complejo
                if i < len(texto) and texto[i] in 'iI':
                    i += 1
                
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Identificadores/Keywords
            if self._es_inicio_identificador(texto[i]):
                inicio = i
                while i < len(texto) and self._es_caracter_identificador(texto[i]):
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Carácter individual no reconocido
            tokens.append((texto[i], i))
            i += 1
        
        return tokens

class RacketHTMLGenerator:
    """Generador de HTML para el resaltado de sintaxis Racket con colores específicos"""
    
    # Delimitadores con colores específicos para resaltar estructura
    DELIMITER_CSS_MAP = {
        '(': 'racket-del-paren-open',
        ')': 'racket-del-paren-close',
        '[': 'racket-del-bracket-open',
        ']': 'racket-del-bracket-close',
        '{': 'racket-del-brace-open',
        '}': 'racket-del-brace-close'
    }
    
    # Keywords categorizados para diferentes colores
    DEFINITION_KEYWORDS = {'define', 'define-values', 'define-syntax', 'define-struct', 'lambda', 'λ'}
    CONTROL_KEYWORDS = {'if', 'cond', 'case', 'when', 'unless', 'and', 'or', 'not'}
    BINDING_KEYWORDS = {'let', 'let*', 'letrec', 'let-values', 'let*-values'}
    MODULE_KEYWORDS = {'module', 'require', 'provide'}
    
    # Funciones por categoría
    LIST_FUNCTIONS = {'cons', 'car', 'cdr', 'list', 'append', 'reverse', 'length'}
    NUMERIC_FUNCTIONS = {'max', 'min', 'abs', '+', '-', '*', '/', '=', '<', '>', '<=', '>='}
    
    def generar_css(self) -> str:
        """CSS para el resaltado de sintaxis Racket con temática funcional"""
        return """
        <style>
        .racket-code-container {
            font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e6e6e6;
            border: 2px solid #4a90e2;
            border-radius: 12px;
            padding: 25px;
            margin: 15px 0;
            overflow-x: auto;
            line-height: 1.8;
            box-shadow: 0 8px 32px rgba(74, 144, 226, 0.2);
            position: relative;
        }
        
        .racket-code-container::before {
            content: "λ Racket";
            position: absolute;
            top: -12px;
            left: 20px;
            background: linear-gradient(45deg, #4a90e2, #7bb3f2);
            color: #0f0f23;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        /* Keywords de Definición - Púrpura brillante */
        .racket-keyword-definition { 
            color: #c678dd; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(198, 120, 221, 0.5);
        }
        
        /* Keywords de Control - Azul cyan */
        .racket-keyword-control { 
            color: #56b6c2; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(86, 182, 194, 0.5);
        }
        
        /* Keywords de Binding - Verde esmeralda */
        .racket-keyword-binding { 
            color: #98c379; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(152, 195, 121, 0.5);
        }
        
        /* Keywords de Módulo - Amarillo dorado */
        .racket-keyword-module { 
            color: #e5c07b; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(229, 192, 123, 0.5);
        }
        
        /* Keywords Generales - Azul claro */
        .racket-keyword { 
            color: #61afef; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(97, 175, 239, 0.5);
        }
        
        /* Built-ins de Listas - Rosa neón */
        .racket-builtin-list { 
            color: #ff79c6; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(255, 121, 198, 0.5);
        }
        
        /* Built-ins Numéricos - Naranja vibrante */
        .racket-builtin-numeric { 
            color: #ffb86c; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(255, 184, 108, 0.5);
        }
        
        /* Built-ins Generales - Cyan claro */
        .racket-builtin { 
            color: #8be9fd; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(139, 233, 253, 0.5);
        }
        
        /* Operadores - Rojo coral */
        .racket-operator { 
            color: #ff5555; 
            font-weight: bold; 
            font-size: 1.1em;
            text-shadow: 0 0 5px rgba(255, 85, 85, 0.5);
        }
        
        /* Strings - Verde menta */
        .racket-string { 
            color: #50fa7b; 
            background: rgba(80, 250, 123, 0.1);
            border-radius: 3px;
            padding: 1px 2px;
        }
        
        /* Números - Magenta brillante */
        .racket-number { 
            color: #bd93f9; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(189, 147, 249, 0.5);
        }
        
        /* Booleanos - Verde lima/Rojo */
        .racket-boolean-true { 
            color: #50fa7b; 
            font-weight: bold; 
            background: rgba(80, 250, 123, 0.15);
            border-radius: 3px;
            padding: 1px 4px;
        }
        .racket-boolean-false { 
            color: #ff5555; 
            font-weight: bold; 
            background: rgba(255, 85, 85, 0.15);
            border-radius: 3px;
            padding: 1px 4px;
        }
        
        /* Caracteres Literales - Amarillo brillante */
        .racket-character { 
            color: #f1fa8c; 
            font-weight: bold; 
            background: rgba(241, 250, 140, 0.1);
            border-radius: 3px;
            padding: 1px 2px;
        }
        
        /* Símbolos - Cyan brillante */
        .racket-symbol { 
            color: #8be9fd; 
            font-style: italic; 
            font-weight: bold;
        }
        
        /* Comentarios - Gris azulado */
        .racket-comment { 
            color: #6272a4; 
            font-style: italic; 
            background: rgba(98, 114, 164, 0.1);
            border-radius: 3px;
            padding: 1px 2px;
        }
        
        /* Identificadores - Blanco suave */
        .racket-identifier { 
            color: #f8f8f2; 
        }
        
        /* Delimitadores con colores únicos y efectos visuales */
        .racket-del-paren-open { 
            color: #ff79c6; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(255, 121, 198, 0.6);
        }
        .racket-del-paren-close { 
            color: #ff79c6; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(255, 121, 198, 0.6);
        }
        .racket-del-bracket-open { 
            color: #50fa7b; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(80, 250, 123, 0.6);
        }
        .racket-del-bracket-close { 
            color: #50fa7b; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(80, 250, 123, 0.6);
        }
        .racket-del-brace-open { 
            color: #ffb86c; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(255, 184, 108, 0.6);
        }
        .racket-del-brace-close { 
            color: #ffb86c; 
            font-weight: bold; 
            font-size: 1.3em; 
            text-shadow: 0 0 8px rgba(255, 184, 108, 0.6);
        }
        
        /* Espacios en blanco */
        .racket-whitespace { background-color: transparent; }
        
        /* Tokens desconocidos */
        .racket-unknown { 
            color: #ff5555; 
            background: rgba(255, 85, 85, 0.2); 
            border: 2px solid #ff5555;
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: bold;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .racket-stats {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-left: 4px solid #4a90e2;
            color: #e6e6e6;
            padding: 20px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3);
        }
        
        .racket-stats h3 {
            margin-top: 0;
            color: #4a90e2;
            text-shadow: 0 0 5px rgba(74, 144, 226, 0.5);
        }
        
        /* Leyenda de colores para Racket */
        .racket-color-legend {
            background: linear-gradient(135deg, #16213e 0%, #0f0f23 100%);
            border: 2px solid #4a90e2;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            font-size: 13px;
            color: #e6e6e6;
            box-shadow: 0 6px 24px rgba(74, 144, 226, 0.3);
        }
        
        .racket-legend-category {
            margin-bottom: 18px;
            padding: 10px;
            background: rgba(74, 144, 226, 0.1);
            border-radius: 8px;
        }
        
        .racket-legend-item {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 8px;
        }
        
        .racket-legend-category h4 {
            color: #4a90e2;
            margin-bottom: 10px;
            font-size: 15px;
            text-shadow: 0 0 5px rgba(74, 144, 226, 0.5);
        }
        
        /* Efectos hover para interactividad */
        .racket-code-container span:hover {
            background: rgba(74, 144, 226, 0.2);
            border-radius: 3px;
            transition: all 0.2s ease;
        }
        </style>
        """
    
    def tokens_a_html(self, tokens: List[Token]) -> str:
        """Convierte tokens Racket a HTML resaltado con colores específicos"""
        html_parts = []
        
        for token in tokens:
            valor_escapado = (token.valor.replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;')
                                        .replace('"', '&quot;'))
            
            # Determinar clase CSS específica basada en el tipo y valor del token
            css_class = self._determinar_clase_css_racket(token)
            
            if token.tipo == TipoToken.WHITESPACE:
                # Preservar espacios y tabs
                valor_escapado = valor_escapado.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                html_parts.append(valor_escapado)
            else:
                html_parts.append(f'<span class="{css_class}">{valor_escapado}</span>')
        
        return ''.join(html_parts)
    
    def _determinar_clase_css_racket(self, token: Token) -> str:
        """Determina la clase CSS específica para cada token Racket"""
        
        if token.tipo == TipoToken.KEYWORD:
            # Categorizar keywords por función
            if token.valor in self.DEFINITION_KEYWORDS:
                return 'racket-keyword-definition'
            elif token.valor in self.CONTROL_KEYWORDS:
                return 'racket-keyword-control'
            elif token.valor in self.BINDING_KEYWORDS:
                return 'racket-keyword-binding'
            elif token.valor in self.MODULE_KEYWORDS:
                return 'racket-keyword-module'
            return 'racket-keyword'
        
        elif token.tipo == TipoToken.BUILTIN:
            # Categorizar built-ins por función
            if token.valor in self.LIST_FUNCTIONS:
                return 'racket-builtin-list'
            elif token.valor in self.NUMERIC_FUNCTIONS:
                return 'racket-builtin-numeric'
            return 'racket-builtin'
        
        elif token.tipo == TipoToken.OPERATOR:
            return 'racket-operator'
        
        elif token.tipo == TipoToken.STRING:
            return 'racket-string'
        
        elif token.tipo == TipoToken.NUMBER:
            return 'racket-number'
        
        elif token.tipo == TipoToken.BOOLEAN:
            if token.valor in ['#t', '#true']:
                return 'racket-boolean-true'
            else:
                return 'racket-boolean-false'
        
        elif token.tipo == TipoToken.CHARACTER:
            return 'racket-character'
        
        elif token.tipo == TipoToken.SYMBOL:
            return 'racket-symbol'
        
        elif token.tipo == TipoToken.COMMENT:
            return 'racket-comment'
        
        elif token.tipo == TipoToken.IDENTIFIER:
            return 'racket-identifier'
        
        elif token.tipo == TipoToken.DELIMITER:
            return self.DELIMITER_CSS_MAP.get(token.valor, 'racket-delimiter')
        
        elif token.tipo == TipoToken.WHITESPACE:
            return 'racket-whitespace'
        
        else:
            return 'racket-unknown'

class RacketResaltadorSintaxis:
    """Clase principal del resaltador de sintaxis Racket basado en Máquina de Turing"""
    
    def __init__(self):
        self.maquina_turing = RacketTuringMachine()
        self.generador_html = RacketHTMLGenerator()
    
    def procesar_archivo(self, archivo_entrada: str, archivo_salida: str):
        """Procesa un archivo TXT con código Racket y genera HTML resaltado"""
        
        try:
            # Verificar que el archivo de entrada sea .txt
            if not archivo_entrada.lower().endswith('.txt'):
                print(f"❌ Error: Se esperaba un archivo .txt, recibido: {archivo_entrada}")
                return
            
            # Cargar archivo TXT
            print(f"🚀 Iniciando procesamiento de archivo Racket: {archivo_entrada}")
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            print(f"📄 Archivo Racket cargado exitosamente ({len(contenido)} caracteres)")
            print(f"🔍 Analizando código Racket/Lisp contenido en el archivo...")
            
            # Procesar con la Máquina de Turing
            tokens = self.maquina_turing.tokenizar_archivo(contenido)
            
            # Generar estadísticas
            stats = self._generar_estadisticas_racket(tokens)
            
            # Generar HTML
            css = self.generador_html.generar_css()
            html_codigo = self.generador_html.tokens_a_html(tokens)
            
            # Documento HTML completo
            html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Léxico Racket - {archivo_entrada}</title>
    {css}
</head>
<body style="background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%); color: #e6e6e6; font-family: Arial, sans-serif; margin: 0; padding: 20px; min-height: 100vh;">
    <h1 style="color: #4a90e2; text-align: center; text-shadow: 0 0 10px rgba(74, 144, 226, 0.5); margin-bottom: 10px;">
        λ Análisis Léxico Racket con Máquina de Turing
    </h1>
    <h2 style="color: #50fa7b; text-align: center; margin-bottom: 30px;">
        Archivo procesado: {archivo_entrada}
    </h2>
    <p style="text-align: center; margin-bottom: 30px;">
        <em style="color: #6272a4;">Código Racket (Lisp/Scheme) analizado usando principios de Máquina de Turing</em>
    </p>
    
    <div class="racket-color-legend">
        <h3 style="color: #4a90e2; margin-top: 0; text-align: center; text-shadow: 0 0 5px rgba(74, 144, 226, 0.5);">
            🎨 Leyenda de Colores Racket (Programación Funcional)
        </h3>
        
        <div class="racket-legend-category">
            <h4>Keywords por Función:</h4>
            <span class="racket-legend-item"><span class="racket-keyword-definition">define lambda λ</span> (Definiciones)</span>
            <span class="racket-legend-item"><span class="racket-keyword-control">if cond when unless</span> (Control)</span>
            <span class="racket-legend-item"><span class="racket-keyword-binding">let let* letrec</span> (Binding)</span>
            <span class="racket-legend-item"><span class="racket-keyword-module">module require provide</span> (Módulos)</span>
        </div>
        
        <div class="racket-legend-category">
            <h4>Built-ins por Categoría:</h4>
            <span class="racket-legend-item"><span class="racket-builtin-list">cons car cdr list append</span> (Listas)</span>
            <span class="racket-legend-item"><span class="racket-builtin-numeric">+ - * / = < ></span> (Numéricos)</span>
            <span class="racket-legend-item"><span class="racket-builtin">map filter string? number?</span> (Generales)</span>
        </div>
        
        <div class="racket-legend-category">
            <h4>Literales y Tipos:</h4>
            <span class="racket-legend-item"><span class="racket-string">"strings"</span> (Cadenas)</span>
            <span class="racket-legend-item"><span class="racket-number">123 3.14 1/2 3+4i</span> (Números)</span>
            <span class="racket-legend-item"><span class="racket-boolean-true">#t</span> <span class="racket-boolean-false">#f</span> (Booleanos)</span>
            <span class="racket-legend-item"><span class="racket-character">#\\c #\\newline</span> (Caracteres)</span>
            <span class="racket-legend-item"><span class="racket-symbol">'symbol</span> (Símbolos)</span>
        </div>
        
        <div class="racket-legend-category">
            <h4>Estructura del Código:</h4>
            <span class="racket-legend-item"><span class="racket-del-paren-open">(</span><span class="racket-del-paren-close">)</span> S-expresiones</span>
            <span class="racket-legend-item"><span class="racket-del-bracket-open">[</span><span class="racket-del-bracket-close">]</span> Listas alternativas</span>
            <span class="racket-legend-item"><span class="racket-del-brace-open">{{</span><span class="racket-del-brace-close">}}</span> Diccionarios</span>
            <span class="racket-legend-item"><span class="racket-comment">; comentarios</span></span>
        </div>
        
        <div style="text-align: center; margin-top: 15px; color: #6272a4;">
            <p><strong>Características únicas de Racket:</strong></p>
            <p>• Sintaxis uniforme basada en S-expresiones • Notación prefija • Soporte para macros avanzadas</p>
            <p>• Números complejos y fracciones • Módulos y contratos • Programación funcional pura</p>
        </div>
    </div>
    
    <div class="racket-stats">
        <h3>📊 Estadísticas del Análisis Racket</h3>
        {stats}
    </div>
    
    <div class="racket-code-container">
        {html_codigo}
    </div>
    
    <div style="margin-top: 30px; color: #6272a4; font-size: 12px; text-align: center; background: rgba(74, 144, 226, 0.1); padding: 15px; border-radius: 8px;">
        <p><strong>λ Generado por Resaltador de Sintaxis Racket - Máquina de Turing</strong></p>
        <p>Implementación basada en Estados y Transiciones Deterministas para Racket/Lisp/Scheme</p>
        <p>Entrada: Archivo TXT con Racket → Salida: HTML con sintaxis resaltada</p>
        <p><strong>🎨 Colores optimizados para programación funcional y S-expresiones</strong></p>
        <p>Compatible con: Racket, DrRacket, Scheme R6RS, Common Lisp (parcial)</p>
        <p><em>"Code is data, data is code" - Filosofía Lisp</em></p>
    </div>
</body>
</html>"""
            
            # Guardar archivo HTML
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write(html_completo)
            
            print(f"✅ Procesamiento Racket completado exitosamente!")
            print(f"📄 Archivo Racket procesado: {archivo_entrada}")
            print(f"🌐 Archivo HTML generado: {archivo_salida}")
            print(f"🎯 Tokens Racket identificados: {len(tokens)}")
            print(f"λ Características detectadas: S-expresiones, literales especiales, funciones built-in")
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo Racket: {archivo_entrada}")
        except Exception as e:
            print(f"❌ Error durante el procesamiento del archivo Racket: {e}")
    
    def _generar_estadisticas_racket(self, tokens: List[Token]) -> str:
        """Genera estadísticas específicas del análisis de tokens Racket"""
        conteo_tipos = {}
        keywords_encontrados = set()
        builtins_encontrados = set()
        delimitadores_conteo = {'(': 0, ')': 0, '[': 0, ']': 0, '{': 0, '}': 0}
        tokens_invalidos = []
        
        for token in tokens:
            if token.tipo not in conteo_tipos:
                conteo_tipos[token.tipo] = 0
            conteo_tipos[token.tipo] += 1
            
            if token.tipo == TipoToken.KEYWORD:
                keywords_encontrados.add(token.valor)
            elif token.tipo == TipoToken.BUILTIN:
                builtins_encontrados.add(token.valor)
            elif token.tipo == TipoToken.DELIMITER and token.valor in delimitadores_conteo:
                delimitadores_conteo[token.valor] += 1
            
            if not token.valido:
                tokens_invalidos.append(token)
        
        stats_html = f"<p><strong>Total de tokens Racket procesados:</strong> {len(tokens)}</p>"
        stats_html += f"<p><strong>Keywords Racket únicos encontrados:</strong> {len(keywords_encontrados)}</p>"
        stats_html += f"<p><strong>Built-ins Racket únicos encontrados:</strong> {len(builtins_encontrados)}</p>"
        
        # Análisis de balance de delimitadores
        balance_parentesis = delimitadores_conteo['('] - delimitadores_conteo[')']
        balance_corchetes = delimitadores_conteo['['] - delimitadores_conteo[']']
        balance_llaves = delimitadores_conteo['{'] - delimitadores_conteo['}']
        
        stats_html += "<p><strong>Balance de delimitadores (característica clave de Lisp):</strong></p>"
        stats_html += f"<ul>"
        stats_html += f"<li>Paréntesis: {delimitadores_conteo['(']} aperturas, {delimitadores_conteo[')']} cierres "
        stats_html += f"({'✅ Balanceados' if balance_parentesis == 0 else f'❌ Desbalanceados ({balance_parentesis:+d})'})</li>"
        stats_html += f"<li>Corchetes: {delimitadores_conteo['[']} aperturas, {delimitadores_conteo[']']} cierres "
        stats_html += f"({'✅ Balanceados' if balance_corchetes == 0 else f'❌ Desbalanceados ({balance_corchetes:+d})'})</li>"
        stats_html += f"<li>Llaves: {delimitadores_conteo['{']} aperturas, {delimitadores_conteo['}']} cierres "
        stats_html += f"({'✅ Balanceados' if balance_llaves == 0 else f'❌ Desbalanceados ({balance_llaves:+d})'})</li>"
        stats_html += "</ul>"
        
        stats_html += "<p><strong>Distribución por tipo de token:</strong></p><ul>"
        
        for tipo, cantidad in sorted(conteo_tipos.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / len(tokens)) * 100
            stats_html += f"<li>{tipo.value}: {cantidad} ({porcentaje:.1f}%)</li>"
        
        stats_html += "</ul>"
        
        # Mostrar algunos keywords encontrados
        if keywords_encontrados:
            keywords_list = sorted(list(keywords_encontrados))[:12]
            stats_html += f"<p><strong>Keywords Racket detectados (muestra):</strong> {', '.join(keywords_list)}"
            if len(keywords_encontrados) > 12:
                stats_html += f" y {len(keywords_encontrados) - 12} más..."
            stats_html += "</p>"
        
        # Mostrar built-ins encontrados
        if builtins_encontrados:
            builtins_list = sorted(list(builtins_encontrados))[:10]
            stats_html += f"<p><strong>Built-ins Racket detectados:</strong> {', '.join(builtins_list)}"
            if len(builtins_encontrados) > 10:
                stats_html += f" y {len(builtins_encontrados) - 10} más..."
            stats_html += "</p>"
        
        if tokens_invalidos:
            stats_html += f"<p><strong>⚠️ Tokens inválidos encontrados:</strong> {len(tokens_invalidos)}</p>"
            stats_html += "<ul>"
            for token in tokens_invalidos[:5]:
                stats_html += f"<li>'{token.valor}' en posición {token.posicion}</li>"
            if len(tokens_invalidos) > 5:
                stats_html += f"<li>... y {len(tokens_invalidos) - 5} más</li>"
            stats_html += "</ul>"
        
        return stats_html

def main():
    """Función principal del resaltador Racket"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Uso: python racket_turing_highlighter.py <archivo.txt> [salida.html]")
        print("📝 Ejemplo: python racket_turing_highlighter.py programa.txt resultado_racket.html")
        print("📄 El archivo de entrada debe ser un .txt que contenga código Racket")
        print("λ Soporta: Racket, DrRacket, Scheme R6RS, características Lisp")
        print("🎯 Especializado en: S-expresiones, macros, programación funcional")
        return
    
    archivo_entrada = sys.argv[1]
    
    # Verificar que la entrada sea un archivo .txt
    if not archivo_entrada.lower().endswith('.txt'):
        print("❌ Error: El archivo de entrada debe ser un archivo .txt")
        print("📝 Ejemplo: python racket_turing_highlighter.py mi_programa.txt")
        return
    
    # Generar nombre de salida basado en el archivo .txt
    if len(sys.argv) > 2:
        archivo_salida = sys.argv[2]
    else:
        # Cambiar .txt por _racket_highlighted.html
        archivo_salida = archivo_entrada.replace('.txt', '_racket_highlighted.html')
    
    resaltador = RacketResaltadorSintaxis()
    resaltador.procesar_archivo(archivo_entrada, archivo_salida)

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print(f"λ Procesamiento completado en {time.time() - start_time:.4f} segundos")