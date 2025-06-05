"""
Resaltador de Sintaxis SQL basado en Máquina de Turing
Implementación con estados explícitos y transiciones deterministas
Adaptado para el lenguaje SQL con soporte completo de palabras reservadas
"""

import string
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class EstadoMaquina(Enum):
    """Estados posibles de la Máquina de Turing para SQL"""
    INICIAL = "INICIAL"
    KEYWORD_CANDIDATO = "KEYWORD_CANDIDATO"
    KEYWORD_CONFIRMADO = "KEYWORD_CONFIRMADO"
    STRING_INICIADO = "STRING_INICIADO"
    STRING_ESCAPE = "STRING_ESCAPE"
    STRING_COMPLETO = "STRING_COMPLETO"
    NUMERO_INICIADO = "NUMERO_INICIADO"
    NUMERO_DECIMAL = "NUMERO_DECIMAL"
    NUMERO_COMPLETO = "NUMERO_COMPLETO"
    COMENTARIO_LINEA_INICIADO = "COMENTARIO_LINEA_INICIADO"
    COMENTARIO_BLOQUE_INICIADO = "COMENTARIO_BLOQUE_INICIADO"
    COMENTARIO_BLOQUE_ASTERISCO = "COMENTARIO_BLOQUE_ASTERISCO"
    COMENTARIO_COMPLETO = "COMENTARIO_COMPLETO"
    OPERADOR_INICIADO = "OPERADOR_INICIADO"
    OPERADOR_COMPLETO = "OPERADOR_COMPLETO"
    IDENTIFICADOR_INICIADO = "IDENTIFICADOR_INICIADO"
    IDENTIFICADOR_COMPLETO = "IDENTIFICADOR_COMPLETO"
    DELIMITADOR_DETECTADO = "DELIMITADOR_DETECTADO"
    ESPACIO_DETECTADO = "ESPACIO_DETECTADO"
    VARIABLE_INICIADA = "VARIABLE_INICIADA"
    VARIABLE_COMPLETA = "VARIABLE_COMPLETA"
    NO_ACEPTACION = "NO_ACEPTACION"
    ACEPTACION = "ACEPTACION"

class TipoToken(Enum):
    """Tipos de tokens reconocidos en SQL"""
    KEYWORD = "keyword"
    STRING = "string"
    NUMBER = "number"
    COMMENT = "comment"
    OPERATOR = "operator"
    IDENTIFIER = "identifier"
    DELIMITER = "delimiter"
    WHITESPACE = "whitespace"
    VARIABLE = "variable"
    FUNCTION = "function"
    DATATYPE = "datatype"
    UNKNOWN = "unknown"

@dataclass
class Token:
    """Representación de un token procesado"""
    tipo: TipoToken
    valor: str
    posicion: int
    valido: bool = True

