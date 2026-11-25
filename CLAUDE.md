# dc2naomi — instrucciones para Claude

## Qué leer primero
1. **[HANDOFF.md](HANDOFF.md)** (~250 líneas): reglas, recetas vigentes, estado de cada juego y pendientes. Basta para
   casi cualquier tarea.
2. Solo si hace falta el detalle de un juego o de un problema: el archivo de [`docs/historial/`](docs/historial/) que
   indica la tabla del final del HANDOFF (no leer el historial entero).
3. Cómo está hecho por dentro (residente, cabecera, parches): [docs/arquitectura.md](docs/arquitectura.md); la lista
   completa de flags y mapas de mandos, en `resident/resident.h`.
4. Qué hay cargado en cada Raspberry: [docs/pi250-juegos.md](docs/pi250-juegos.md) (estándar, .250) y
   `naomi-wheel-games/docs/pi60-juegos.md` (Crazy Taxi, hoy .251).

## Reglas que no se saltan
- **Los juegos del usuario y su `info.txt` están en `C:\Users\Usuario\Documents\dc2naomi` y no se suben nunca a GitHub**
  (ni se copian al repo, ni se citan sus datos en commits o documentos). Tampoco BIOS, IP.BIN, discos ni desensamblados.
- La contraseña de las Raspberry va en la variable `PIPASS`, nunca en un fichero del repo.
- "Probado" = funciona en la placa real. Flycast es solo el primer paso.
- Al terminar: HANDOFF (+ historial) y README (agradecimientos) al día, commit y push (receta 7 del HANDOFF).

# Equipo de agentes (Claude + Gemini)

Este proyecto puede usar Gemini vía Antigravity CLI (`agy`) como ayudante para ahorrar tokens.
- Activa el modo equipo con `/equipo <tarea>`; las reglas completas están en `.claude/commands/equipo.md`.
- Encargos y respuestas: `.agy-tasks/` (plantilla en `_plantilla.md`). Script: `scripts/agy-task.ps1` (estado del equipo en `.agy-tasks/_estado.md`).
- `agy` debe usar la API key de Google AI Studio (`GEMINI_API_KEY`), nunca el login de la suscripción.
- Los ayudantes solo leen; los cambios en archivos los hace Claude tras revisar.
