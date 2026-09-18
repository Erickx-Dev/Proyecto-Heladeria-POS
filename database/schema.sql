-- ==============================================================================
-- SISTEMA DE GESTIÓN COMERCIAL, CONTROL DE INVENTARIO, CAJA Y POS - HELADERÍA
-- Módulo: Infraestructura de Persistencia Relacional (SQLite3)
-- Archivo: database/schema.sql
-- ==============================================================================

-- Habilitar expresamente restricciones de integridad referencial
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. TABLA: Rol
-- Catálogo de roles del sistema (Administrador, Empleado)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Rol (
    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_rol TEXT NOT NULL UNIQUE CHECK (length(trim(nombre_rol)) > 0)
);

-- ------------------------------------------------------------------------------
-- 2. TABLA: Usuario
-- Operadores del sistema con credenciales cifradas (bcrypt)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    username TEXT NOT NULL UNIQUE CHECK (length(trim(username)) >= 3),
    password_hash TEXT NOT NULL CHECK (length(password_hash) = 60),
    id_rol INTEGER NOT NULL,
    estado INTEGER NOT NULL DEFAULT 1 CHECK (estado IN (0, 1)),
    FOREIGN KEY (id_rol) REFERENCES Rol (id_rol) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 3. TABLA: Categoria
-- Clasificación de productos terminados para catálogo y POS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_categoria TEXT NOT NULL UNIQUE CHECK (length(trim(nombre_categoria)) > 0),
    descripcion TEXT
);

