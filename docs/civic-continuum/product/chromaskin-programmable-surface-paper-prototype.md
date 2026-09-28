# ChromaSkin / ChromaMask Programmable Surface Paper Prototype

## Status

This document is a paper prototype and product-architecture draft. It does not claim that ChromaSkin has been physically built, safety-certified, weather-tested, mass-produced, or validated as a finished product.

The purpose is to make the idea concrete enough for engineering review, market review, materials review, student capstone routing, maker-space discussion, and staged prototyping.

## Plain-English Concept

ChromaSkin is a programmable visual surface platform: a cut-to-size sheet, panel, wrap, or tile that can be applied to objects and then changed digitally.

A simple phrase for reviewers:

> Programmable construction paper for objects, rooms, displays, furniture, and vehicles.

Instead of repainting, replacing, rewrapping, or buying a new object, the user changes the visible surface through an app, controller, or programmed theme.

## Product Names

| Name | Working meaning |
|---|---|
| ChromaSkin | Larger surfaces such as furniture, walls, vehicles, display panels, retail fixtures, and interior design surfaces. |
| ChromaMask | Smaller object skins such as phone cases, remotes, controllers, laptops, desk tiles, nameplates, product shells, and decor pieces. |

These names are working product names only. Trademark review is required before commercial use.

## Core Use Cases

| Use case | Example | Why it matters |
|---|---|---|
| Device personalization | Phone case, laptop skin, remote control, game controller | Small first product; easy to understand; lower material area and lower cost. |
| Room and furniture themes | Desk, shelf, table, wall tile, gaming room, studio, salon | Lets a user change a room's style without replacing furniture. |
| Retail and event displays | Counter sign, kiosk panel, booth wall, menu surface, product display | Business customers already understand digital signage and visual refresh value. |
| Vehicle customization | Door panel, hood section, motorcycle fairing, helmet, show-car panel | Strong brand identity and visual impact; later-stage durability challenge. |
| Education and prototyping | Maker kits, classroom demos, design-school surface experiments | Useful first reviewer lane before full manufacturing. |

## First Sellable Framing

The first version should not be pitched as a whole-room system or whole-vehicle wrap. The first version should be framed as a small programmable surface kit.

A realistic first kit could include:

1. One phone-case-sized sample.
2. One flat desk tile or nameplate sample.
3. One small wall or furniture coupon panel.
4. A controller or app mockup that changes color, image, pattern, brightness, and theme.
5. A test checklist showing what has and has not been validated.

## System Architecture

```mermaid
flowchart TD
    A[User image or theme] --> B[App or controller]
    B --> C[Image and pattern processor]
    C --> D[Surface control electronics]
    D --> E[Programmable surface sheet]
    F[Power source] --> D
```

## Candidate Layer Stack

This is a starting architecture for review, not a final bill of materials.

| Layer | Function | Early review questions |
|---|---|---|
| Clear protective top layer | Scratch, wipe, moisture, and UV protection | Can it survive cleaning, touch, abrasion, and sunlight? |
| Visual/display layer | Produces color, image, pattern, or illuminated effect | Is the right technology LED matrix, flexible e-paper, fiber optic, micro-LED, electrochromic film, or hybrid? |
| Diffusion or optical layer | Spreads or shapes light and hides pixel structure | Does the image look clean at normal viewing distance? |
| Flexible backing layer | Gives structure and bend control | How much bending is allowed before failure? |
| Adhesive or mounting layer | Attaches to object, case, panel, furniture, or vehicle surface | Can it be removed without damage? Does heat weaken it? |
| Power and control connector | Moves power/data into the surface | Can small products use a battery while larger panels use wired power? |

## Technology Options to Compare

