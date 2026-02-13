#!/bin/bash
# Firmar APK para Google Play Store
# Usage: ./sign-apk.sh

set -e

ANDROID_DIR="android/app/build/outputs/apk/release"
APK_NAME="app-release-unsigned.apk"
SIGNED_NAME="app-release-signed.apk"
KEYSTORE="release.keystore"
KEY_ALIAS="sportsCardAI"
STORE_PASSWORD="change_me"
KEY_PASSWORD="change_me"

echo "=== Firmar APK para Google Play ==="

# Verificar APK existe
if [ ! -f "$ANDROID_DIR/$APK_NAME" ]; then
    echo "Error: No se encontró $APK_NAME"
    echo "Ejecuta: ./gradlew assembleRelease"
    exit 1
fi

# Crear keystore si no existe
if [ ! -f "$KEYSTORE" ]; then
    echo "1. Creando keystore..."
    keytool -genkey -v -keystore "$KEYSTORE" -alias "$KEY_ALIAS" \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass "$STORE_PASSWORD" -keypass "$KEY_PASSWORD" \
        -dname "CN=Sports Card AI, OU=Dev, O=SportsCardAI, L=City, ST=State, C=US"
fi

# Firmar APK
echo "2. Firmando APK..."
$JAVA_HOME/bin/jarsigner -verbose \
    -keystore "$KEYSTORE" \
    -storepass "$STORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -signedjar "$ANDROID_DIR/$SIGNED_NAME" \
    "$ANDROID_DIR/$APK_NAME" \
    "$KEY_ALIAS"

# Verificar firma
echo "3. Verificando firma..."
$JAVA_HOME/bin/jarsigner -verify -verbose "$ANDROID_DIR/$SIGNED_NAME"

echo ""
echo "=== APK firmado exitosamente ==="
echo "Ubicación: $ANDROID_DIR/$SIGNED_NAME"
echo ""
echo "Para Google Play:"
echo "1. Crea una cuenta en Google Play Console"
echo "2. Sube el APK firmado a Release Management"
echo "3. Completa la información de la app"
