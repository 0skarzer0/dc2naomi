Hola de nuevo: ha llegado a nuestras manos la **Rev 2.9-b** (GDI para GDEMU, la del coche ligero de carrera `COCHEnnL.DAT`) y nos interesa mucho para la versión de NAOMI 2, porque ataca justo lo que medimos como más caro en la placa: el coche del jugador se llevaba 4 ms fijos por cuadro con 10 440 vértices, y el ligero baja a 7 794.

El problema es que nosotros no podemos usar el GDI tal cual: en la NAOMI compilamos desde tus fuentes con nuestro parche (KallistiOS con `NAOMI_HOST`, tope de 30 fps, lecturas del disco troceadas, etc.), y en GitHub el código llega hasta `7dfe8a9`. Sobre esa versión nuestro parche ya entra (21 de 22 trozos; el que falla es la línea de `arranque_hold`), pero los datos de la 2.9-b (etapas, uniones, personajes, tráfico) ya no casan con ese código.

¿Podrías subir la rama `rev-2.9b` (en el informe del GDI sale el commit `5960ccc`) o, si lo prefieres, una etiqueta con esa versión, junto con las herramientas de conversión de los datos de esa revisión? Con eso rebasamos el parche de NAOMI, lo medimos en la placa con el coche L y te pasamos las cifras reales (fps, CPU por cuadro, distancia de dibujo y popping) como hicimos con la `a689a9a`: así tendrías también la medida de "consola real" que dejas pendiente en el informe.

¡Gracias otra vez por el port y por publicarlo!
