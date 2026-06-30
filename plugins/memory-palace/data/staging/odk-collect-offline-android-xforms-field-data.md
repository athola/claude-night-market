---
title: 'ODK Collect: offline Android XForms field data collection'
source:
  type: web_fetch
  identifier: https://github.com/getodk/collect
author: drain-workflow
date_captured: '2026-06-30'
palace: Tacit Knowledge Capture
district: Research 2026-06-29
maturity: probation
tags:
- mobile-data-collection
- android
- xforms
- offline-first
- form-capture
---

# ODK Collect: offline Android XForms field data collection

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: mobile-data-collection, android, xforms, offline-first, form-capture

## Intake Content

# ODK Collect: offline Android XForms field data collection

ODK Collect is an offline-capable Android app for form-based field data collection using the open XForms standard via JavaRosa. Built for resource-constrained settings; geospatial question types, XLSForm authoring, multi-language. Reference for offline-first mobile capture standardized on open form specs.

## Key points

- Renders ODK XForms (subset of XForms 1.1) via the JavaRosa library
- Offline-first for unreliable connectivity / power-constrained environments
- Kotlin/Java, Gradle, Android API 21+; Robolectric + instrumented tests
- GeoPoint/GeoTrace/GeoShape via optional Google Maps / Mapbox SDKs
- XLSForm conversion, ADB form deploy, Transifex translations

Source: https://github.com/getodk/collect
