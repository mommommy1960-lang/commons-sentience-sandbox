# Digital Fit and Curvature Simulation Plan

## Purpose

Use an open-licensed or self-created generic vehicle-body mesh to test routing, zoning, power, thermal, and serviceability assumptions before any physical installation. This simulation is an engineering filter, not proof that the surface works physically.

## Geometry and rights boundary

- Use only geometry whose license permits research and redistribution, or create a simplified parametric body surface.
- Record source, author, license, version, scale, coordinate system, and modifications.
- Do not copy proprietary OEM CAD merely because it is visible online.
- Keep patent-sensitive layer dimensions, routing rules, and supplier-specific details outside the public model.

## Model inputs

For surface mesh vertices \(x_i\), compute principal curvatures \(\kappa_1,\kappa_2\), local curvature radius \(R=1/\max(|\kappa_1|,|\kappa_2|)\), and candidate geodesic routes. Inputs include:

- minimum allowable optical-fiber bend radius \(R_{min}\);
- maximum route strain and attachment shear;
- attenuation per unit length and bend-loss model;
- light-engine output, electrical efficiency, and zone duty cycle;
- ambient and substrate temperature bounds;
- zone-area, service-access, and fault-containment limits;
- mass and power per unit area.

A route fails digitally wherever \(R<R_{min}\), predicted strain exceeds its limit, a service termination is inaccessible, or the thermal/power budget exceeds its bound.

## Computed outputs

1. curvature and exclusion map;
2. candidate low-strain fiber routes;
3. zone boundaries and service-edge locations;
4. optical path length and predicted attenuation;
5. predicted irradiance/uniformity map with uncertainty;
6. power, heat, and mass budget by zone;
7. single-zone fault and cutoff behavior;
8. tolerance/Monte-Carlo sensitivity report.

## Falsification checks

- At least one deliberately impossible bend case must be rejected.
- Mesh refinement must not materially change route feasibility.
- Results must be compared with a flat analytical case.
- Uncertain coefficients must be swept, not silently fixed.
- No parameter may be tuned against physical results and then presented as a prediction without disclosure.

## Connection to the physical gate

The digital result may select the most informative 600 mm × 600 mm coupon layout. It cannot validate adhesion, weathering, abrasion, impact, optical uniformity, bend fatigue, heat rejection, electromagnetic compatibility, or road legality. Those claims remain open until measured.
