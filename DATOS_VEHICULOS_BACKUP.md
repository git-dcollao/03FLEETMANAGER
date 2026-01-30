# Datos de Vehículos - Backup Extraído

## Información de IDs

### id_dtv: 9
- **Nombre**: 3/4
- **Tipo Vehículo**: 5 (Camión)

### id_flota: 7
- **Nombre**: Basureros
- **Departamento**: DAF (id_dpto_empresa=7)

---

## Vehículos a Cargar

| # | Patente | GPS | Estado | Tipo Detalle | Flota | Restricción |
|---|---------|-----|--------|--------------|-------|-------------|
| 1 | YL 3334 | 864035050615344 | Activo | 3/4 (id:9) | Basureros (id:7) | Sin restricción |
| 2 | ZD 7233 | 860856040481560 | Activo | 3/4 (id:9) | Basureros (id:7) | Sin restricción |
| 3 | JPJB 38 | 864035051052281 | Activo | 3/4 (id:9) | Basureros (id:7) | Sin restricción |

---

## Estructura de Datos en Base de Datos

### detalle_tv (Detalles de Tipo Vehículo)
```
id_dtv=9  -> nombre_dtv='3/4'       -> id_tv=5
id_dtv=10 -> nombre_dtv='prueba'    -> id_tv=7
id_dtv=11 -> nombre_dtv='Mazda'     -> id_tv=6
```

### flota (Flotas)
```
id_flota=0 -> nombre_flota='X'          -> id_dpto_empresa=0
id_flota=6 -> nombre_flota='Basureros'  -> id_dpto_empresa=0
id_flota=7 -> nombre_flota='Basureros'  -> id_dpto_empresa=7  ← ESTA ES LA FLOTA
id_flota=8 -> nombre_flota='Basureros'  -> id_dpto_empresa=8
```

### dpto_empresa (Departamentos)
```
id_dpto_empresa=0 -> nombre_dpto_empresa='X'      -> id_empresa=0
id_dpto_empresa=7 -> nombre_dpto_empresa='DAF'    -> id_empresa=4
id_dpto_empresa=8 -> nombre_dpto_empresa='DAO'    -> id_empresa=5
id_dpto_empresa=9 -> nombre_dpto_empresa='Ejemplo' -> id_empresa=4
```

### empresa (Empresas)
```
id_empresa=0 -> nombre_empresa='X'
id_empresa=4 -> nombre_empresa='MAHO'
id_empresa=5 -> nombre_empresa='Municipalidad Iquique'
```

---

## Resumen

- **id_dtv=9**: Corresponde a un detalle de tipo vehículo llamado **"3/4"** que pertenece al tipo de vehículo 5
- **id_flota=7**: Corresponde a una flota llamada **"Basureros"** que pertenece al departamento **DAF**

Todos los 3 vehículos del backup usan los mismos valores:
- **Detalle Tipo**: 3/4 (id_dtv=9)
- **Flota**: Basureros (id_flota=7)
- **Estado**: Activo
- **Restricción**: Sin restricción (1)