| Option | Strength | Concern |
|---|---|---|
| Flexible LED matrix | Bright, colorful, animated | Power draw, heat, thickness, pixel visibility. |
| E-paper / color e-paper | Low power for static images | Refresh speed, color range, flexibility, cost. |
| Fiber-optic illuminated layer | Strong visual identity and decorative effects | Complexity, routing, image resolution limits. |
| Electrochromic film | Thin, low-power tint/color shifts | Limited image detail and color range. |
| Printed interchangeable overlay plus smart backlight | Cheap first prototype path | Not a fully programmable image surface yet. |

## Prototype Ladder

| Stage | Prototype | Purpose | Pass condition |
|---|---|---|---|
| 0 | Paper design and diagrams | Make the concept inspectable | Reviewers understand the system and can critique assumptions. |
| 1 | Non-electronic visual mockup | Show size, layers, mounting, and product feel | People understand the product in hand. |
| 2 | Flat illuminated coupon | Show basic color/pattern change on a small panel | Surface changes reliably under controlled conditions. |
| 3 | Phone-case-sized demo | Prove a small consumer object path | Fits a small object and survives normal handling tests. |
| 4 | Furniture/decor tile | Prove room-decor lane | Multiple panels can coordinate themes. |
| 5 | Vehicle coupon panel | Begin heat, UV, vibration, moisture, and cleaning tests | Survives controlled environmental tests. |

## Evidence Checklist

Before any product claim escalates, the project should document:

- Image/pattern quality.
- Viewing distance and brightness.
- Power draw and battery life.
- Heat under continuous use.
- Scratch resistance.
- Bend radius and flex-cycle limits.
- Adhesive strength and removability.
- Cleaning and moisture tolerance.
- UV/sunlight exposure tolerance.
- Fire/electrical safety review needs.
- Repairability and replacement path.
- Cost per square inch or square foot.
- Privacy/security assumptions if app-controlled.

## Market Hypothesis

ChromaSkin is potentially marketable because it sits at the overlap of several familiar buyer behaviors:

- People personalize phones, cases, laptops, controllers, rooms, and vehicles.
- Businesses already pay for digital signage and changeable displays.
- Creators, streamers, salons, studios, and gaming-room customers value visual identity.
- Retailers and event teams need fast theme changes without rebuilding sets.
- Smart-home buyers already understand app-controlled lighting and decor.

The strongest first customers are likely not full-vehicle buyers. The strongest first customers are likely:

1. Creators and gamers who want customizable room objects.
2. Small businesses that want reusable display panels.
3. Phone/accessory customers who want changeable visuals.
4. Maker/education users who want a programmable surface kit.
5. Design students or capstone teams who can test material approaches.

## Safety and Claim Boundary

ChromaSkin should be presented as a concept-to-prototype product architecture until physical test articles exist.

Do not claim:

- It is already a working commercial product.
- It is automotive-safe.
- It survives weather, car washes, heat, impact, or road conditions.
- It can display any image at any size without power, heat, or resolution limits.
- It is patent-protected unless counsel confirms filing status.

Do claim:

- It is a documented programmable-surface concept.
- It has a staged paper-to-prototype path.
- It can be reviewed as materials, controls, product design, and market-positioning work.
- Vehicles are one lane, not the whole invention.

## Best Entrance Points for Reviewers

| Reviewer type | What to ask them |
|---|---|
| Materials science | Which flexible visual surface technology is most realistic for a low-cost first coupon? |
| Electrical engineering | What controller, power, heat, and safety constraints appear first? |
| Product design | Which first form factor is easiest for users to understand and buy? |
| Business/startup advisor | Which customer segment is most reachable with the smallest prototype? |
| Maker-space or capstone team | Can a flat coupon or phone-case-sized demo be built with available components? |
| IP/legal clinic | What prior art and trademark searches should be done before public commercialization? |

## Next GitHub Actions

1. Add a simple diagram image or rendered product mockup.
2. Create a one-page pitch sheet.
3. Create a component comparison table with estimated costs.
4. Create a physical test plan for the Stage 2 flat coupon.
5. Link this paper prototype from the Civic Continuum overview and portfolio index.
