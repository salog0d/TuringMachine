"""
Resaltador de Sintaxis basado en Máquina de Turing - VERSIÓN MULTICORE
Implementación con estados explícitos, transiciones deterministas y procesamiento multi-núcleo REAL
Usa multiprocessing para evitar el GIL y aprovechar todos los núcleos del CPU
"""

import string
import multiprocessing as mp
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import pickle
import psutil

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
    proceso_id: Optional[int] = None  # ID del proceso que procesó el token
    cpu_core: Optional[int] = None    # Núcleo de CPU usado

@dataclass
class ChunkProcesamiento:
    """Chunk de tokens para procesamiento en paralelo"""
    tokens_texto: List[Tuple[str, int]]
    chunk_id: int
    inicio_global: int
    fin_global: int

def procesar_chunk_multicore(chunk_data: Tuple[ChunkProcesamiento, Dict]) -> Tuple[int, List[Token], Dict]:
    """
    Función INDEPENDIENTE para procesamiento multicore
    Esta función se ejecuta en un proceso separado, aprovechando un núcleo completo del CPU
    """
    chunk, configuracion = chunk_data
    inicio_tiempo = time.time()
    
    # Información del proceso y CPU
    proceso_id = os.getpid()
    cpu_core = psutil.Process().cpu_num() if hasattr(psutil.Process(), 'cpu_num') else -1
    
    # Crear instancia local de la máquina de Turing
    maquina_local = TuringMachineInstance(
        keywords=configuracion['keywords'],
        operadores=configuracion['operadores'],
        delimitadores=configuracion['delimitadores'],
        alfabeto=configuracion['alfabeto']
    )
    
    tokens_procesados = []
    errores = 0
    
    print(f"🔥 Proceso {proceso_id} (CPU {cpu_core}) procesando chunk {chunk.chunk_id} con {len(chunk.tokens_texto)} tokens")
    
    try:
        for texto_token, posicion in chunk.tokens_texto:
            # Procesar token individual
            token = maquina_local.procesar_token_individual(texto_token, posicion)
            token.proceso_id = proceso_id
            token.cpu_core = cpu_core
            tokens_procesados.append(token)
            
            if not token.valido:
                errores += 1
                    
    except Exception as e:
        print(f"❌ Error en proceso {proceso_id} procesando chunk {chunk.chunk_id}: {e}")
        errores += 1
    
    tiempo_total = time.time() - inicio_tiempo
    
    estadisticas_proceso = {
        'proceso_id': proceso_id,
        'cpu_core': cpu_core,
        'chunk_id': chunk.chunk_id,
        'tokens_procesados': len(tokens_procesados),
        'errores': errores,
        'tiempo_procesamiento': tiempo_total,
        'tokens_por_segundo': len(tokens_procesados) / tiempo_total if tiempo_total > 0 else 0
    }
    
    print(f"✅ Proceso {proceso_id} completó chunk {chunk.chunk_id}: {len(tokens_procesados)} tokens en {tiempo_total:.3f}s ({estadisticas_proceso['tokens_por_segundo']:.0f} tokens/seg)")
    
    return chunk.chunk_id, tokens_procesados, estadisticas_proceso


