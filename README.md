# Mis apps

Apps web personales hechas con Claude, publicadas con GitHub Pages para usarlas en el móvil como apps (Safari → Compartir → Añadir a pantalla de inicio).

| App | Carpeta |
|---|---|
| Caja de Pablo | `caja/` |
| Máster Profesorado 26/27 | `master/` |
| Mi Habituario | `habituario/` |
| La Discoteca (vinilos) | `vinilos/` |
| Coplas de Cádiz | `coplas/` |
| Un ramito de violetas (regalo 9-N para Alejandra) | `violetas/` |

> Los datos de cada app se guardan solo en el dispositivo (localStorage). Nunca se suben al repositorio.

## Coplas de Cádiz

`coplas/catalogo.json` guarda solo datos de catálogo y enlaces a [Acordes Gaditanos](https://acordesgaditanos.com/). No guarda letras ni acordes. La GitHub Action `coplas.yml` lo actualiza cada día.

## Añadir una app nueva

1. Crear una carpeta con un `index.html`, su `icon-180.png` y su `manifest.webmanifest`.
2. Añadir una tarjeta en el `index.html` de la raíz.
3. Subir los cambios: GitHub Pages la publica en un par de minutos.
