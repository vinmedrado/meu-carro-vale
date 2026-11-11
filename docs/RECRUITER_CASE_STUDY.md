# Meu Carro Vale — Technical case study

*English / Español · Data engineering, vehicle valuation and full-stack delivery*

## The problem

A single reference price rarely reflects a specific vehicle's mileage, region and market demand. A valuation product needs clear data provenance and a reliable fallback when external data is incomplete.

## System design

\`\`\`text
Vehicle selection → React/TypeScript interface → FastAPI valuation service
                                                    ↓
                                 local FIPE references / available comparables
                                                    ↓
                                      pricing insights → report / PDF
mcv-data-engine/ → collection and normalization → PostgreSQL / data services
\`\`\`

The architecture separates \`frontend/\`, \`backend/\` and \`mcv-data-engine/\`. The valuation result communicates reference prices, confidence and alternative price ranges. A public GitHub Pages deployment runs in demonstration mode with illustrative values.

## What this demonstrates

- Full-stack integration across collection, backend rules, frontend and reports.
- Local-first reference data and explicit fallback when external market sources are unavailable.
- Data quality and explainable output, rather than a number without supporting context.
- Automated and practical user-flow validation.

## Quality evidence

The [CI workflow](../.github/workflows/ci.yml) has three jobs: backend tests, data-engine tests and TypeScript/Vite frontend build. The frontend was also exercised in Chrome on desktop and mobile for demo navigation, report and tabs. The PDF/report interaction was manually checked by the project owner; this is different from an automated end-to-end PDF assertion.

**Important limitation:** demo valuations are synthetic/illustrative; they are not current market quotations. CI and smoke tests do not replace an exhaustive security or usability audit.

## Explore

- [Public demo](https://vinmedrado.github.io/meu-carro-vale/)
- [Repository and setup](https://github.com/vinmedrado/meu-carro-vale)
- [CI](https://github.com/vinmedrado/meu-carro-vale/actions/workflows/ci.yml)

---

## Resumen en español

**Problema:** la referencia FIPE, por sí sola, no siempre recoge las características y condiciones del mercado local de un vehículo.

**Solución:** aplicación de valoración con React y FastAPI, un módulo de ingeniería de datos separado, fuentes de referencia FIPE, comparables cuando están disponibles e informes PDF.

**Competencias demostradas:** procesamiento de datos, APIs, TypeScript, arquitectura desacoplada, calidad de datos y pruebas automatizadas.

**Limitación explícita:** la demostración utiliza cifras ilustrativas; no debe interpretarse como una tasación actual del mercado.

[Ver demostración](https://vinmedrado.github.io/meu-carro-vale/) · [Ver código](https://github.com/vinmedrado/meu-carro-vale)
