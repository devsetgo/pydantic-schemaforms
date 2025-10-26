# Makefile Commands for Pydantic Forms Examples

## ✅ **Updated Makefile Targets**

I've successfully updated the makefile targets to use the PORT and WORKER variables consistently and provide both development (reload) and production (workers) versions.

### 🚀 **Available Commands**

#### **Flask Examples**
```bash
make ex-flask           # Flask demo (development with reload)
make ex-flask-prod      # Flask demo (production with workers)
```

#### **FastAPI Examples**
```bash
make ex-fastapi         # FastAPI demo (development with reload)
make ex-fastapi-prod    # FastAPI demo (production with workers)
```

#### **Legacy/Other Examples**
```bash
make ex-run             # Run the main FastAPI application
make ex-f               # Run example flask application
```

### 📋 **Command Details**

| Command | Mode | Port Variable | Workers Variable | Features |
|---------|------|---------------|------------------|----------|
| `make ex-flask` | Development | ✅ ${PORT} | ❌ | Auto-reload, debug mode |
| `make ex-flask-prod` | Production | ✅ ${PORT} | ✅ ${WORKER} | Gunicorn, workers |
| `make ex-fastapi` | Development | ✅ ${PORT} | ❌ | Auto-reload, debug logging |
| `make ex-fastapi-prod` | Production | ✅ ${PORT} | ✅ ${WORKER} | Uvicorn workers |

### 🎯 **Usage Examples**

**Default Settings (PORT=5000, WORKER=8):**
```bash
make ex-flask           # Flask on port 5000
make ex-fastapi         # FastAPI on port 5000
make ex-flask-prod      # Flask with 8 workers on port 5000
make ex-fastapi-prod    # FastAPI with 8 workers on port 5000
```

**Custom Port:**
```bash
make ex-flask PORT=8080         # Flask on port 8080
make ex-fastapi PORT=9000       # FastAPI on port 9000
```

**Custom Workers:**
```bash
make ex-flask-prod WORKER=4     # Flask with 4 workers
make ex-fastapi-prod WORKER=16  # FastAPI with 16 workers
```

**Combined Overrides:**
```bash
make ex-fastapi-prod PORT=8000 WORKER=12  # FastAPI with 12 workers on port 8000
```

### 🔧 **Implementation Details**

#### **Environment Variable Support**
Both Flask and FastAPI demos now support environment variables:
- **Flask**: Uses `FLASK_PORT` environment variable
- **FastAPI**: Uses `FASTAPI_PORT` environment variable (for direct execution)

#### **Makefile Variables Used**
```makefile
PORT = 5000      # Default port for all services
WORKER = 8       # Default number of workers for production
LOG_LEVEL = debug # Logging level
```

#### **Development vs Production**
```makefile
# Development (with reload)
ex-flask: 
	cd examples && FLASK_PORT=${PORT} python3 unified_demo.py

ex-fastapi:
	cd examples && uvicorn fastapi_demo:app --host 0.0.0.0 --port ${PORT} --reload --log-level $(LOG_LEVEL)

# Production (with workers)
ex-flask-prod:
	cd examples && gunicorn -w ${WORKER} -b 0.0.0.0:${PORT} --log-level $(LOG_LEVEL) unified_demo:app

ex-fastapi-prod:
	cd examples && uvicorn fastapi_demo:app --host 0.0.0.0 --port ${PORT} --workers ${WORKER} --log-level $(LOG_LEVEL)
```

### ✅ **Features**

- **Consistent Variables**: All commands use `${PORT}` and `${WORKER}` makefile variables
- **Environment Support**: Flask and FastAPI apps respect environment variables
- **Development/Production**: Separate commands for reload vs workers
- **Flexible Configuration**: Override port and workers via command line
- **Help Integration**: All commands documented in `make help`
- **Devcontainer Ready**: Works seamlessly in devcontainer environments

### 📚 **See All Available Commands**
```bash
make help
```

### 🎉 **Benefits**

1. **Consistency**: All commands use the same PORT and WORKER variables
2. **Flexibility**: Easy to override defaults on command line
3. **Production Ready**: Separate production commands with worker support
4. **Development Friendly**: Reload enabled for development commands
5. **Environment Aware**: Apps adapt to environment variable configuration

The makefile now provides a complete, consistent interface for running pydantic-forms examples in both development and production modes! 🚀