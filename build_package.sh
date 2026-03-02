#!/bin/bash
# Script para construir el paquete Debian para escuela-domain-joiner

# Obtener versión y arquitectura del archivo de control
VERSION=$(grep -oP 'Version: \K.*' DEBIAN/control)
ARCH=$(grep -oP 'Architecture: \K.*' DEBIAN/control)
PACKAGE_NAME=$(grep -oP 'Package: \K.*' DEBIAN/control)

# Definir el nombre del archivo de salida
FILENAME="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Construyendo paquete: $FILENAME"

# Construir el paquete
# El comando dpkg-deb --build <directorio> [paquete]
# El primer argumento es el directorio que contiene el directorio DEBIAN y los archivos a empaquetar.
# El segundo argumento (opcional) es el nombre del paquete a generar.
dpkg-deb --build . "${FILENAME}"

if [ $? -eq 0 ]; then
  echo "Paquete construido exitosamente: ${FILENAME}"
  echo "El archivo se encuentra en: $(pwd)/${FILENAME}"
else
  echo "Error al construir el paquete."
fi