-- ------------------------------------------------------------------------------
-- 4. TABLA: Producto
-- Catálogo de productos para venta en mostrador
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Producto (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    precio_venta REAL NOT NULL CHECK (precio_venta >= 0.0),
    id_categoria INTEGER NOT NULL,
    estado INTEGER NOT NULL DEFAULT 1 CHECK (estado IN (0, 1)),
    FOREIGN KEY (id_categoria) REFERENCES Categoria (id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 5. TABLA: Insumo
-- Materias primas y suministros con control de stock y umbral de alerta
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Insumo (
    id_insumo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    unidad_medida TEXT NOT NULL CHECK (length(trim(unidad_medida)) > 0),
    stock_actual REAL NOT NULL DEFAULT 0.0 CHECK (stock_actual >= 0.0),
    stock_minimo REAL NOT NULL DEFAULT 0.0 CHECK (stock_minimo >= 0.0)
);

-- ------------------------------------------------------------------------------
-- 6. TABLA: Caja
-- Turnos de caja, fondo de apertura, cierre conciliado y arqueo
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Caja (
    id_caja INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    fecha_apertura TEXT NOT NULL,
    monto_inicial REAL NOT NULL CHECK (monto_inicial >= 0.0),
    fecha_cierre TEXT,
    monto_final_real REAL,
    diferencia REAL,
    estado TEXT NOT NULL DEFAULT 'ABIERTA' CHECK (estado IN ('ABIERTA', 'CERRADA')),
    FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 7. TABLA: Venta
-- Registro maestro de transacciones comerciales emitidas en caja
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Venta (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caja INTEGER NOT NULL,
    fecha_hora TEXT NOT NULL,
    total REAL NOT NULL CHECK (total >= 0.0),
    metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'OTRO')),
    dinero_recibido REAL NOT NULL DEFAULT 0.0 CHECK (dinero_recibido >= 0.0),
    cambio REAL NOT NULL DEFAULT 0.0 CHECK (cambio >= 0.0),
    FOREIGN KEY (id_caja) REFERENCES Caja (id_caja) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 8. TABLA: DetalleVenta
-- Partidas individuales de cada venta (relación 1:N con Venta y Producto)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DetalleVenta (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0.0),
    subtotal REAL NOT NULL CHECK (subtotal >= 0.0),
    FOREIGN KEY (id_venta) REFERENCES Venta (id_venta) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto (id_producto) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 9. TABLA: Gasto
-- Egresos operativos menores desembolsados durante el turno de caja
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Gasto (
    id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caja INTEGER NOT NULL,
    fecha_hora TEXT NOT NULL,
    monto REAL NOT NULL CHECK (monto > 0.0),
    descripcion TEXT NOT NULL CHECK (length(trim(descripcion)) > 0),
    id_usuario INTEGER NOT NULL,
    FOREIGN KEY (id_caja) REFERENCES Caja (id_caja) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 10. TABLA: Merma
-- Pérdidas o descartes justificados de insumos e inventario
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Merma (
    id_merma INTEGER PRIMARY KEY AUTOINCREMENT,
    id_insumo INTEGER NOT NULL,
    cantidad REAL NOT NULL CHECK (cantidad > 0.0),
    motivo TEXT NOT NULL CHECK (length(trim(motivo)) > 0),
    fecha_hora TEXT NOT NULL,
    id_usuario INTEGER NOT NULL,
    FOREIGN KEY (id_insumo) REFERENCES Insumo (id_insumo) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ------------------------------------------------------------------------------
-- 11. TABLA: AuditoriaLog
-- Bitácora cronológica inalterable para trazabilidad de eventos sensibles
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS AuditoriaLog (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER,
    accion TEXT NOT NULL CHECK (length(trim(accion)) > 0),
    modulo TEXT NOT NULL CHECK (length(trim(modulo)) > 0),
    fecha_hora TEXT NOT NULL,
    detalles TEXT,
    FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ==============================================================================
-- ÍNDICES ESTRATÉGICOS PARA CONSULTAS FRECUENTES Y RENDIMIENTO
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_usuario_username ON Usuario (username);
CREATE INDEX IF NOT EXISTS idx_usuario_rol ON Usuario (id_rol);
CREATE INDEX IF NOT EXISTS idx_producto_codigo ON Producto (codigo);
CREATE INDEX IF NOT EXISTS idx_producto_categoria ON Producto (id_categoria);
CREATE INDEX IF NOT EXISTS idx_caja_usuario_estado ON Caja (id_usuario, estado);
CREATE INDEX IF NOT EXISTS idx_venta_caja ON Venta (id_caja);
CREATE INDEX IF NOT EXISTS idx_venta_fecha_hora ON Venta (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_venta ON DetalleVenta (id_venta);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_producto ON DetalleVenta (id_producto);
CREATE INDEX IF NOT EXISTS idx_gasto_caja ON Gasto (id_caja);
CREATE INDEX IF NOT EXISTS idx_merma_insumo ON Merma (id_insumo);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha_hora ON AuditoriaLog (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON AuditoriaLog (id_usuario);

-- ==============================================================================
-- DATOS SEMILLA (SEED DATA)
-- ==============================================================================

-- 1. Roles del Sistema
INSERT OR IGNORE INTO Rol (id_rol, nombre_rol) VALUES
    (1, 'Administrador'),
    (2, 'Empleado');

-- 2. Categorías Base Iniciales
INSERT OR IGNORE INTO Categoria (id_categoria, nombre_categoria, descripcion) VALUES
    (1, 'Helados Tradicionales', 'Paletas, barquillos y conos de sabores artesanales'),
    (2, 'Bebidas y Malteadas', 'Bebidas frías, aguas minerales y malteadas'),
    (3, 'Toppings y Adicionales', 'Coberturas de chocolate, dulces y salsas');

-- 3. Usuario Administrador por Defecto
-- Credenciales: username = admin, password = admin123
-- bcrypt('admin123') = $2b$12$PmIxg7ONN2NO7XExZ9hBAODxQxq25YxDrbayYPDmfTgFxYFhMmSPa
INSERT OR IGNORE INTO Usuario (id_usuario, nombre, username, password_hash, id_rol, estado) VALUES
    (1, 'Administrador del Sistema', 'admin', '$2b$12$PmIxg7ONN2NO7XExZ9hBAODxQxq25YxDrbayYPDmfTgFxYFhMmSPa', 1, 1);
