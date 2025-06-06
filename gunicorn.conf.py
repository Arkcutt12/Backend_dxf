import multiprocessing

# Número de workers
workers = multiprocessing.cpu_count() * 2 + 1

# Configuración del worker
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Configuración del servidor
bind = "0.0.0.0:8000"
backlog = 2048

# Configuración de logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Configuración de seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190 