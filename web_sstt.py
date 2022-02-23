# coding=utf-8
#!/usr/bin/env python3

import socket
import selectors    #https://docs.python.org/3/library/selectors.html
import select
import types        # Para definir el tipo de datos data
import argparse     # Leer parametros de ejecución
import os           # Obtener ruta y extension
from datetime import datetime, timedelta # Fechas de los mensajes HTTP
import time         # Timeout conexión
import sys          # sys.exit
import re           # Analizador sintáctico
import logging      # Para imprimir logs


BUFSIZE = 8192 # Tamaño máximo del buffer que se puede utilizar
TIMEOUT_CONNECTION = 20 # Timout para la conexión persistente
MAX_ACCESOS = 10

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


def enviar_mensaje(cs, data):
    """ Esta función envía datos (data) a través del socket cs
        Devuelve el número de bytes enviados.
    """
    return cs.send(data.encode())


def recibir_mensaje(cs,data):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    data = (cs.recv(data)).decode()
    return data


def cerrar_conexion(cs):
    """ Esta función cierra una conexión activa.
    """
    return cs.close()


def process_cookies(headers,  cs):
    """ Esta función procesa la cookie cookie_counter
        1. Se analizan las cabeceras en headers para buscar la cabecera Cookie
        2. Una vez encontrada una cabecera Cookie se comprueba si el valor es cookie_counter
        3. Si no se encuentra cookie_counter , se devuelve 1
        4. Si se encuentra y tiene el valor MAX_ACCESSOS se devuelve MAX_ACCESOS
        5. Si se encuentra y tiene un valor 1 <= x < MAX_ACCESOS se incrementa en 1 y se devuelve el valor
    """
    pass


def process_web_request(cs, webroot):
    """ Procesamiento principal de los mensajes recibidos.
        Típicamente se seguirá un procedimiento similar al siguiente (aunque el alumno puede modificarlo si lo desea)
    """
    " * Bucle para esperar hasta que lleguen datos en la red a través del socket cs con select() "
        rsublist, wsublist, xsublist = select.select([cs],[],[cs],TIMEOUT_CONNECTION)
        # * Se comprueba si hay que cerrar la conexión por exceder TIMEOUT_CONNECTION segundos
        # sin recibir ningún mensaje o hay datos. Se utiliza select.select
        if not (rsublist or xsublist):
            print("Error: Timeout exceeded")
            cs.close()
            return
         # * Si no es por timeout y hay datos en el socket cs.
        elif not xsublist:           
            # * Leer los datos con recv.
            data = cs.recv(BUFSIZE)
            data = data.decode()
            data = data.split('\r\n')
            # * Analizar que la línea de solicitud y comprobar está bien formateada según HTTP 1.1
            patron_met = r'([A-Z]*) (.*) HTTP\/1.({0-4})\\r\\n'   ## Expresión regular para la primera línea del mensaje
            patron_atrib = r'(([A-Za-z-]*): (.*)\\r\\n)'   ## Expresión regular para los atributos
            er_met = re.compile(patron_met)
            er_atrib = re.compile(patron_atrib)

            reg = er_met.fullmatch(data[0])
            if not reg:
                cs.close()
                print("Not HTTP message\n")
            else:

                if string(reg.group(1)) != "GET":
                    print("Error 405: Method not allowed")
                    cs.close()
                    exit()
                # * Comprobar si la versión de HTTP es 1.1
                if int(reg.group(3)) != 1:
                    print("Error: Not HTTP version")
                # * Leer URL y eliminar parámetros si los hubiera
                URL = reg.group(2).split('?',1)

                # * Devuelve una lista con los atributos de las cabeceras.
                Atr = {}
                for i in [1 - len(data)]:
                    reg = er_atrib.fullmatch(data[i])
                    Atr[string(reg.group(1))] = string(reg.group(2))


                # * Comprobar si es un método GET. Si no devolver un error Error 405 "Method Not Allowed".
                # * Leer URL y eliminar parámetros si los hubiera
                # * Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
                # * Construir la ruta absoluta del recurso (webroot + recurso solicitado)
                # * Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
                # * Analizar las cabeceras. Imprimir cada cabecera y su valor. Si la cabecera es Cookie comprobar
                #  el valor de cookie_counter para ver si ha llegado a MAX_ACCESOS.
                #  Si se ha llegado a MAX_ACCESOS devolver un Error "403 Forbidden"
                # * Obtener el tamaño del recurso en bytes.
                # * Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                # * Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                #  las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                #  Content-Length y Content-Type.
                # * Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                # * Se abre el fichero en modo lectura y modo binario
                #    * Se lee el fichero en bloques de BUFSIZE bytes (8KB)
                #    * Cuando ya no hay más información para leer, se corta el bucle

        # * Si es por timeout, se cierra el socket tras el período de persistencia.
            # * NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.



def main():
    """ Función principal del servidor
    """
    try:

        # Argument parser para obtener la ip y puerto de los parámetros de ejecución del programa. IP por defecto 0.0.0.0
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="Puerto del servidor", type=int, required=True)
        parser.add_argument("-ip", "--host", help="Dirección IP del servidor o localhost", required=True)
        parser.add_argument("-wb", "--webroot", help="Directorio base desde donde se sirven los ficheros (p.ej. /home/user/mi_web)")
        parser.add_argument('--verbose', '-v', action='store_true', help='Incluir mensajes de depuración en la salida')
        args = parser.parse_args()


        if args.verbose:
            logger.setLevel(logging.DEBUG)

        logger.info('Enabling server in address {} and port {}.'.format(args.host, args.port))

        logger.info("Serving files from {}".format(args.webroot))

        """ Funcionalidad a realizar """
        ## * Crea un socket TCP (SOCK_STREAM)
        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

        ## * Permite reusar la misma dirección previamente vinculada a otro proceso. Debe ir antes de sock.bind
        mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ## * Vinculamos el socket a una IP y puerto elegidos
        mysocket.bind( (args.host, args.port) )

        ## * Escucha conexiones entrantes
        mysocket.listen()

        ## * Bucle infinito para mantener el servidor activo indefinidamente
        while True:
            ## - Aceptamos la conexión
            conn, addr = mysocket.accept()
            ## - Creamos un proceso hijo
            pid = os.fork()
            ## - Si es el proceso hijo se cierra el socket del padre y procesar la petición con process_web_request()
            if not pid:
                mysocket.close()
                process_web_request( conn , args.webroot)
            ##- Si es el proceso padre cerrar el socket que gestiona el hijo.
            else:
                conn.close()
    except KeyboardInterrupt:
        True

if __name__== "__main__":
    main()

"""
    Solo codificamos el texto, no las imágenes

"""