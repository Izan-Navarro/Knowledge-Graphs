INSTRUCCIONES PARA LEVANTAR EL ENTORNO Y EJECUTAR LA APP

1. Ejecutar Apache Jena Fuseki usando Docker:

   Abre una terminal y corre el siguiente comando:
```bash
   docker run -it --rm -p 3030:3030 --env ADMIN_PASSWORD=admin123 stain/jena-fuseki
```
   Esto iniciará el servidor Fuseki en el puerto 3030 con contraseña "admin123".

2. Crear y cargar la base de datos RDF:

   - Abre tu navegador y ve a http://localhost:3030
   - Crea un nuevo dataset (base de datos) con el nombre que prefieras.
   - Carga el archivo .ttl (Turtle) que contiene tus datos RDF en ese dataset.

3. Descargar e iniciar la aplicación Streamlit:

   - Abre otra terminal.
     
   - Instala la libreria streamlit
  
   ```bash
     pip install streamlit
   ```
     
   - Ejecuta el siguiente comando, reemplazando "ruta al archivo de la app" por la ruta completa donde esté tu archivo app.py:

     python -m streamlit run "ruta al archivo de la app"

   Por ejemplo:
```bash
     python -m streamlit run "ruta_al_archivo/app.py"
```
---

Asegúrate de que el endpoint SPARQL en tu aplicación (app.py) esté configurado para apuntar a la URL correcta  en Fuseki:

http://localhost:3030/NOMBRE_DEL_DATASET/sparql

---