class SQLTuringMachine:
    """Máquina de Turing para análisis léxico de SQL"""
    
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
            EstadoMaquina.COMENTARIO_LINEA_INICIADO,
            EstadoMaquina.COMENTARIO_BLOQUE_INICIADO,
            EstadoMaquina.COMENTARIO_BLOQUE_ASTERISCO,
            EstadoMaquina.COMENTARIO_COMPLETO,
            EstadoMaquina.OPERADOR_INICIADO,
            EstadoMaquina.OPERADOR_COMPLETO,
            EstadoMaquina.IDENTIFICADOR_INICIADO,
            EstadoMaquina.IDENTIFICADOR_COMPLETO,
            EstadoMaquina.DELIMITADOR_DETECTADO,
            EstadoMaquina.ESPACIO_DETECTADO,
            EstadoMaquina.VARIABLE_INICIADA,
            EstadoMaquina.VARIABLE_COMPLETA,
            EstadoMaquina.NO_ACEPTACION,
            EstadoMaquina.ACEPTACION
        }
        
        # Estado actual de la máquina
        self.estado_actual = EstadoMaquina.INICIAL
        
        # Alfabeto válido para SQL
        self.alfabeto = set(string.ascii_letters + string.digits + '_."\'`@#\t\n\r+-*/<>=!()[]{},:;')
        
        # Palabras reservadas de SQL (Standard SQL + extensiones comunes)
        self.keywords = {
            # DML (Data Manipulation Language)
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH',
            'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER',
            'ON', 'USING', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC',
            'LIMIT', 'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT', 'ALL', 'DISTINCT',
            'INTO', 'VALUES', 'SET',
            
            # DDL (Data Definition Language)
            'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'RENAME',
            'TABLE', 'VIEW', 'INDEX', 'SEQUENCE', 'SCHEMA', 'DATABASE',
            'CONSTRAINT', 'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES',
            'UNIQUE', 'CHECK', 'DEFAULT', 'AUTO_INCREMENT',
            'ADD', 'MODIFY', 'CHANGE', 'COLUMN',
            
            # DCL (Data Control Language)
            'GRANT', 'REVOKE', 'DENY',
            
            # TCL (Transaction Control Language)
            'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'BEGIN', 'START', 'TRANSACTION',
            
            # Tipos de datos
            'INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT',
            'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
            'CHAR', 'VARCHAR', 'TEXT', 'NCHAR', 'NVARCHAR',
            'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'YEAR',
            'BOOLEAN', 'BOOL', 'BIT', 'BINARY', 'VARBINARY',
            'BLOB', 'CLOB', 'JSON', 'XML',
            
            # Operadores lógicos
            'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE',
            'IS', 'NULL', 'TRUE', 'FALSE',
            
            # Funciones de agregado
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE',
            
            # Funciones de ventana
            'OVER', 'PARTITION', 'ROWS', 'RANGE', 'UNBOUNDED', 'PRECEDING',
            'FOLLOWING', 'CURRENT', 'ROW',
            
            # Condicionales
            'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'IF', 'ELSEIF', 'ENDIF',
            
            # Otros
            'AS', 'ALIAS', 'CAST', 'CONVERT', 'EXTRACT', 'SUBSTRING',
            'TRIM', 'COALESCE', 'NULLIF', 'GREATEST', 'LEAST',
            'EXPLAIN', 'DESCRIBE', 'SHOW', 'USE', 'CALL', 'PROCEDURE',
            'FUNCTION', 'TRIGGER', 'CURSOR', 'DECLARE', 'OPEN', 'FETCH', 'CLOSE',
            'WHILE', 'LOOP', 'FOR', 'REPEAT', 'UNTIL', 'LEAVE', 'ITERATE',
            'HANDLER', 'CONDITION', 'SQLSTATE', 'SQLEXCEPTION', 'SQLWARNING',
            'CONTINUE', 'EXIT', 'UNDO'
        }
        
        # Funciones comunes de SQL
        self.functions = {
            # Funciones de cadena
            'CONCAT', 'LENGTH', 'UPPER', 'LOWER', 'LTRIM', 'RTRIM', 'TRIM',
            'SUBSTRING', 'SUBSTR', 'REPLACE', 'REVERSE', 'LEFT', 'RIGHT',
            'CHARINDEX', 'POSITION', 'LOCATE', 'INSTR', 'LPAD', 'RPAD',
            
            # Funciones de fecha
            'NOW', 'CURDATE', 'CURTIME', 'TODAY', 'SYSDATE', 'GETDATE',
            'DATEADD', 'DATEDIFF', 'DATEPART', 'YEAR', 'MONTH', 'DAY',
            'HOUR', 'MINUTE', 'SECOND', 'DAYOFWEEK', 'DAYOFYEAR',
            'WEEK', 'QUARTER', 'LAST_DAY', 'DATE_FORMAT', 'STR_TO_DATE',
            
            # Funciones matemáticas
            'ABS', 'CEIL', 'CEILING', 'FLOOR', 'ROUND', 'TRUNCATE', 'TRUNC',
            'MOD', 'POWER', 'POW', 'SQRT', 'EXP', 'LOG', 'LOG10', 'LN',
            'SIN', 'COS', 'TAN', 'ASIN', 'ACOS', 'ATAN', 'ATAN2',
            'DEGREES', 'RADIANS', 'PI', 'RAND', 'RANDOM', 'SIGN',
            
            # Funciones de conversión
            'CAST', 'CONVERT', 'TO_CHAR', 'TO_DATE', 'TO_NUMBER',
            'FORMAT', 'PARSE', 'TRY_CAST', 'TRY_CONVERT',
            
            # Funciones condicionales
            'COALESCE', 'ISNULL', 'NULLIF', 'IIF', 'CHOOSE',
            'GREATEST', 'LEAST',
            
            # Funciones de ventana
            'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'PERCENT_RANK',
            'CUME_DIST', 'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE',
            'NTH_VALUE'
        }
        
        # Operadores de SQL
        self.operadores = {
            # Aritméticos
            '+', '-', '*', '/', '%',
            # Comparación
            '=', '!=', '<>', '<', '>', '<=', '>=',
            # Lógicos
            '||', '&&',
            # Asignación
            ':=', '+=', '-=', '*=', '/=',
            # Otros
            '!', '@', '::',
            # Comodines
            '_', '%'
        }
        
        # Delimitadores
        self.delimitadores = {'(', ')', '[', ']', '{', '}', ',', ';', '.'}
        
        # Tipos de datos específicos
        self.datatypes = {
            'VARCHAR2', 'NVARCHAR2', 'CLOB', 'NCLOB', 'BLOB', 'BFILE',
            'NUMBER', 'BINARY_FLOAT', 'BINARY_DOUBLE',
            'TIMESTAMP', 'INTERVAL', 'RAW', 'LONG', 'ROWID', 'UROWID',
            'MEDIUMINT', 'MEDIUMTEXT', 'LONGTEXT', 'TINYTEXT',
            'ENUM', 'SET', 'GEOMETRY', 'POINT', 'LINESTRING', 'POLYGON'
        }
        
        # Inicialización de atributos de la máquina
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
        Función de transición de la Máquina de Turing para SQL
        Retorna (nuevo_estado, acción)
        """
        
        # Verificar si el carácter es válido
        if not self.es_caracter_valido(caracter):
            return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        estado_actual = self.estado_actual
        
        # Estado INICIAL - Punto de partida
        if estado_actual == EstadoMaquina.INICIAL:
            if caracter.isalpha() or caracter == '_':
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            elif caracter.isdigit():
                return EstadoMaquina.NUMERO_INICIADO, "LEER"
            elif caracter in ['"', "'", '`']:  # Incluir backticks para identificadores
                return EstadoMaquina.STRING_INICIADO, "LEER"
            elif caracter == '-':
                return EstadoMaquina.COMENTARIO_LINEA_INICIADO, "LEER"
            elif caracter == '/':
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
            elif caracter == '@':  # Variables en SQL Server/MySQL
                return EstadoMaquina.VARIABLE_INICIADA, "LEER"
            elif caracter in '+-*/<>=!:|&%':
                return EstadoMaquina.OPERADOR_INICIADO, "LEER"
            elif caracter in self.delimitadores:
                return EstadoMaquina.DELIMITADOR_DETECTADO, "ACEPTAR"
            elif caracter in ' \t\n\r':
                return EstadoMaquina.ESPACIO_DETECTADO, "ACEPTAR"
            else:
                return EstadoMaquina.NO_ACEPTACION, "RECHAZAR"
        
        # Estado KEYWORD_CANDIDATO - Leyendo posible keyword/identificador
        elif estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            if caracter.isalnum() or caracter in '_':
                return EstadoMaquina.KEYWORD_CANDIDATO, "LEER"
            else:
                # Fin del token, verificar tipo
                token_upper = self.buffer_token.upper()
                if token_upper in self.keywords:
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
            elif caracter in ['"', "'", '`']:
                return EstadoMaquina.STRING_COMPLETO, "ACEPTAR"
            else:
                return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado STRING_ESCAPE - Carácter de escape en string
        elif estado_actual == EstadoMaquina.STRING_ESCAPE:
            return EstadoMaquina.STRING_INICIADO, "LEER"
        
        # Estado COMENTARIO_LINEA_INICIADO - Verificando comentario de línea
        elif estado_actual == EstadoMaquina.COMENTARIO_LINEA_INICIADO:
            if caracter == '-':  # Segundo guión confirma comentario
                return EstadoMaquina.COMENTARIO_LINEA_INICIADO, "LEER"
            elif caracter in '\n\r':
                return EstadoMaquina.COMENTARIO_COMPLETO, "ACEPTAR_RETROCEDER"
            else:
                return EstadoMaquina.COMENTARIO_LINEA_INICIADO, "LEER"
        
        # Estado COMENTARIO_BLOQUE_INICIADO - Verificando comentario de bloque
        elif estado_actual == EstadoMaquina.COMENTARIO_BLOQUE_INICIADO:
            if caracter == '*':  # /* inicia comentario de bloque
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
            elif caracter == '*':  # Buscando cierre */
                return EstadoMaquina.COMENTARIO_BLOQUE_ASTERISCO, "LEER"
            else:
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
        
        # Estado COMENTARIO_BLOQUE_ASTERISCO - Después de * en comentario de bloque
        elif estado_actual == EstadoMaquina.COMENTARIO_BLOQUE_ASTERISCO:
            if caracter == '/':  # */ cierra comentario
                return EstadoMaquina.COMENTARIO_COMPLETO, "ACEPTAR"
            elif caracter == '*':
                return EstadoMaquina.COMENTARIO_BLOQUE_ASTERISCO, "LEER"
            else:
                return EstadoMaquina.COMENTARIO_BLOQUE_INICIADO, "LEER"
        
        # Estado VARIABLE_INICIADA - Leyendo variable (@var)
        elif estado_actual == EstadoMaquina.VARIABLE_INICIADA:
            if caracter.isalnum() or caracter == '_':
                return EstadoMaquina.VARIABLE_INICIADA, "LEER"
            else:
                return EstadoMaquina.VARIABLE_COMPLETA, "ACEPTAR_RETROCEDER"
        
        # Estado OPERADOR_INICIADO - Leyendo operador
        elif estado_actual == EstadoMaquina.OPERADOR_INICIADO:
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
        """Procesa un token individual usando la máquina de Turing"""
        self.reiniciar_estado()
        self.buffer_token = ""
        
        # Verificaciones directas primero
        
        # 1. Strings (completos con comillas)
        if ((token_texto.startswith('"') and token_texto.endswith('"')) or 
            (token_texto.startswith("'") and token_texto.endswith("'")) or
            (token_texto.startswith('`') and token_texto.endswith('`'))):
            return Token(TipoToken.STRING, token_texto, posicion, True)
        
        # 2. Comentarios
        if token_texto.startswith('--') or (token_texto.startswith('/*') and token_texto.endswith('*/')):
            return Token(TipoToken.COMMENT, token_texto, posicion, True)
        
        # 3. Variables (@variable)
        if token_texto.startswith('@') and len(token_texto) > 1:
            return Token(TipoToken.VARIABLE, token_texto, posicion, True)
        
        # 4. Números
        if self._es_numero(token_texto):
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        
        # 5. Operadores
        if token_texto in self.operadores:
            return Token(TipoToken.OPERATOR, token_texto, posicion, True)
        
        # 6. Delimitadores
        if token_texto in self.delimitadores:
            return Token(TipoToken.DELIMITER, token_texto, posicion, True)
        
        # 7. Keywords (insensitive a mayúsculas)
        if token_texto.upper() in self.keywords:
            return Token(TipoToken.KEYWORD, token_texto, posicion, True)
        
        # 8. Funciones
        if token_texto.upper() in self.functions:
            return Token(TipoToken.FUNCTION, token_texto, posicion, True)
        
        # 9. Tipos de datos
        if token_texto.upper() in self.datatypes:
            return Token(TipoToken.DATATYPE, token_texto, posicion, True)
        
        # 10. Espacios en blanco
        if token_texto.isspace():
            return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
        
        # 11. Identificadores
        if self._es_identificador_valido(token_texto):
            return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        
        # 12. Usar la máquina de Turing como respaldo
        return self._procesar_con_maquina_turing(token_texto, posicion)
    
    def _es_numero(self, texto: str) -> bool:
        """Verifica si un texto es un número válido en SQL"""
        try:
            if '.' in texto:
                float(texto)
            else:
                int(texto)
            return True
        except ValueError:
            return False
    
    def _es_identificador_valido(self, texto: str) -> bool:
        """Verifica si un texto es un identificador válido en SQL"""
        if not texto:
            return False
        
        # Puede empezar con letra o guión bajo
        if not (texto[0].isalpha() or texto[0] == '_'):
            return False
        
        # El resto deben ser letras, números o guiones bajos
        return all(c.isalnum() or c == '_' for c in texto[1:])
    
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
                elif nuevo_estado == EstadoMaquina.VARIABLE_COMPLETA:
                    return Token(TipoToken.VARIABLE, token_texto, posicion, True)
                elif nuevo_estado == EstadoMaquina.ESPACIO_DETECTADO:
                    return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
                
                break
            
            elif accion == "LEER":
                self.estado_actual = nuevo_estado
                continue
        
        # Clasificar por estado final si no hay aceptación explícita
        if self.estado_actual == EstadoMaquina.KEYWORD_CANDIDATO:
            token_upper = token_texto.upper()
            if token_upper in self.keywords:
                return Token(TipoToken.KEYWORD, token_texto, posicion, True)
            elif token_upper in self.functions:
                return Token(TipoToken.FUNCTION, token_texto, posicion, True)
            elif token_upper in self.datatypes:
                return Token(TipoToken.DATATYPE, token_texto, posicion, True)
            else:
                return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        elif self.estado_actual in [EstadoMaquina.NUMERO_INICIADO, EstadoMaquina.NUMERO_DECIMAL]:
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        elif self.estado_actual == EstadoMaquina.VARIABLE_INICIADA:
            return Token(TipoToken.VARIABLE, token_texto, posicion, True)
        
        return Token(TipoToken.UNKNOWN, token_texto, posicion, False)
    
    def tokenizar_archivo(self, contenido_archivo: str) -> List[Token]:
        """
        Proceso completo de tokenización:
        1. Cargar archivo
        2. Separar por tokens
        3. Procesar cada token con la máquina de Turing
        """
        
        print(f"📁 Paso 1: Archivo SQL cargado ({len(contenido_archivo)} caracteres)")
        
        # Separación inteligente por tokens
        tokens_texto = self._separar_tokens_sql(contenido_archivo)
        print(f"🔍 Paso 2: Separados en {len(tokens_texto)} tokens SQL")
        
        # Procesar cada token con la máquina de Turing
        tokens_procesados = []
        tokens_rechazados = []
        
        print("⚙️  Paso 3: Procesando tokens SQL con Máquina de Turing...")
        
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
                print(f"❌ Token SQL rechazado: '{token.valor}' en posición {token.posicion}")
        
        print(f"✅ Procesamiento SQL completado:")
        print(f"   - Tokens válidos: {len(tokens_procesados) - len(tokens_rechazados)}")
        print(f"   - Tokens rechazados: {len(tokens_rechazados)}")
        
        return tokens_procesados
    
    def _separar_tokens_sql(self, texto: str) -> List[Tuple[str, int]]:
        """Separación inteligente de tokens SQL"""
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
            
            # Strings con comillas simples, dobles o backticks
            if texto[i] in '"\'`':
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
            
            # Comentarios de línea --
            if i < len(texto) - 1 and texto[i:i+2] == '--':
                inicio = i
                while i < len(texto) and texto[i] not in '\n\r':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Comentarios de bloque /* */
            if i < len(texto) - 1 and texto[i:i+2] == '/*':
                inicio = i
                i += 2
                while i < len(texto) - 1:
                    if texto[i:i+2] == '*/':
                        i += 2
                        break
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Variables @variable
            if texto[i] == '@' and i + 1 < len(texto) and (texto[i + 1].isalpha() or texto[i + 1] == '_'):
                inicio = i
                i += 1  # Saltar @
                while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Delimitadores
            if texto[i] in '()[]{},:;.':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Operadores - manejo específico para SQL
            if texto[i] in '+-*/<>=!:|&%':
                inicio = i
                # Verificar operadores compuestos
                if i < len(texto) - 1:
                    operador_doble = texto[i:i+2]
                    if operador_doble in ['!=', '<>', '<=', '>=', '||', '&&', ':=', '+=', '-=', '*=', '/=', '::']:
                        tokens.append((operador_doble, inicio))
                        i += 2
                        continue
                
                # Operador simple
                tokens.append((texto[i], inicio))
                i += 1
                continue
            
            # Números
            if texto[i].isdigit() or (texto[i] == '.' and i + 1 < len(texto) and texto[i + 1].isdigit()):
                inicio = i
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
            
            # Identificadores/Keywords
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

class SQLHTMLGenerator:
    """Generador de HTML para el resaltado de sintaxis SQL con colores específicos"""
    
    # Mapeo específico de operadores SQL a clases CSS únicas
    OPERATOR_CSS_MAP = {
        '+': 'sql-op-plus',
        '-': 'sql-op-minus', 
        '*': 'sql-op-multiply',
        '/': 'sql-op-divide',
        '%': 'sql-op-modulo',
        '=': 'sql-op-assign',
        '!=': 'sql-op-not-equal',
        '<>': 'sql-op-not-equal-alt',
        '<': 'sql-op-less',
        '>': 'sql-op-greater',
        '<=': 'sql-op-less-equal',
        '>=': 'sql-op-greater-equal',
        '||': 'sql-op-concat',
        '&&': 'sql-op-and',
        ':=': 'sql-op-assign-alt',
        '+=': 'sql-op-plus-assign',
        '-=': 'sql-op-minus-assign',
        '*=': 'sql-op-multiply-assign',
        '/=': 'sql-op-divide-assign',
        '::': 'sql-op-cast',
        '!': 'sql-op-not'
    }
    
    # Mapeo específico de delimitadores SQL
    DELIMITER_CSS_MAP = {
        '(': 'sql-del-paren-open',
        ')': 'sql-del-paren-close',
        '[': 'sql-del-bracket-open',
        ']': 'sql-del-bracket-close',
        '{': 'sql-del-brace-open',
        '}': 'sql-del-brace-close',
        ',': 'sql-del-comma',
        ';': 'sql-del-semicolon',
        '.': 'sql-del-dot'
    }
    
    # Keywords categorizados para diferentes colores
    DML_KEYWORDS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER'}
    DDL_KEYWORDS = {'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'TABLE', 'VIEW', 'INDEX', 'SCHEMA', 'DATABASE'}
    LOGICAL_KEYWORDS = {'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE', 'IS', 'NULL'}
    AGGREGATE_FUNCTIONS = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE'}
    
    def generar_css(self) -> str:
        """CSS para el resaltado de sintaxis SQL con colores únicos por categoría"""
        return """
        <style>
        .sql-code-container {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            overflow-x: auto;
            line-height: 1.6;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        /* Keywords DML - Azules brillantes */
        .sql-keyword-dml { color: #569cd6; font-weight: bold; text-transform: uppercase; }
        
        /* Keywords DDL - Verdes */
        .sql-keyword-ddl { color: #4ec9b0; font-weight: bold; text-transform: uppercase; }
        
        /* Keywords Lógicos - Magentas */
        .sql-keyword-logical { color: #c586c0; font-weight: bold; text-transform: uppercase; }
        
        /* Keywords Generales - Azul claro */
        .sql-keyword { color: #569cd6; font-weight: bold; text-transform: uppercase; }
        
        /* Funciones - Amarillo dorado */
        .sql-function { color: #dcdcaa; font-weight: bold; text-transform: uppercase; }
        
        /* Funciones de agregado - Naranja brillante */
        .sql-function-aggregate { color: #ff8c00; font-weight: bold; text-transform: uppercase; }
        
        /* Tipos de datos - Cyan */
        .sql-datatype { color: #4fc1ff; font-weight: bold; text-transform: uppercase; }
        
        /* Strings - Verde claro */
        .sql-string { color: #ce9178; background-color: rgba(206, 145, 120, 0.1); }
        
        /* Números - Verde menta */
        .sql-number { color: #b5cea8; font-weight: bold; }
        
        /* Comentarios - Grises */
        .sql-comment { color: #6a9955; font-style: italic; background-color: rgba(106, 153, 85, 0.1); }
        
        /* Variables - Rosa */
        .sql-variable { color: #ff69b4; font-weight: bold; }
        
        /* Identificadores - Blanco/Gris claro */
        .sql-identifier { color: #9cdcfe; }
        
        /* Operadores Aritméticos - Violetas */
        .sql-op-plus { color: #da70d6; font-weight: bold; font-size: 1.1em; }
        .sql-op-minus { color: #ba55d3; font-weight: bold; font-size: 1.1em; }
        .sql-op-multiply { color: #9370db; font-weight: bold; font-size: 1.1em; }
        .sql-op-divide { color: #8a2be2; font-weight: bold; font-size: 1.1em; }
        .sql-op-modulo { color: #9932cc; font-weight: bold; font-size: 1.1em; }
        
        /* Operadores de Comparación - Azules eléctricos */
        .sql-op-assign { color: #00bfff; font-weight: bold; font-size: 1.1em; }
        .sql-op-not-equal { color: #1e90ff; font-weight: bold; font-size: 1.1em; }
        .sql-op-not-equal-alt { color: #4169e1; font-weight: bold; font-size: 1.1em; }
        .sql-op-less { color: #0000ff; font-weight: bold; font-size: 1.1em; }
        .sql-op-greater { color: #6495ed; font-weight: bold; font-size: 1.1em; }
        .sql-op-less-equal { color: #4682b4; font-weight: bold; font-size: 1.1em; }
        .sql-op-greater-equal { color: #5f9ea0; font-weight: bold; font-size: 1.1em; }
        
        /* Operadores Especiales SQL - Rojos */
        .sql-op-concat { color: #ff6347; font-weight: bold; font-size: 1.1em; }
        .sql-op-and { color: #dc143c; font-weight: bold; font-size: 1.1em; }
        .sql-op-cast { color: #b22222; font-weight: bold; font-size: 1.1em; }
        .sql-op-assign-alt { color: #8b0000; font-weight: bold; font-size: 1.1em; }
        
        /* Operadores de Asignación - Naranjas */
        .sql-op-plus-assign { color: #ffa500; font-weight: bold; font-size: 1.1em; }
        .sql-op-minus-assign { color: #ff8c00; font-weight: bold; font-size: 1.1em; }
        .sql-op-multiply-assign { color: #ff7f50; font-weight: bold; font-size: 1.1em; }
        .sql-op-divide-assign { color: #ff6347; font-weight: bold; font-size: 1.1em; }
        
        /* Delimitadores - Diferentes tonos brillantes */
        .sql-del-paren-open { color: #ffff00; font-weight: bold; font-size: 1.2em; }
        .sql-del-paren-close { color: #ffff00; font-weight: bold; font-size: 1.2em; }
        .sql-del-bracket-open { color: #ffd700; font-weight: bold; font-size: 1.2em; }
        .sql-del-bracket-close { color: #ffd700; font-weight: bold; font-size: 1.2em; }
        .sql-del-brace-open { color: #f0e68c; font-weight: bold; font-size: 1.2em; }
        .sql-del-brace-close { color: #f0e68c; font-weight: bold; font-size: 1.2em; }
        .sql-del-comma { color: #32cd32; font-weight: bold; font-size: 1.1em; }
        .sql-del-semicolon { color: #00ff00; font-weight: bold; font-size: 1.2em; }
        .sql-del-dot { color: #adff2f; font-weight: bold; font-size: 1.1em; }
        
        /* Espacios en blanco */
        .sql-whitespace { background-color: transparent; }
        
        /* Tokens desconocidos */
        .sql-unknown { 
            color: #ff0000; 
            background-color: rgba(255, 0, 0, 0.2); 
            border: 2px solid #ff6347;
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        /* Valores especiales SQL */
        .sql-null { color: #c586c0; font-weight: bold; background-color: rgba(197, 134, 192, 0.1); text-transform: uppercase; }
        .sql-true { color: #4ec9b0; font-weight: bold; background-color: rgba(78, 201, 176, 0.1); text-transform: uppercase; }
        .sql-false { color: #f44747; font-weight: bold; background-color: rgba(244, 71, 71, 0.1); text-transform: uppercase; }
        
        .sql-stats {
            background-color: #2d2d30;
            border-left: 4px solid #569cd6;
            color: #d4d4d4;
            padding: 15px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            border-radius: 4px;
        }
        
        .sql-stats h3 {
            margin-top: 0;
            color: #569cd6;
        }
        
        /* Leyenda de colores para SQL */
        .sql-color-legend {
            background-color: #252526;
            border: 1px solid #464647;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #d4d4d4;
        }
        
        .sql-legend-category {
            margin-bottom: 15px;
        }
        
        .sql-legend-item {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }
        
        .sql-legend-category h4 {
            color: #569cd6;
            margin-bottom: 8px;
            font-size: 14px;
        }
        </style>
        """
    
    def tokens_a_html(self, tokens: List[Token]) -> str:
        """Convierte tokens SQL a HTML resaltado con colores específicos"""
        html_parts = []
        
        for token in tokens:
            valor_escapado = (token.valor.replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;')
                                        .replace('"', '&quot;'))
            
            # Determinar clase CSS específica basada en el tipo y valor del token
            css_class = self._determinar_clase_css_sql(token)
            
            if token.tipo == TipoToken.WHITESPACE:
                # Preservar espacios y tabs
                valor_escapado = valor_escapado.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                html_parts.append(valor_escapado)
            else:
                html_parts.append(f'<span class="{css_class}">{valor_escapado}</span>')
        
        return ''.join(html_parts)
    
    def _determinar_clase_css_sql(self, token: Token) -> str:
        """Determina la clase CSS específica para cada token SQL"""
        
        if token.tipo == TipoToken.KEYWORD:
            token_upper = token.valor.upper()
            # Categorizar keywords por tipo
            if token_upper in self.DML_KEYWORDS:
                return 'sql-keyword-dml'
            elif token_upper in self.DDL_KEYWORDS:
                return 'sql-keyword-ddl'
            elif token_upper in self.LOGICAL_KEYWORDS:
                return 'sql-keyword-logical'
            return 'sql-keyword'
        
        elif token.tipo == TipoToken.FUNCTION:
            token_upper = token.valor.upper()
            if token_upper in self.AGGREGATE_FUNCTIONS:
                return 'sql-function-aggregate'
            return 'sql-function'
        
        elif token.tipo == TipoToken.DATATYPE:
            return 'sql-datatype'
        
        elif token.tipo == TipoToken.STRING:
            return 'sql-string'
        
        elif token.tipo == TipoToken.NUMBER:
            return 'sql-number'
        
        elif token.tipo == TipoToken.COMMENT:
            return 'sql-comment'
        
        elif token.tipo == TipoToken.VARIABLE:
            return 'sql-variable'
        
        elif token.tipo == TipoToken.OPERATOR:
            return self.OPERATOR_CSS_MAP.get(token.valor, 'sql-operator')
        
        elif token.tipo == TipoToken.IDENTIFIER:
            # Verificar valores especiales
            token_upper = token.valor.upper()
            if token_upper == 'NULL':
                return 'sql-null'
            elif token_upper == 'TRUE':
                return 'sql-true'
            elif token_upper == 'FALSE':
                return 'sql-false'
            return 'sql-identifier'
        
        elif token.tipo == TipoToken.DELIMITER:
            return self.DELIMITER_CSS_MAP.get(token.valor, 'sql-delimiter')
        
        elif token.tipo == TipoToken.WHITESPACE:
            return 'sql-whitespace'
        
        else:
            return 'sql-unknown'

class SQLResaltadorSintaxis:
    """Clase principal del resaltador de sintaxis SQL basado en Máquina de Turing"""
    
    def __init__(self):
        self.maquina_turing = SQLTuringMachine()
        self.generador_html = SQLHTMLGenerator()
    
    def procesar_archivo(self, archivo_entrada: str, archivo_salida: str):
        """Procesa un archivo TXT con código SQL y genera HTML resaltado"""
        
        try:
            # Verificar que el archivo de entrada sea .txt
            if not archivo_entrada.lower().endswith('.txt'):
                print(f"❌ Error: Se esperaba un archivo .txt, recibido: {archivo_entrada}")
                return
            
            # Cargar archivo TXT
            print(f"🚀 Iniciando procesamiento de archivo SQL: {archivo_entrada}")
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            print(f"📄 Archivo SQL cargado exitosamente ({len(contenido)} caracteres)")
            print(f"🔍 Analizando código SQL contenido en el archivo...")
            
            # Procesar con la Máquina de Turing
            tokens = self.maquina_turing.tokenizar_archivo(contenido)
            
            # Generar estadísticas
            stats = self._generar_estadisticas_sql(tokens)
            
            # Generar HTML
            css = self.generador_html.generar_css()
            html_codigo = self.generador_html.tokens_a_html(tokens)
            
            # Documento HTML completo
            html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Léxico SQL - {archivo_entrada}</title>
    {css}
</head>
<body style="background-color: #1e1e1e; color: #d4d4d4; font-family: Arial, sans-serif; margin: 0; padding: 20px;">
    <h1 style="color: #569cd6;">🔍 Análisis Léxico SQL con Máquina de Turing</h1>
    <h2 style="color: #4ec9b0;">Archivo procesado: {archivo_entrada}</h2>
    <p><em style="color: #6a9955;">Código SQL analizado desde archivo de texto usando principios de Máquina de Turing</em></p>
    
    <div class="sql-color-legend">
        <h3 style="color: #569cd6; margin-top: 0;">🎨 Leyenda de Colores SQL</h3>
        
        <div class="sql-legend-category">
            <h4>Keywords por Categoría:</h4>
            <span class="sql-legend-item"><span class="sql-keyword-dml">SELECT INSERT UPDATE DELETE</span> (DML - Azul)</span>
            <span class="sql-legend-item"><span class="sql-keyword-ddl">CREATE ALTER DROP TABLE</span> (DDL - Verde)</span>
            <span class="sql-legend-item"><span class="sql-keyword-logical">AND OR NOT IN EXISTS</span> (Lógicos - Magenta)</span>
        </div>
        
        <div class="sql-legend-category">
            <h4>Funciones:</h4>
            <span class="sql-legend-item"><span class="sql-function">CONCAT LENGTH UPPER LOWER</span> (Funciones generales)</span>
            <span class="sql-legend-item"><span class="sql-function-aggregate">COUNT SUM AVG MIN MAX</span> (Agregadas - Naranja)</span>
        </div>
        
        <div class="sql-legend-category">
            <h4>Tipos de Datos:</h4>
            <span class="sql-legend-item"><span class="sql-datatype">VARCHAR INT DECIMAL DATE BOOLEAN</span> (Cyan)</span>
        </div>
        
        <div class="sql-legend-category">
            <h4>Operadores:</h4>
            <span class="sql-legend-item"><span class="sql-op-plus">+</span> <span class="sql-op-minus">-</span> <span class="sql-op-multiply">*</span> <span class="sql-op-divide">/</span> (Aritméticos)</span>
            <span class="sql-legend-item"><span class="sql-op-assign">=</span> <span class="sql-op-not-equal">!=</span> <span class="sql-op-less">&lt;</span> <span class="sql-op-greater">&gt;</span> (Comparación)</span>
            <span class="sql-legend-item"><span class="sql-op-concat">||</span> <span class="sql-op-cast">::</span> (SQL Específicos)</span>
        </div>
        
        <div class="sql-legend-category">
            <h4>Delimitadores:</h4>
            <span class="sql-legend-item"><span class="sql-del-paren-open">(</span><span class="sql-del-paren-close">)</span> Paréntesis</span>
            <span class="sql-legend-item"><span class="sql-del-bracket-open">[</span><span class="sql-del-bracket-close">]</span> Corchetes</span>
            <span class="sql-legend-item"><span class="sql-del-comma">,</span> <span class="sql-del-semicolon">;</span> <span class="sql-del-dot">.</span></span>
        </div>
        
        <div class="sql-legend-category">
            <h4>Elementos Especiales:</h4>
            <span class="sql-legend-item"><span class="sql-string">'strings'</span> <span class="sql-string">"strings"</span></span>
            <span class="sql-legend-item"><span class="sql-number">123</span> <span class="sql-number">45.67</span></span>
            <span class="sql-legend-item"><span class="sql-variable">@variable</span></span>
            <span class="sql-legend-item"><span class="sql-null">NULL</span> <span class="sql-true">TRUE</span> <span class="sql-false">FALSE</span></span>
            <span class="sql-legend-item"><span class="sql-comment">-- comentarios</span></span>
        </div>
    </div>
    
    <div class="sql-stats">
        <h3>📊 Estadísticas del Análisis SQL</h3>
        {stats}
    </div>
    
    <div class="sql-code-container">
        {html_codigo}
    </div>
    
    <div style="margin-top: 20px; color: #6a9955; font-size: 12px; text-align: center;">
        <p>Generado por Resaltador de Sintaxis SQL - Máquina de Turing</p>
        <p>Implementación basada en Estados y Transiciones Deterministas para SQL</p>
        <p>Entrada: Archivo TXT con SQL → Salida: HTML con sintaxis resaltada</p>
        <p><strong>🎨 Cada elemento SQL tiene colores específicos para máxima claridad</strong></p>
        <p>Compatible con: SQL Standard, MySQL, PostgreSQL, SQL Server, Oracle</p>
    </div>
</body>
</html>"""
            
            # Guardar archivo HTML
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write(html_completo)
            
            print(f"✅ Procesamiento SQL completado exitosamente!")
            print(f"📄 Archivo SQL procesado: {archivo_entrada}")
            print(f"🌐 Archivo HTML generado: {archivo_salida}")
            print(f"🎯 Tokens SQL identificados: {len(tokens)}")
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo SQL: {archivo_entrada}")
        except Exception as e:
            print(f"❌ Error durante el procesamiento del archivo SQL: {e}")
    
    def _generar_estadisticas_sql(self, tokens: List[Token]) -> str:
        """Genera estadísticas específicas del análisis de tokens SQL"""
        conteo_tipos = {}
        keywords_encontrados = set()
        funciones_encontradas = set()
        tokens_invalidos = []
        
        for token in tokens:
            if token.tipo not in conteo_tipos:
                conteo_tipos[token.tipo] = 0
            conteo_tipos[token.tipo] += 1
            
            if token.tipo == TipoToken.KEYWORD:
                keywords_encontrados.add(token.valor.upper())
            elif token.tipo == TipoToken.FUNCTION:
                funciones_encontradas.add(token.valor.upper())
            
            if not token.valido:
                tokens_invalidos.append(token)
        
        stats_html = f"<p><strong>Total de tokens SQL procesados:</strong> {len(tokens)}</p>"
        stats_html += f"<p><strong>Keywords SQL únicos encontrados:</strong> {len(keywords_encontrados)}</p>"
        stats_html += f"<p><strong>Funciones SQL únicas encontradas:</strong> {len(funciones_encontradas)}</p>"
        
        stats_html += "<p><strong>Distribución por tipo de token:</strong></p><ul>"
        
        for tipo, cantidad in sorted(conteo_tipos.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / len(tokens)) * 100
            stats_html += f"<li>{tipo.value}: {cantidad} ({porcentaje:.1f}%)</li>"
        
        stats_html += "</ul>"
        
        # Mostrar algunos keywords encontrados
        if keywords_encontrados:
            keywords_list = sorted(list(keywords_encontrados))[:10]
            stats_html += f"<p><strong>Keywords SQL detectados (muestra):</strong> {', '.join(keywords_list)}"
            if len(keywords_encontrados) > 10:
                stats_html += f" y {len(keywords_encontrados) - 10} más..."
            stats_html += "</p>"
        
        # Mostrar funciones encontradas
        if funciones_encontradas:
            funciones_list = sorted(list(funciones_encontradas))[:8]
            stats_html += f"<p><strong>Funciones SQL detectadas:</strong> {', '.join(funciones_list)}"
            if len(funciones_encontradas) > 8:
                stats_html += f" y {len(funciones_encontradas) - 8} más..."
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
    """Función principal del resaltador SQL"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Uso: python sql_turing_highlighter.py <archivo.txt> [salida.html]")
        print("📝 Ejemplo: python sql_turing_highlighter.py consulta.txt resultado_sql.html")
        print("📄 El archivo de entrada debe ser un .txt que contenga código SQL")
        print("🎯 Soporta: SQL Standard, MySQL, PostgreSQL, SQL Server, Oracle")
        return
    
    archivo_entrada = sys.argv[1]
    
    # Verificar que la entrada sea un archivo .txt
    if not archivo_entrada.lower().endswith('.txt'):
        print("❌ Error: El archivo de entrada debe ser un archivo .txt")
        print("📝 Ejemplo: python sql_turing_highlighter.py mi_consulta.txt")
        return
    
    # Generar nombre de salida basado en el archivo .txt
    if len(sys.argv) > 2:
        archivo_salida = sys.argv[2]
    else:
        # Cambiar .txt por _sql_highlighted.html
        archivo_salida = archivo_entrada.replace('.txt', '_sql_highlighted.html')
    
    resaltador = SQLResaltadorSintaxis()
    resaltador.procesar_archivo(archivo_entrada, archivo_salida)

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print(f"--- Procesamiento completado en {time.time() - start_time:.4f} segundos ---")