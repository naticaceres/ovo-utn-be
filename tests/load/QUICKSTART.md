# Inicio Rápido - Pruebas de Carga

## 🚀 Pasos Rápidos

### 1. Instalar dependencias

```bash
pip install -r requirements-dev.txt
```

### 2. Iniciar servidor mock

```bash
cd tests/load
./run_mock_server.sh
```

### 3. Ejecutar prueba de carga

**En otra terminal:**

**CP010 - Búsqueda en tableros:**
```bash
cd tests/load
./run_load_test.sh cp010 http://localhost:8000
```

**CP011 - Finalización de test e informe:**
```bash
cd tests/load
./run_load_test.sh cp011 http://localhost:8000
```

**CP012 - Autenticación y sesión:**
```bash
cd tests/load
./run_load_test.sh cp012 http://localhost:8000
```

**CP013 - Generación de reportes institucionales:**
```bash
cd tests/load
./run_load_test.sh cp013 http://localhost:8000
```

### 4. Ver resultados

Los resultados se muestran automáticamente al finalizar. También puedes abrir el reporte HTML:

```bash
open reports/report_cp010_*.html
# o
open reports/report_cp011_*.html
```

## ✅ Verificar Umbrales

### CP010
- **Tiempo promedio**: ≤ 5 segundos
- **Tiempo máximo**: ≤ 10 segundos  
- **Tasa de error**: < 1%

### CP011
- **Persistencia (finish)**: ≤ 3 segundos
- **Informe (report)**: ≤ 6 segundos
- **Tasa de error**: < 1%

### CP012
- **Tiempo promedio**: ≤ 6 segundos
- **Tasa de error**: < 1%

### CP013
- **Tiempo promedio**: ≤ 15 segundos
- **Tasa de error**: < 1%

## 📚 Documentación Completa

Ver [README.md](README.md) para más detalles.
