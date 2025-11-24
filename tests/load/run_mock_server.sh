#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando servidor mock local${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Flask no está instalado. Instalando dependencias...${NC}"
    pip install -r requirements-dev.txt
    echo ""
fi

if [ ! -f "common/mock_server.py" ]; then
    echo -e "${YELLOW}❌ Error: common/mock_server.py no encontrado${NC}"
    echo "Asegúrate de ejecutar este script desde el directorio tests/load"
    exit 1
fi

echo -e "${BLUE}📋 Endpoints disponibles:${NC}"
echo "   GET  /api/dashboard/search (CP010)"
echo "   POST /api/tests/finish (CP011)"
echo "   GET  /api/tests/report (CP011)"
echo "   POST /api/auth/login (CP012)"
echo "   GET  /api/auth/validate (CP012)"
echo "   GET  /api/reportes/export (CP013)"
echo "   GET  /health"
echo ""
echo -e "${YELLOW}💡 Para probar manualmente:${NC}"
echo "   curl 'http://localhost:8000/api/dashboard/search?tipoCarrera=Todas'"
echo "   curl -X POST http://localhost:8000/api/tests/finish -H 'Content-Type: application/json' -d '{\"testId\":\"test123\",\"userId\":\"user456\"}'"
echo "   curl -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"usuario1@prueba.com\",\"password\":\"password123\"}'"
echo "   curl 'http://localhost:8000/api/reportes/export?formato=csv&institucionId=123&fechaDesde=01/01/2024&fechaHasta=31/12/2024'"
echo ""
echo -e "${GREEN}▶️  Iniciando servidor...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python common/mock_server.py
