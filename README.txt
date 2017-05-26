Para probar el proyecto es necesario tener virtualenv instalado y python3

1. Clonamos el proyecto en nuestro ordenador
2. Creamos un entorno virtual con virtualenv y python3
3. Activamos el entorno virtual con "source entorno_virtual/bin/activate"
4. Ejecutamos "pip install -r requeriments.txt" en el directorio raiz del proyecto
5. En el directorio raiz ejecutamos "crossbar start" para levantar el servicio de crossbar(localhost:8080)
6. En el directorio "custom-app" ejecutamos "polymer serve" para levantar el servicio de prueba de polymer(localhost:8081)
7. Navegamos en el navegador a "localhost:8081" y probamos la webapp



*Para instalar crossbar es necesario tener python3.5-dev
