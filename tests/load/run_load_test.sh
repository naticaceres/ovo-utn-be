#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

TEST_CASE="${1:-cp010}"
API_BASE_URL="${2:-${API_BASE_URL:-}}"
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
RUN_TIME="1m"
OUTPUT_DIR="reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$API_BASE_URL" ]; then
    echo -e "${RED}❌ Error: Se requiere la URL base de la API${NC}"
    echo ""
    echo "Uso: ./run_load_test.sh [TEST_CASE] [API_BASE_URL]"
    echo ""
    echo "Test cases disponibles:"
    echo "  cp010 - Búsqueda/filtrado en tableros"
    echo "  cp011 - Finalización de test y generación de informe"
    echo "  cp012 - Autenticación y sesión bajo carga concurrente"
    echo "  cp013 - Generación de reportes institucionales bajo carga"
    echo ""
    echo "Ejemplo:"
    echo "  ./run_load_test.sh cp010 http://localhost:8000"
    exit 1
fi

case $TEST_CASE in
    cp010)
        LOCUSTFILE="cp010/locustfile.py"
        TEST_NAME="CP010"
        ;;
    cp011)
        LOCUSTFILE="cp011/locustfile.py"
        TEST_NAME="CP011"
        ;;
    cp012)
        LOCUSTFILE="cp012/locustfile.py"
        TEST_NAME="CP012"
        ;;
    cp013)
        LOCUSTFILE="cp013/locustfile.py"
        TEST_NAME="CP013"
        ;;
    *)
        echo -e "${RED}❌ Test case inválido: $TEST_CASE${NC}"
        echo "Test cases disponibles: cp010, cp011, cp012, cp013"
        exit 1
        ;;
esac

if [ ! -f "$LOCUSTFILE" ]; then
    echo -e "${RED}❌ Error: No se encontró $LOCUSTFILE${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Iniciando prueba de carga ${TEST_NAME}${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Configuración:"
echo "   Test Case: ${TEST_NAME}"
echo "   API Base URL: $API_BASE_URL"
echo "   Usuarios concurrentes: $USERS"
echo "   Spawn rate: $SPAWN_RATE usuarios/segundo"
echo "   Duración: $RUN_TIME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p "$OUTPUT_DIR"
HTML_REPORT="$OUTPUT_DIR/report_${TEST_CASE}_${TIMESTAMP}.html"
CSV_PREFIX="$OUTPUT_DIR/results_${TEST_CASE}_${TIMESTAMP}"

echo -e "${YELLOW}⏳ Ejecutando prueba...${NC}"
echo ""

locust -f "$LOCUSTFILE" \
  --host="$API_BASE_URL" \
  --users "$USERS" \
  --spawn-rate "$SPAWN_RATE" \
  --run-time "$RUN_TIME" \
  --headless \
  --html="$HTML_REPORT" \
  --csv="$CSV_PREFIX" \
  --loglevel INFO

echo ""
echo -e "${GREEN}✅ Prueba completada${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Reportes generados:"
echo "   HTML: $HTML_REPORT"
echo "   CSV:  ${CSV_PREFIX}_*.csv"
echo ""

if [ -f "${CSV_PREFIX}_stats.csv" ]; then
    echo -e "${BLUE}📈 Mostrando resultados...${NC}"
    echo ""
    python3 common/show_results.py "${CSV_PREFIX}_stats.csv" "$TEST_NAME"
fi

if [ -f "${CSV_PREFIX}_failures.csv" ]; then
    FAILURE_COUNT=$(tail -n +2 "${CSV_PREFIX}_failures.csv" 2>/dev/null | wc -l)
    if [ "$FAILURE_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Se detectaron $FAILURE_COUNT fallos. Revisa ${CSV_PREFIX}_failures.csv${NC}"
    fi
fi
