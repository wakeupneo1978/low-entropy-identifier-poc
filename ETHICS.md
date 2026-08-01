# Alcance ético y de publicación

Este proyecto demuestra una propiedad criptográfica conocida utilizando datos
generados específicamente para el laboratorio.

- No se incorporan datos personales, hashes obtenidos de filtraciones ni
  identificadores asociados a personas reales.
- Un valor con formato válido de DNI/NIF no se presenta como emitido ni se
  vincula a un individuo.
- Los dominios `.invalid`, los nombres sintéticos, los teléfonos y los
  sustitutos de IBAN están reservados o son manifiestamente ficticios.
- Las cifras de rendimiento deben publicarse junto con el hardware, software,
  formato canónico y metodología.
- Las afirmaciones de FulcrumSec se distinguen de las observaciones y
  evaluaciones de GRIT. Una recreación saneada de una negociación no equivale a
  una verificación forense independiente de cada detalle.
- La clave HMAC del generador está fijada y publicada únicamente para hacer el
  laboratorio determinista. No representa custodia de claves de producción y
  no debe reutilizarse.
- El análisis regulatorio es informativo y debe someterse a revisión jurídica
  antes de utilizarse como asesoramiento para un caso concreto.

La finalidad es ayudar a responsables, DPO, equipos de seguridad, auditores y
arquitectos de datos a detectar una falsa sensación de protección y a elegir
controles adecuados.

## English summary

This project demonstrates a known cryptographic property using data generated
specifically for the laboratory. It contains no identifiers sourced from real
people, breach material or third-party hashes. A syntactically valid generated
string could accidentally coincide with an issued identifier, but it is never
linked to a real person or real attributes.

Do not adapt the project to personal data or use it to identify individuals.
Performance claims must include exact hardware, software, input format, target
count and methodology. Regulatory analysis is informational and requires
legal review for a specific case.
