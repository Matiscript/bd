# 🛠️ Digitalización y Modernización del Catálogo: Ferretería Puerta Carmona

Repositorio de ingeniería de software y gestión de datos desarrollado para la asignatura **Gestión de Sistemas de Información (GSI)** de la **Escuela Técnica Superior de Ingeniería Informática (Universidad de Sevilla)**.

El propósito de este proyecto es modernizar la infraestructura digital y el catálogo comercial de un negocio tradicional histórico (**Ferretería Puerta Carmona**, fundada en 1936), trasladando sus catálogos impresos a un sistema de gestión de contenidos (CMS) basado en **WordPress** y **WooCommerce** bajo el marco metodológico **Scrum**.

---

## 📌 Contexto y Objetivos del Proyecto

La ferretería disponía de su inventario comercial en múltiples catálogos distribuidos en documentos PDF no estructurados (diseñados para imprenta en cuadrículas de 3 columnas con precios sin IVA)[cite: 6]. 

Este repositorio documenta el flujo completo de ingeniería: **Extracción, Transformación, Carga (ETL), curación de activos multimedia y sincronización con el CMS** para dar cumplimiento a los requisitos modelados en la metodología REM / REMUS:
* **OBJ-01:** Digitalización integral del catálogo histórico para consulta de particulares y profesionales[cite: 7].
* **RI-01 (Ficha técnica de producto):** Almacenamiento normalizado de SKU, marca, taxonomía (categoría y subcategoría), precio con/sin IVA, imagen de alta resolución y disponibilidad.
* **RN-01 (Regla de negocio de precios):** Cálculo y desglose explícito del 21% de IVA aplicable sobre el precio mayorista/catálogo[cite: 6, 7].

---

## 🏗️ Pipeline de Ingeniería y Procesamiento de Datos (ETL)

El procesamiento del inventario desde los documentos originales hasta la base de datos se estructuró en cuatro etapas:
