-- Asegurar que usamos la base de datos de WordPress creada en phpMyAdmin
USE `wordpress`;

-- Tabla unificada para todo el catálogo de la ferretería
CREATE TABLE IF NOT EXISTS `catalogo_productos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sku` VARCHAR(50) NOT NULL UNIQUE,
    `nombre` VARCHAR(150) NOT NULL,
    `marca` VARCHAR(100) NULL,
    `categoria` VARCHAR(100) NOT NULL,       -- Droguería, Herramientas, etc.
    `subcategoria` VARCHAR(100) NULL,        -- Químicos, Adhesivos, etc.
    `precio_sin_iva` DECIMAL(10, 2) NOT NULL,
    `tipo_iva` DECIMAL(4, 2) NOT NULL DEFAULT 21.00,
    `precio_con_iva` DECIMAL(10, 2) GENERATED ALWAYS AS (ROUND(`precio_sin_iva` * (1 + (`tipo_iva` / 100)), 2)) STORED,
    `imagen_url` VARCHAR(255) NULL,
    `descripcion` TEXT NULL,
    `disponible` TINYINT(1) NOT NULL DEFAULT 1,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;