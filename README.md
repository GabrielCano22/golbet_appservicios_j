# golbet_appservicios_j

Aplicación académica ASP.NET Core MVC sobre .NET 8, con arquitectura N-Capas y SQL Server.

## Módulo 6: CRUD de equipos y partidos

- Equipos: listado de activos, creación, edición y desactivación, con escudo opcional.
- Partidos: creación y edición con equipos activos en los selectores; desactivación desde el detalle.
- Formularios parciales compartidos entre crear y editar, validación cliente/servidor en español y tokens antifalsificación en todos los POST.
- Reglas del servicio: local y visitante distintos y fecha futura. Las cuotas deben estar entre 1,01 y 999,99.
- Guardado mediante Post-Redirect-Get y mensajes `TempData` cerrables que se consumen una sola vez.
- Cultura `es-CO`; formularios en hora de Colombia, almacenamiento UTC y conversión al editar. Las cuotas aceptan punto o coma decimal.
- Borrado lógico: los registros permanecen con `IsActive = false` y `ModifiedDate`, y desaparecen de los listados activos.

Las páginas de gestión quedan públicas según el alcance del documento del módulo 6. La autorización por roles corresponde al módulo 7. Desactivar un equipo conserva sus partidos visibles y su historia, conforme al caso descrito en la guía; no se agregó la regla opcional de impedir su desactivación.

## Ejecutar

Requiere SDK .NET 8 y SQL Server local. La conexión se configura en `GolBet.Web/appsettings.json` o mediante `ConnectionStrings__DefaultConnection`. Al iniciar, se aplican las migraciones existentes y los datos iniciales si corresponde; este módulo no cambia el esquema.

```powershell
dotnet restore GolBet.sln
dotnet run --project GolBet.Web --launch-profile http
```

Abrir `http://localhost:5207/Teams` o `http://localhost:5207/Matches`.

## Verificar

```powershell
dotnet build GolBet.sln --no-restore
powershell -ExecutionPolicy Bypass -File scripts/verify-module6.ps1
```

La verificación requiere Python 3 y `sqlcmd`. Crea una base SQL Server temporal con nombre único, inicia otra instancia de la aplicación en un puerto disponible, prueba los formularios por HTTP y consulta la persistencia directamente en SQL Server. Al terminar, detiene esa instancia y elimina únicamente su base temporal. Conserva los logs en la carpeta temporal indicada en la salida y mantiene intacta la base configurada del proyecto.

Comprueba creación, edición y desactivación de ambas entidades; auditoría y conservación de `CreatedDate`; errores de anotaciones y negocio; recarga de selectores; cuotas con ambos separadores; UTC/Colombia; fechas en español; PRG, consumo de `TempData`, rechazo de POST sin token y respuestas 404. Para observar la validación instantánea, abrir Crear, enviar campos vacíos o cuota 1,00 y comprobar en la pestaña Red del navegador que no se envía el POST.