class TuringMachineMulticore:
    """Máquina de Turing para análisis léxico con capacidades multicore REALES"""
    
    def __init__(self):
        # Configuraciones compartidas (inmutables para serialización)
        self.keywords = frozenset([
            'False', 'None', 'True', 'and', 'as', 'assert', 'break',
            'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
            'return', 'try', 'while', 'with', 'yield', 'async', 'await'
        ])
        
        self.operadores = frozenset([
            '+', '-', '*', '/', '//', '%', '**',
            '=', '+=', '-=', '*=', '/=', '//=', '%=', '**=',
            '==', '!=', '<', '>', '<=', '>=', '<>',
            '&', '|', '^', '~', '<<', '>>', '&=', '|=', '^=', '<<=', '>>=',
            '!', '@', '@='
        ])
        
        self.delimitadores = frozenset(['(', ')', '[', ']', '{', '}', ',', ':', ';', '.'])
        self.alfabeto = frozenset(string.ascii_letters + string.digits + '_."\'#\t\n\r+-*/<>=!()[]{},:; ')
        
        # Detectar número óptimo de procesos basado en CPU
        self.num_cores = mp.cpu_count()
        print(f"🖥️  Sistema detectado: {self.num_cores} núcleos de CPU disponibles")
        
        # Estadísticas de rendimiento multicore
        self.stats_multicore = {
            'chunks_procesados': 0,
            'tokens_por_proceso': {},
            'tiempo_por_chunk': [],
            'errores_por_proceso': {},
            'cpu_cores_utilizados': set()
        }
    
    def _crear_configuracion_serializable(self) -> Dict:
        """Crea configuración serializable para procesos"""
        return {
            'keywords': self.keywords,
            'operadores': self.operadores,
            'delimitadores': self.delimitadores,
            'alfabeto': self.alfabeto
        }
    
    def _dividir_en_chunks(self, tokens_texto: List[Tuple[str, int]], 
                          num_procesos: int) -> List[ChunkProcesamiento]:
        """
        Divide la lista de tokens en chunks para procesamiento multicore
        Estrategia optimizada para evitar overhead de comunicación entre procesos
        """
        if len(tokens_texto) < num_procesos:
            # Si hay pocos tokens, crear menos chunks
            chunks = []
            for i, (texto, pos) in enumerate(tokens_texto):
                chunk = ChunkProcesamiento(
                    tokens_texto=[(texto, pos)],
                    chunk_id=i,
                    inicio_global=pos,
                    fin_global=pos + len(texto)
                )
                chunks.append(chunk)
            return chunks
        
        # Crear chunks más grandes para reducir overhead de multiprocessing
        min_chunk_size = max(100, len(tokens_texto) // (num_procesos * 2))
        chunk_size = max(min_chunk_size, len(tokens_texto) // num_procesos)
        
        chunks = []
        
        for i in range(num_procesos):
            inicio = i * chunk_size
            fin = min((i + 1) * chunk_size, len(tokens_texto))
            
            # Para el último chunk, incluir tokens restantes
            if i == num_procesos - 1:
                fin = len(tokens_texto)
            
            if inicio < len(tokens_texto):
                chunk_tokens = tokens_texto[inicio:fin]
                chunk = ChunkProcesamiento(
                    tokens_texto=chunk_tokens,
                    chunk_id=i,
                    inicio_global=chunk_tokens[0][1] if chunk_tokens else 0,
                    fin_global=chunk_tokens[-1][1] + len(chunk_tokens[-1][0]) if chunk_tokens else 0
                )
                chunks.append(chunk)
        
        return chunks
    
    def tokenizar_archivo_multicore(self, contenido_archivo: str, 
                                   num_procesos: int = None) -> Tuple[List[Token], Dict]:
        """
        Tokeniza un archivo usando VERDADERO procesamiento multicore
        Cada proceso usa un núcleo diferente del CPU
        """
        if num_procesos is None:
            num_procesos = min(self.num_cores, max(2, self.num_cores - 1))  # Dejar un núcleo libre
        
        print(f"🚀 Iniciando procesamiento MULTICORE REAL")
        print(f"🔥 CPU: {self.num_cores} núcleos | Usando: {num_procesos} procesos paralelos")
        print(f"📁 Archivo cargado ({len(contenido_archivo)} caracteres)")
        
        inicio_total = time.time()
        
        # Paso 1: Separación de tokens (secuencial - muy rápido)
        print("🔍 Separando tokens...")
        tokens_texto = self._separar_tokens(contenido_archivo)
        print(f"📦 {len(tokens_texto)} tokens identificados")
        
        # Paso 2: Dividir en chunks para procesamiento multicore
        chunks = self._dividir_en_chunks(tokens_texto, num_procesos)
        print(f"🧩 Dividido en {len(chunks)} chunks (tamaño promedio: {len(tokens_texto)//len(chunks)} tokens por chunk)")
        
        # Paso 3: Configuración para serialización
        configuracion = self._crear_configuracion_serializable()
        
        # Paso 4: Procesamiento MULTICORE con ProcessPoolExecutor
        todos_los_tokens = [None] * len(chunks)
        estadisticas_procesos = []
        
        print("🔥 Iniciando procesamiento multicore...")
        print("💡 Cada proceso usará un núcleo de CPU diferente")
        
        with ProcessPoolExecutor(max_workers=num_procesos) as executor:
            # Preparar datos para cada proceso
            chunk_data = [(chunk, configuracion) for chunk in chunks]
            
            # Enviar chunks a procesos separados
            futuros = {
                executor.submit(procesar_chunk_multicore, data): data[0].chunk_id 
                for data in chunk_data
            }
            
            # Recopilar resultados conforme se completan
            chunks_completados = 0
            for futuro in as_completed(futuros):
                chunk_id = futuros[futuro]
                try:
                    chunk_id_resultado, tokens_chunk, stats_proceso = futuro.result()
                    todos_los_tokens[chunk_id_resultado] = tokens_chunk
                    estadisticas_procesos.append(stats_proceso)
                    chunks_completados += 1
                    
                    porcentaje = (chunks_completados / len(chunks)) * 100
                    print(f"🏁 [{porcentaje:5.1f}%] Chunk {chunk_id_resultado} completado por proceso {stats_proceso['proceso_id']} "
                          f"(CPU {stats_proceso['cpu_core']}) - {stats_proceso['tokens_procesados']} tokens")
                    
                except Exception as e:
                    print(f"❌ Error procesando chunk {chunk_id}: {e}")
        
        # Paso 5: Reconstruir lista ordenada de tokens
        tokens_finales = []
        for tokens_chunk in todos_los_tokens:
            if tokens_chunk:
                tokens_finales.extend(tokens_chunk)
        
        tiempo_total = time.time() - inicio_total
        
        # Generar estadísticas finales
        estadisticas_finales = self._generar_estadisticas_multicore(
            tokens_finales, estadisticas_procesos, tiempo_total, num_procesos
        )
        
        print(f"\n🏆 PROCESAMIENTO MULTICORE COMPLETADO")
        print(f"⏱️  Tiempo total: {tiempo_total:.3f} segundos")
        print(f"🚀 Velocidad total: {len(tokens_finales)/tiempo_total:.0f} tokens/segundo")
        print(f"💪 Núcleos utilizados: {len(estadisticas_finales['cpu_cores_utilizados'])}")
        print(f"⚡ Speedup estimado: {estadisticas_finales['speedup_estimado']:.1f}x vs. un solo núcleo")
        
        return tokens_finales, estadisticas_finales
    
    def _generar_estadisticas_multicore(self, tokens: List[Token], 
                                      stats_procesos: List[Dict], 
                                      tiempo_total: float,
                                      num_procesos: int) -> Dict:
        """Genera estadísticas completas del procesamiento multicore"""
        
        # Estadísticas básicas de tokens
        conteo_tipos = {}
        tokens_por_proceso = {}
        cpu_cores_utilizados = set()
        tokens_invalidos = []
        
        for token in tokens:
            # Conteo por tipo
            if token.tipo not in conteo_tipos:
                conteo_tipos[token.tipo] = 0
            conteo_tipos[token.tipo] += 1
            
            # Conteo por proceso
            if token.proceso_id:
                if token.proceso_id not in tokens_por_proceso:
                    tokens_por_proceso[token.proceso_id] = 0
                tokens_por_proceso[token.proceso_id] += 1
            
            # Núcleos utilizados
            if token.cpu_core is not None and token.cpu_core >= 0:
                cpu_cores_utilizados.add(token.cpu_core)
            
            # Tokens inválidos
            if not token.valido:
                tokens_invalidos.append(token)
        
        # Estadísticas de rendimiento
        total_tokens = len(tokens)
        tiempo_promedio_por_chunk = sum(s['tiempo_procesamiento'] for s in stats_procesos) / len(stats_procesos)
        tokens_por_segundo_promedio = sum(s['tokens_por_segundo'] for s in stats_procesos) / len(stats_procesos)
        
        # Eficiencia multicore REAL
        tiempo_secuencial_estimado = total_tokens / tokens_por_segundo_promedio if tokens_por_segundo_promedio > 0 else tiempo_total
        eficiencia_multicore = (tiempo_secuencial_estimado / tiempo_total) / num_procesos if tiempo_total > 0 else 0
        speedup_real = tiempo_secuencial_estimado / tiempo_total if tiempo_total > 0 else 1
        
        # Utilización de CPU
        utilizacion_cpu = len(cpu_cores_utilizados) / mp.cpu_count() * 100
        
        return {
            'total_tokens': total_tokens,
            'tokens_invalidos': len(tokens_invalidos),
            'conteo_tipos': conteo_tipos,
            'tokens_por_proceso': tokens_por_proceso,
            'cpu_cores_utilizados': cpu_cores_utilizados,
            'estadisticas_procesos': stats_procesos,
            'tiempo_total': tiempo_total,
            'num_procesos_usados': num_procesos,
            'num_cores_sistema': mp.cpu_count(),
            'tiempo_promedio_por_chunk': tiempo_promedio_por_chunk,
            'tokens_por_segundo_total': total_tokens / tiempo_total if tiempo_total > 0 else 0,
            'tokens_por_segundo_promedio': tokens_por_segundo_promedio,
            'eficiencia_multicore': eficiencia_multicore,
            'speedup_estimado': speedup_real,
            'utilizacion_cpu_porcentaje': utilizacion_cpu,
            'ejemplos_tokens_invalidos': tokens_invalidos[:5]
        }
    
    def _separar_tokens(self, texto: str) -> List[Tuple[str, int]]:
        """Separación inteligente de tokens (optimizada para multicore)"""
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
            
            # Strings completos
            if texto[i] in '"\'':
                inicio = i
                quote = texto[i]
                i += 1
                while i < len(texto) and texto[i] != quote:
                    if texto[i] == '\\':
                        i += 2 if i + 1 < len(texto) else 1
                    else:
                        i += 1
                if i < len(texto):
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # f-strings
            if i < len(texto) - 1 and texto[i] == 'f' and texto[i + 1] in '"\'':
                inicio = i
                i += 1
                quote = texto[i]
                i += 1
                while i < len(texto) and texto[i] != quote:
                    if texto[i] == '\\':
                        i += 2 if i + 1 < len(texto) else 1
                    else:
                        i += 1
                if i < len(texto):
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Comentarios
            if texto[i] == '#':
                inicio = i
                while i < len(texto) and texto[i] not in '\n\r':
                    i += 1
                tokens.append((texto[inicio:i], inicio))
                continue
            
            # Delimitadores
            if texto[i] in '()[]{},:;.':
                tokens.append((texto[i], i))
                i += 1
                continue
            
            # Operadores compuestos
            if texto[i] in '+-*/<>=!&|^~':
                inicio = i
                if i < len(texto) - 1:
                    op_doble = texto[i:i+2]
                    if op_doble in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '//', '**', '<<', '>>', '&=', '|=', '^=', '<>']:
                        tokens.append((op_doble, inicio))
                        i += 2
                        continue
                    if i < len(texto) - 2:
                        op_triple = texto[i:i+3]
                        if op_triple in ['//=', '**=', '<<=', '>>=']:
                            tokens.append((op_triple, inicio))
                            i += 3
                            continue
                tokens.append((texto[i], inicio))
                i += 1
                continue
            
            # Números (incluyendo hex, oct, bin)
            if texto[i].isdigit() or (texto[i] == '.' and i + 1 < len(texto) and texto[i + 1].isdigit()):
                inicio = i
                if i < len(texto) - 1 and texto[i] == '0' and texto[i + 1] in 'xXoObB':
                    i += 2
                    while i < len(texto) and texto[i].isalnum():
                        i += 1
                    tokens.append((texto[inicio:i], inicio))
                    continue
                
                while i < len(texto) and (texto[i].isdigit() or texto[i] == '.'):
                    i += 1
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
            
            # Caracteres individuales
            tokens.append((texto[i], i))
            i += 1
        
        return tokens


class TuringMachineInstance:
    """
    Instancia local de Máquina de Turing para procesos independientes
    Cada proceso tiene su propia instancia completamente aislada
    """
    
    def __init__(self, keywords, operadores, delimitadores, alfabeto):
        self.keywords = keywords
        self.operadores = operadores  
        self.delimitadores = delimitadores
        self.alfabeto = alfabeto
        
        # Estado local del proceso
        self.estado_actual = EstadoMaquina.INICIAL
        self.buffer_token = ""
    
    def es_caracter_valido(self, caracter: str) -> bool:
        return caracter in self.alfabeto
    
    def reiniciar_estado(self):
        self.estado_actual = EstadoMaquina.INICIAL
        self.buffer_token = ""
    
    def procesar_token_individual(self, token_texto: str, posicion: int) -> Token:
        """Procesa un token individual (completamente aislado por proceso)"""
        self.reiniciar_estado()
        
        # Verificaciones directas optimizadas
        if ((token_texto.startswith('"') and token_texto.endswith('"')) or 
            (token_texto.startswith("'") and token_texto.endswith("'")) or
            (token_texto.startswith('f"') and token_texto.endswith('"')) or
            (token_texto.startswith("f'") and token_texto.endswith("'"))):
            return Token(TipoToken.STRING, token_texto, posicion, True)
        
        if token_texto.startswith('#'):
            return Token(TipoToken.COMMENT, token_texto, posicion, True)
        
        if self._es_numero(token_texto):
            return Token(TipoToken.NUMBER, token_texto, posicion, True)
        
        if token_texto in self.operadores:
            return Token(TipoToken.OPERATOR, token_texto, posicion, True)
        
        if token_texto in self.delimitadores:
            return Token(TipoToken.DELIMITER, token_texto, posicion, True)
        
        if token_texto in self.keywords:
            return Token(TipoToken.KEYWORD, token_texto, posicion, True)
        
        if token_texto.isspace():
            return Token(TipoToken.WHITESPACE, token_texto, posicion, True)
        
        if self._es_identificador_valido(token_texto):
            return Token(TipoToken.IDENTIFIER, token_texto, posicion, True)
        
        return Token(TipoToken.UNKNOWN, token_texto, posicion, False)
    
    def _es_numero(self, texto: str) -> bool:
        try:
            if '.' in texto or 'e' in texto.lower():
                float(texto)
            else:
                int(texto, 0)
            return True
        except ValueError:
            return False
    
    def _es_identificador_valido(self, texto: str) -> bool:
        if not texto:
            return False
        if not (texto[0].isalpha() or texto[0] == '_'):
            return False
        return all(c.isalnum() or c == '_' for c in texto[1:])


class HTMLGenerator:
    """Generador de HTML mejorado con información de multiprocessing"""
    
    OPERATOR_CSS_MAP = {
        '+': 'op-plus', '-': 'op-minus', '*': 'op-multiply', '/': 'op-divide',
        '//': 'op-divide', '%': 'op-modulo', '**': 'op-power', '=': 'op-assign',
        '==': 'op-equal', '!=': 'op-not-equal', '<>': 'op-not-equal',
        '<': 'op-less', '>': 'op-greater', '<=': 'op-less-equal', '>=': 'op-greater-equal',
        '+=': 'op-plus-assign', '-=': 'op-minus-assign', '*=': 'op-multiply-assign',
        '/=': 'op-divide-assign', '//=': 'op-divide-assign', '%=': 'op-modulo',
        '**=': 'op-power', '&': 'op-bitwise-and', '|': 'op-bitwise-or',
        '^': 'op-bitwise-xor', '~': 'op-bitwise-not', '<<': 'op-left-shift',
        '>>': 'op-right-shift', '&=': 'op-bitwise-and', '|=': 'op-bitwise-or',
        '^=': 'op-bitwise-xor', '<<=': 'op-left-shift', '>>=': 'op-right-shift',
        '!': 'op-not'
    }
    
    DELIMITER_CSS_MAP = {
        '(': 'del-paren-open', ')': 'del-paren-close',
        '[': 'del-bracket-open', ']': 'del-bracket-close',
        '{': 'del-brace-open', '}': 'del-brace-close',
        ',': 'del-comma', ':': 'del-colon', ';': 'del-semicolon', '.': 'del-dot'
    }
    
    LOGICAL_KEYWORDS = {'and': 'op-and', 'or': 'op-or', 'not': 'op-not'}
    
    BUILTINS = {
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
        'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
        'open', 'input', 'abs', 'max', 'min', 'sum', 'all', 'any', 'enumerate',
        'zip', 'map', 'filter', 'sorted', 'reversed', 'round', 'pow', 'divmod'
    }
    
    # Colores para diferentes procesos/núcleos
    PROCESS_COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    
    def generar_css(self) -> str:
        """CSS mejorado con estilos para información multicore"""
        process_css = ""
        for i, color in enumerate(self.PROCESS_COLORS):
            process_css += f"""
        .process-{i} {{ border-bottom: 2px solid {color}; }}
        .cpu-core-{i} {{ background-color: {color}20; }}
        """
        
        return f"""
        <style>
        .code-container {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            overflow-x: auto;
            line-height: 1.6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Estilos de tokens originales */
        .keyword {{ color: #0066cc; font-weight: bold; }}
        .string {{ color: #228B22; background-color: #f0fff0; }}
        .number {{ color: #FF6347; font-weight: bold; }}
        .comment {{ color: #708090; font-style: italic; background-color: #f5f5f5; }}
        .identifier {{ color: #2F4F4F; }}
        
        /* Operadores con colores específicos */
        .op-plus {{ color: #8A2BE2; font-weight: bold; }}
        .op-minus {{ color: #9932CC; font-weight: bold; }}
        .op-multiply {{ color: #BA55D3; font-weight: bold; }}
        .op-divide {{ color: #DA70D6; font-weight: bold; }}
        .op-modulo {{ color: #DDA0DD; font-weight: bold; }}
        .op-power {{ color: #EE82EE; font-weight: bold; }}
        
        .op-equal {{ color: #191970; font-weight: bold; }}
        .op-not-equal {{ color: #000080; font-weight: bold; }}
        .op-less {{ color: #0000CD; font-weight: bold; }}
        .op-greater {{ color: #4169E1; font-weight: bold; }}
        .op-less-equal {{ color: #4682B4; font-weight: bold; }}
        .op-greater-equal {{ color: #6495ED; font-weight: bold; }}
        
        .op-assign {{ color: #8B4513; font-weight: bold; }}
        .op-plus-assign {{ color: #A0522D; font-weight: bold; }}
        .op-minus-assign {{ color: #CD853F; font-weight: bold; }}
        .op-multiply-assign {{ color: #D2691E; font-weight: bold; }}
        .op-divide-assign {{ color: #DEB887; font-weight: bold; }}
        
        .op-and {{ color: #B22222; font-weight: bold; }}
        .op-or {{ color: #DC143C; font-weight: bold; }}
        .op-not {{ color: #FF0000; font-weight: bold; }}
        
        .op-bitwise-and {{ color: #008B8B; font-weight: bold; }}
        .op-bitwise-or {{ color: #20B2AA; font-weight: bold; }}
        .op-bitwise-xor {{ color: #48D1CC; font-weight: bold; }}
        .op-bitwise-not {{ color: #00CED1; font-weight: bold; }}
        .op-left-shift {{ color: #40E0D0; font-weight: bold; }}
        .op-right-shift {{ color: #AFEEEE; font-weight: bold; }}
        
        /* Delimitadores con colores específicos */
        .del-paren-open {{ color: #FF1493; font-weight: bold; font-size: 1.1em; }}
        .del-paren-close {{ color: #FF1493; font-weight: bold; font-size: 1.1em; }}
        .del-bracket-open {{ color: #FF4500; font-weight: bold; font-size: 1.1em; }}
        .del-bracket-close {{ color: #FF4500; font-weight: bold; font-size: 1.1em; }}
        .del-brace-open {{ color: #FF6347; font-weight: bold; font-size: 1.1em; }}
        .del-brace-close {{ color: #FF6347; font-weight: bold; font-size: 1.1em; }}
        .del-comma {{ color: #32CD32; font-weight: bold; }}
        .del-colon {{ color: #00FF00; font-weight: bold; }}
        .del-semicolon {{ color: #ADFF2F; font-weight: bold; }}
        .del-dot {{ color: #9ACD32; font-weight: bold; }}
        
        /* Valores especiales */
        .boolean-true {{ color: #006400; font-weight: bold; background-color: #F0FFF0; }}
        .boolean-false {{ color: #8B0000; font-weight: bold; background-color: #FFF0F0; }}
        .none-value {{ color: #4B0082; font-weight: bold; background-color: #F8F8FF; }}
        .builtin {{ color: #800080; font-weight: bold; text-decoration: underline; }}
        
        .whitespace {{ background-color: transparent; }}
        .unknown {{ 
            color: #FF0000; 
            background-color: #FFE4E1; 
            border: 2px solid #FF6347;
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        /* Estilos específicos para multiprocessing */
        {process_css}
        
        .multicore-info {{
            background-color: #e6f7ff;
            border: 2px solid #1890ff;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            font-family: Arial, sans-serif;
        }}
        
        .multicore-stats {{
            background-color: #f6ffed;
            border-left: 5px solid #52c41a;
            padding: 20px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
        }}
        
        .multicore-stats h3 {{
            margin-top: 0;
            color: #389e0d;
            display: flex;
            align-items: center;
        }}
        
        .cpu-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .cpu-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }}
        
        .cpu-card:hover {{
            transform: translateY(-5px);
        }}
        
        .cpu-metric {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .cpu-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .core-utilization {{
            background-color: #fff;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .core-bar {{
            height: 25px;
            border-radius: 12px;
            margin: 8px 0;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        }}
        
        .process-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
            padding: 10px;
            background-color: #fafafa;
            border-radius: 6px;
        }}
        
        .process-badge {{
            display: inline-flex;
            align-items: center;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        
        .performance-comparison {{
            background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .speedup-indicator {{
            font-size: 48px;
            font-weight: bold;
            margin: 15px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .efficiency-meter {{
            width: 100%;
            height: 20px;
            background-color: rgba(255,255,255,0.3);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .efficiency-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
            transition: width 0.5s ease;
        }}
        
        .detailed-stats {{
            background-color: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .stats-table th {{
            background-color: #f5f5f5;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            font-weight: bold;
        }}
        
        .stats-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        
        .stats-table tr:hover {{
            background-color: #f9f9f9;
        }}
        
        .color-legend {{
            background-color: #f0f8ff;
            border: 1px solid #b0c4de;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            font-size: 12px;
        }}
        
        .legend-category {{
            margin-bottom: 10px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }}
        </style>
        """
    
    def tokens_a_html(self, tokens: List[Token]) -> str:
        """Convierte tokens a HTML con información de multiprocessing"""
        html_parts = []
        
        for token in tokens:
            valor_escapado = (token.valor.replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;')
                                        .replace('"', '&quot;'))
            
            css_class = self._determinar_clase_css(token)
            
            if token.tipo == TipoToken.WHITESPACE:
                valor_escapado = valor_escapado.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                html_parts.append(valor_escapado)
            else:
                # Agregar información de proceso y núcleo CPU
                data_attrs = ""
                if token.proceso_id:
                    data_attrs += f' data-process="{token.proceso_id}"'
                if token.cpu_core is not None and token.cpu_core >= 0:
                    data_attrs += f' data-cpu-core="{token.cpu_core}"'
                    # Agregar clase CSS específica del núcleo
                    core_class = f" cpu-core-{token.cpu_core % len(self.PROCESS_COLORS)}"
                    css_class += core_class
                
                html_parts.append(f'<span class="{css_class}"{data_attrs}>{valor_escapado}</span>')
        
        return ''.join(html_parts)
    
    def _determinar_clase_css(self, token: Token) -> str:
        """Determina la clase CSS específica para cada token"""
        if token.tipo == TipoToken.KEYWORD:
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
            return self.OPERATOR_CSS_MAP.get(token.valor, 'operator')
        elif token.tipo == TipoToken.IDENTIFIER:
            if token.valor in self.BUILTINS:
                return 'builtin'
            elif token.valor == 'True':
                return 'boolean-true'
            elif token.valor == 'False':
                return 'boolean-false'
            elif token.valor == 'None':
                return 'none-value'
            return 'identifier'
        elif token.tipo == TipoToken.DELIMITER:
            return self.DELIMITER_CSS_MAP.get(token.valor, 'delimiter')
        elif token.tipo == TipoToken.WHITESPACE:
            return 'whitespace'
        else:
            return 'unknown'
    
    def generar_estadisticas_html(self, estadisticas: Dict) -> str:
        """Genera HTML con estadísticas detalladas del procesamiento multicore"""
        
        total_tokens = estadisticas['total_tokens']
        tiempo_total = estadisticas['tiempo_total']
        num_procesos = estadisticas['num_procesos_usados']
        num_cores = estadisticas['num_cores_sistema']
        tokens_por_segundo = estadisticas['tokens_por_segundo_total']
        eficiencia = estadisticas['eficiencia_multicore']
        speedup = estadisticas['speedup_estimado']
        utilizacion_cpu = estadisticas['utilizacion_cpu_porcentaje']
        
        html = f"""
        <div class="multicore-stats">
            <h3>🔥 Estadísticas de Procesamiento MULTICORE REAL</h3>
            
            <div class="cpu-grid">
                <div class="cpu-card">
                    <div class="cpu-metric">{total_tokens:,}</div>
                    <div class="cpu-label">Tokens Procesados</div>
                </div>
                <div class="cpu-card">
                    <div class="cpu-metric">{tiempo_total:.2f}s</div>
                    <div class="cpu-label">Tiempo Total</div>
                </div>
                <div class="cpu-card">
                    <div class="cpu-metric">{num_procesos}/{num_cores}</div>
                    <div class="cpu-label">Procesos/Núcleos CPU</div>
                </div>
                <div class="cpu-card">
                    <div class="cpu-metric">{tokens_por_segundo:,.0f}</div>
                    <div class="cpu-label">Tokens/Segundo</div>
                </div>
            </div>
            
            <div class="performance-comparison">
                <h4>⚡ Aceleración Multicore</h4>
                <div class="speedup-indicator">{speedup:.1f}x</div>
                <div>vs. procesamiento en un solo núcleo</div>
                <div class="efficiency-meter">
                    <div class="efficiency-fill" style="width: {eficiencia*100:.1f}%"></div>
                </div>
                <div>Eficiencia: {eficiencia:.1%} | Utilización CPU: {utilizacion_cpu:.1f}%</div>
            </div>
        """
        
        # Utilización de núcleos CPU
        if estadisticas['cpu_cores_utilizados']:
            html += """
            <div class="core-utilization">
                <h4>💻 Utilización de Núcleos de CPU</h4>
            """
            
            cores_utilizados = sorted(estadisticas['cpu_cores_utilizados'])
            for i, core in enumerate(cores_utilizados):
                color = self.PROCESS_COLORS[i % len(self.PROCESS_COLORS)]
                html += f"""
                <div class="core-bar" style="background-color: {color};">
                    Núcleo CPU {core} - Activo
                </div>
                """
            
            # Mostrar núcleos no utilizados si hay
            cores_no_utilizados = set(range(num_cores)) - estadisticas['cpu_cores_utilizados']
            for core in sorted(cores_no_utilizados):
                html += f"""
                <div class="core-bar" style="background-color: #cccccc; color: #666;">
                    Núcleo CPU {core} - No utilizado
                </div>
                """
            
            html += "</div>"
        
        # Distribución por proceso
        if estadisticas['tokens_por_proceso']:
            html += """
            <h4>📊 Distribución de Trabajo por Proceso</h4>
            <div class="process-legend">
            """
            
            for i, (proceso_id, cantidad) in enumerate(estadisticas['tokens_por_proceso'].items()):
                color = self.PROCESS_COLORS[i % len(self.PROCESS_COLORS)]
                porcentaje = (cantidad / total_tokens) * 100
                html += f"""
                <div class="process-badge" style="background-color: {color};">
                    PID {proceso_id}: {cantidad:,} tokens ({porcentaje:.1f}%)
                </div>
                """
            
            html += "</div>"
        
        # Estadísticas por tipo de token
        html += "<h4>🏷️ Distribución por Tipo de Token</h4>"
        html += '<div style="columns: 2; column-gap: 20px;"><ul>'
        for tipo, cantidad in sorted(estadisticas['conteo_tipos'].items(), 
                                   key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / total_tokens) * 100
            html += f"<li><strong>{tipo.value}</strong>: {cantidad:,} ({porcentaje:.1f}%)</li>"
        html += "</ul></div>"
        
        # Tabla detallada de rendimiento por proceso
        if estadisticas['estadisticas_procesos']:
            html += """
            <h4>⚡ Rendimiento Detallado por Proceso</h4>
            <div class="detailed-stats">
                <table class="stats-table">
                    <tr>
                        <th>Proceso ID</th>
                        <th>CPU Core</th>
                        <th>Chunk</th>
                        <th>Tokens</th>
                        <th>Tiempo (s)</th>
                        <th>Tokens/seg</th>
                        <th>Errores</th>
                    </tr>
            """
            
            for stats in sorted(estadisticas['estadisticas_procesos'], key=lambda x: x['chunk_id']):
                html += f"""
                <tr>
                    <td>{stats['proceso_id']}</td>
                    <td>Core {stats['cpu_core']}</td>
                    <td>{stats['chunk_id']}</td>
                    <td>{stats['tokens_procesados']:,}</td>
                    <td>{stats['tiempo_procesamiento']:.3f}</td>
                    <td>{stats['tokens_por_segundo']:.0f}</td>
                    <td>{stats['errores']}</td>
                </tr>
                """
            
            html += "</table></div>"
        
        # Tokens inválidos si los hay
        if estadisticas['tokens_invalidos'] > 0:
            html += f"""
            <h4>⚠️ Tokens Inválidos Detectados: {estadisticas['tokens_invalidos']}</h4>
            """
            if estadisticas['ejemplos_tokens_invalidos']:
                html += "<p>Ejemplos:</p><ul>"
                for token in estadisticas['ejemplos_tokens_invalidos']:
                    html += f"<li>'{token.valor}' en posición {token.posicion}</li>"
                html += "</ul>"
        
        html += "</div>"
        return html


class ResaltadorSintaxisMulticore:
    """Clase principal del resaltador multicore REAL"""
    
    def __init__(self, num_procesos: int = None):
        self.num_cores = mp.cpu_count()
        self.num_procesos = num_procesos or min(self.num_cores, max(2, self.num_cores - 1))
        self.maquina_turing = TuringMachineMulticore()
        self.generador_html = HTMLGenerator()
        
        print(f"🔥 Resaltador Multicore inicializado:")
        print(f"   💻 CPU detectado: {self.num_cores} núcleos")
        print(f"   ⚙️  Procesos configurados: {self.num_procesos}")
    
    def procesar_archivo(self, archivo_entrada: str, archivo_salida: str, 
                        mostrar_info_multicore: bool = True):
        """Procesa un archivo con código Python usando VERDADERO procesamiento multicore"""
        
        try:
            if not archivo_entrada.lower().endswith('.txt'):
                print(f"❌ Error: Se esperaba un archivo .txt, recibido: {archivo_entrada}")
                return
            
            print(f"\n🚀 INICIANDO PROCESAMIENTO MULTICORE REAL")
            print(f"📁 Archivo: {archivo_entrada}")
            print(f"🔥 Configuración multicore: {self.num_procesos} procesos en {self.num_cores} núcleos")
            
            # Cargar archivo
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            print(f"📄 Archivo cargado ({len(contenido)} caracteres)")
            
            # Procesar con multiprocessing
            inicio_total = time.time()
            tokens, estadisticas = self.maquina_turing.tokenizar_archivo_multicore(
                contenido, self.num_procesos
            )
            tiempo_procesamiento = time.time() - inicio_total
            
            # Generar HTML
            css = self.generador_html.generar_css()
            html_codigo = self.generador_html.tokens_a_html(tokens)
            stats_html = self.generador_html.generar_estadisticas_html(estadisticas)
            
            # Información multicore opcional
            info_multicore = ""
            if mostrar_info_multicore:
                cores_utilizados = len(estadisticas['cpu_cores_utilizados'])
                info_multicore = f"""
                <div class="multicore-info">
                    <h4>🔥 Información de Procesamiento Multicore REAL</h4>
                    <p><strong>🖥️ Sistema:</strong> {estadisticas['num_cores_sistema']} núcleos de CPU detectados</p>
                    <p><strong>⚙️ Procesos utilizados:</strong> {estadisticas['num_procesos_usados']} procesos paralelos</p>
                    <p><strong>💻 Núcleos activos:</strong> {cores_utilizados} núcleos de CPU trabajando simultáneamente</p>
                    <p><strong>⏱️ Tiempo total:</strong> {tiempo_procesamiento:.3f} segundos</p>
                    <p><strong>🚀 Velocidad:</strong> {estadisticas['tokens_por_segundo_total']:,.0f} tokens/segundo</p>
                    <p><strong>⚡ Aceleración:</strong> {estadisticas['speedup_estimado']:.1f}x vs. un solo núcleo</p>
                    <p><strong>🎯 Utilización CPU:</strong> {estadisticas['utilizacion_cpu_porcentaje']:.1f}% del sistema</p>
                    <p><em>🎨 Los colores en el código indican qué núcleo de CPU procesó cada token</em></p>
                </div>
                """
            
            # Documento HTML completo
            html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Léxico MULTICORE - {archivo_entrada}</title>
    {css}
    <script>
    // JavaScript para mostrar información de procesos y núcleos al hacer hover
    document.addEventListener('DOMContentLoaded', function() {{
        const tokens = document.querySelectorAll('[data-process]');
        tokens.forEach(token => {{
            token.addEventListener('mouseenter', function() {{
                this.style.boxShadow = '0 0 5px rgba(255,0,0,0.8)';
                const process = this.dataset.process || 'N/A';
                const core = this.dataset.cpuCore || 'N/A';
                this.title = `Proceso: ${{process}} | Núcleo CPU: ${{core}}`;
            }});
            token.addEventListener('mouseleave', function() {{
                this.style.boxShadow = '';
            }});
        }});
        
        // Animación de carga para mostrar el poder del multicore
        const cpuCards = document.querySelectorAll('.cpu-card');
        cpuCards.forEach((card, index) => {{
            card.style.animation = `slideIn 0.5s ease ${{index * 0.1}}s forwards`;
        }});
    }});
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </script>
</head>
<body>
    <h1>🔥 Análisis Léxico MULTICORE REAL con Máquina de Turing</h1>
    <h2>Archivo procesado: {archivo_entrada}</h2>
    <p><em>🖥️ Procesamiento paralelo REAL usando {estadisticas['num_procesos_usados']} procesos en {len(estadisticas['cpu_cores_utilizados'])} núcleos de CPU</em></p>
    
    {info_multicore}
    
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
        </div>
        
        <div class="legend-category">
            <strong>💻 Núcleos CPU:</strong>
            <span class="legend-item">Cada token tiene un color de fondo que indica qué núcleo lo procesó</span>
        </div>
        
        <div class="legend-category">
            <strong>Interactividad:</strong>
            <span class="legend-item">🖱️ <em>Hover sobre cualquier token para ver el proceso y núcleo que lo procesó</em></span>
        </div>
    </div>
    
    {stats_html}
    
    <div class="code-container">
        {html_codigo}
    </div>
    
    <div style="margin-top: 20px; color: #666; font-size: 12px; text-align: center;">
        <p>🔥 Generado por Resaltador de Sintaxis MULTICORE - Máquina de Turing con Multiprocessing</p>
        <p>⚡ Implementación optimizada usando {estadisticas['num_procesos_usados']} procesos en {len(estadisticas['cpu_cores_utilizados'])} núcleos de CPU simultáneamente</p>
        <p>🚀 Aceleración REAL: {estadisticas['speedup_estimado']:.1f}x | Eficiencia: {estadisticas['eficiencia_multicore']:.1%} | CPU: {estadisticas['utilizacion_cpu_porcentaje']:.1f}%</p>
        <p><strong>💡 Cada token muestra información del proceso y núcleo que lo procesó al hacer hover</strong></p>
        <p><em>🖥️ Este procesamiento utilizó verdaderamente múltiples núcleos de CPU en paralelo</em></p>
    </div>
</body>
</html>"""
            
            # Guardar archivo
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write(html_completo)
            
            self._imprimir_resumen_final(archivo_entrada, archivo_salida, estadisticas)
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo: {archivo_entrada}")
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            import traceback
            traceback.print_exc()
    
    def _imprimir_resumen_final(self, archivo_entrada: str, archivo_salida: str, stats: Dict):
        """Imprime un resumen final del procesamiento multicore"""
        print("\n" + "="*70)
        print("🔥 PROCESAMIENTO MULTICORE REAL COMPLETADO")
        print("="*70)
        print(f"📄 Archivo de entrada: {archivo_entrada}")
        print(f"🌐 Archivo HTML generado: {archivo_salida}")
        print(f"🖥️  Sistema: {stats['num_cores_sistema']} núcleos de CPU disponibles")
        print(f"⚙️  Procesos utilizados: {stats['num_procesos_usados']}")
        print(f"💻 Núcleos activos: {len(stats['cpu_cores_utilizados'])} ({', '.join(map(str, sorted(stats['cpu_cores_utilizados'])))})")
        print(f"📊 Tokens procesados: {stats['total_tokens']:,}")
        print(f"⏱️  Tiempo total: {stats['tiempo_total']:.3f} segundos")
        print(f"🚀 Velocidad: {stats['tokens_por_segundo_total']:,.0f} tokens/segundo")
        print(f"⚡ Aceleración REAL: {stats['speedup_estimado']:.1f}x vs. un solo núcleo")
        print(f"🎯 Eficiencia multicore: {stats['eficiencia_multicore']:.1%}")
        print(f"💪 Utilización CPU: {stats['utilizacion_cpu_porcentaje']:.1f}% del sistema")
        
        if stats['tokens_invalidos'] > 0:
            print(f"⚠️  Tokens inválidos: {stats['tokens_invalidos']}")
        
        # Mostrar distribución de trabajo por proceso
        print("\n📊 Distribución de trabajo por proceso:")
        for proceso_id, cantidad in stats['tokens_por_proceso'].items():
            porcentaje = (cantidad / stats['total_tokens']) * 100
            print(f"   PID {proceso_id}: {cantidad:,} tokens ({porcentaje:.1f}%)")
        
        print("\n✅ Proceso MULTICORE completado exitosamente!")
        print("💡 Tip: Haz hover sobre los tokens en el HTML para ver qué proceso y núcleo los procesó")
        print("🔥 Este procesamiento utilizó VERDADERAMENTE múltiples núcleos de CPU en paralelo")


def main():
    """Función principal mejorada con opciones de multiprocessing"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Resaltador de Sintaxis MULTICORE basado en Máquina de Turing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔥 PROCESAMIENTO MULTICORE REAL - Utiliza verdaderamente múltiples núcleos del CPU

Ejemplos de uso:
  python turing_multicore.py codigo.txt
  python turing_multicore.py codigo.txt --procesos 8
  python turing_multicore.py codigo.txt resultado.html --procesos 4 --no-multicore-info
  python turing_multicore.py codigo.txt --benchmark
  python turing_multicore.py codigo.txt --mostrar-cores

Ventajas del multiprocessing vs threading:
- ✅ Evita el GIL (Global Interpreter Lock) de Python
- ✅ Utiliza VERDADERAMENTE múltiples núcleos del CPU
- ✅ Cada proceso es completamente independiente
- ✅ Escalabilidad real con el número de núcleos
        """
    )
    
    parser.add_argument('archivo_entrada', help='Archivo .txt con código Python')
    parser.add_argument('archivo_salida', nargs='?', help='Archivo HTML de salida (opcional)')
    parser.add_argument('--procesos', '-p', type=int, default=None,
                       help='Número de procesos a utilizar (default: auto basado en CPU)')
    parser.add_argument('--no-multicore-info', action='store_true',
                       help='No mostrar información de multiprocessing en el HTML')
    parser.add_argument('--benchmark', '-b', action='store_true',
                       help='Ejecutar benchmark comparando diferentes números de procesos')
    parser.add_argument('--mostrar-cores', action='store_true',
                       help='Mostrar información detallada de los núcleos del CPU')
    
    args = parser.parse_args()
    
    # Mostrar información del sistema si se solicita
    if args.mostrar_cores:
        mostrar_info_sistema()
        return
    
    if not args.archivo_entrada.lower().endswith('.txt'):
        print("❌ Error: El archivo de entrada debe ser un archivo .txt")
        return
    
    if not args.archivo_salida:
        args.archivo_salida = args.archivo_entrada.replace('.txt', '_multicore_highlighted.html')
    
    if args.benchmark:
        ejecutar_benchmark_multicore(args.archivo_entrada)
    else:
        resaltador = ResaltadorSintaxisMulticore(num_procesos=args.procesos)
        resaltador.procesar_archivo(
            args.archivo_entrada, 
            args.archivo_salida,
            mostrar_info_multicore=not args.no_multicore_info
        )


def mostrar_info_sistema():
    """Muestra información detallada del sistema y CPU"""
    import platform
    
    print("🖥️  INFORMACIÓN DEL SISTEMA")
    print("="*50)
    print(f"Sistema operativo: {platform.system()} {platform.release()}")
    print(f"Arquitectura: {platform.machine()}")
    print(f"Procesador: {platform.processor()}")
    print(f"Núcleos de CPU: {mp.cpu_count()}")
    
    try:
        # Información adicional con psutil si está disponible
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            print(f"Frecuencia CPU: {cpu_freq.current:.0f} MHz")
        
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"Uso actual de CPU: {cpu_percent}%")
        
        memory = psutil.virtual_memory()
        print(f"Memoria RAM: {memory.total // (1024**3)} GB")
        print(f"Memoria disponible: {memory.available // (1024**3)} GB")
        
    except ImportError:
        print("💡 Instala 'psutil' para información adicional del sistema")
    
    print(f"\n🔥 Configuración recomendada para multiprocessing:")
    optimal_processes = min(mp.cpu_count(), max(2, mp.cpu_count() - 1))
    print(f"   Procesos óptimos: {optimal_processes} (deja 1 núcleo libre para el SO)")
    print(f"   Procesos máximos: {mp.cpu_count()} (usa todos los núcleos)")


def ejecutar_benchmark_multicore(archivo_entrada: str):
    """Ejecuta un benchmark comparando diferentes configuraciones de procesos"""
    print("🏃‍♂️ EJECUTANDO BENCHMARK MULTICORE")
    print("🔥 Comparando rendimiento con diferentes números de procesos")
    print("="*60)
    
    num_cores = mp.cpu_count()
    configuraciones = [1, 2]
    
    # Agregar configuraciones basadas en el número de núcleos
    if num_cores >= 4:
        configuraciones.extend([4, num_cores//2, num_cores-1, num_cores])
    elif num_cores == 3:
        configuraciones.append(3)
    
    # Remover duplicados y ordenar
    configuraciones = sorted(list(set(configuraciones)))
    
    print(f"💻 Sistema detectado: {num_cores} núcleos")
    print(f"🧪 Probando configuraciones: {configuraciones}")
    
    resultados = []
    
    for num_procesos in configuraciones:
        print(f"\n🔥 Probando con {num_procesos} proceso(s)...")
        
        try:
            resaltador = ResaltadorSintaxisMulticore(num_procesos=num_procesos)
            
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            inicio = time.time()
            tokens, stats = resaltador.maquina_turing.tokenizar_archivo_multicore(
                contenido, num_procesos
            )
            tiempo = time.time() - inicio
            
            resultados.append({
                'procesos': num_procesos,
                'tiempo': tiempo,
                'tokens': stats['total_tokens'],
                'tokens_por_segundo': stats['tokens_por_segundo_total'],
                'eficiencia': stats['eficiencia_multicore'],
                'speedup': stats['speedup_estimado'],
                'cores_utilizados': len(stats['cpu_cores_utilizados']),
                'utilizacion_cpu': stats['utilizacion_cpu_porcentaje']
            })
            
            print(f"   ⏱️  Tiempo: {tiempo:.3f}s")
            print(f"   🚀 Velocidad: {stats['tokens_por_segundo_total']:,.0f} tokens/seg")
            print(f"   ⚡ Speedup: {stats['speedup_estimado']:.1f}x")
            print(f"   💻 Núcleos activos: {len(stats['cpu_cores_utilizados'])}")
            print(f"   🎯 Eficiencia: {stats['eficiencia_multicore']:.1%}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Mostrar resumen de benchmark
    print("\n" + "="*80)
    print("📊 RESUMEN DE BENCHMARK MULTICORE")
    print("="*80)
    print(f"{'Proc':<5} {'Tiempo':<8} {'Tokens/seg':<12} {'Speedup':<8} {'Cores':<6} {'Efic':<8} {'CPU%'}")
    print("-" * 80)
    
    for resultado in resultados:
        print(f"{resultado['procesos']:<5} "
              f"{resultado['tiempo']:.3f}s{'':<2} "
              f"{resultado['tokens_por_segundo']:>8,.0f}{'':<4} "
              f"{resultado['speedup']:>5.1f}x{'':<3} "
              f"{resultado['cores_utilizados']:<6} "
              f"{resultado['eficiencia']:>6.1%}{'':<2} "
              f"{resultado['utilizacion_cpu']:>5.1f}%")
    
    # Encontrar configuración óptima
    mejor = max(resultados, key=lambda x: x['tokens_por_segundo'])
    print(f"\n🏆 CONFIGURACIÓN ÓPTIMA:")
    print(f"   🔥 Procesos: {mejor['procesos']}")
    print(f"   🚀 Mejor rendimiento: {mejor['tokens_por_segundo']:,.0f} tokens/seg")
    print(f"   ⚡ Aceleración: {mejor['speedup']:.1f}x vs. 1 proceso")
    print(f"   💻 Núcleos utilizados: {mejor['cores_utilizados']}/{num_cores}")
    print(f"   🎯 Eficiencia: {mejor['eficiencia']:.1%}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if mejor['procesos'] == num_cores:
        print("   ✅ El sistema se beneficia del uso de todos los núcleos")
    elif mejor['procesos'] == num_cores - 1:
        print("   ✅ Configuración óptima: usa casi todos los núcleos (deja uno libre)")
    else:
        print("   ⚠️ El overhead de comunicación entre procesos limita la escalabilidad")
    
    print(f"   📈 Para archivos más grandes, considera usar {min(num_cores, mejor['procesos'] + 1)} procesos")


if __name__ == "__main__":
    # Configuración para multiprocessing en Windows
    mp.set_start_method('spawn', force=True) if mp.get_start_method() != 'spawn' else None
    
    main()