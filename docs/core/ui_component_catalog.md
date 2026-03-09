# UI Component Catalog

GenesisPrediction v2

Purpose: Define reusable UI components used across the GenesisPrediction
dashboards. This catalog ensures that all UI pages share the same
structure and style.

------------------------------------------------------------------------

# 1. Page Structure Standard

All pages should follow this structure.

Header Global Status Hero Content Cards Timeline / Lists Footer

Layout order:

site-header page container panel hero cards timeline footer

------------------------------------------------------------------------

# 2. Core Layout Components

## Panel

Main page wrapper.

Usage: panel wraps the entire page content.

Characteristics: rounded corners soft border dark gradient background

Example structure:

panel └ hero └ cards └ timeline

------------------------------------------------------------------------

## Card

Reusable container for information blocks.

Used for: status cards metric cards content cards history cards

Visual rules: rounded corners light border soft gradient background

Typical structure:

card └ title └ content

------------------------------------------------------------------------

# 3. Status Components

## status-shell

Global system status area.

Displays: global risk sentiment balance FX regime article count last
update

Structure:

status-shell └ status-grid └ status-item

------------------------------------------------------------------------

## status-item

Individual status display.

Contains: label value sub text

Example:

status-item └ status-label └ status-value └ status-sub

------------------------------------------------------------------------

# 4. Hero Components

## hero

Top information banner.

Used for: page explanation current summary prediction overview

Structure:

hero └ title └ summary └ metadata pills

------------------------------------------------------------------------

# 5. Timeline Components

## timeline-card

Container for time‑based events.

Structure:

timeline-card └ timeline-list └ timeline-row

------------------------------------------------------------------------

## timeline-row

Single event entry.

Contains:

date status badge description metrics

Layout:

timeline-row ├ date ├ badge ├ body └ metrics

------------------------------------------------------------------------

# 6. List Components

## list-stack

Vertical list container.

Used for:

watchpoints review notes alerts

Structure:

list-stack └ list-row

------------------------------------------------------------------------

## list-row

Single list item.

Structure:

list-row ├ badge └ content

------------------------------------------------------------------------

# 7. Sparkline Components

## sparkline

Mini chart for trend visualization.

Used for:

confidence trend probability drift

Structure:

sparkline └ sparkbar

------------------------------------------------------------------------

## sparkbar

Single bar in sparkline chart.

Contains:

date label value label

------------------------------------------------------------------------

# 8. Grid Systems

## hero-grid

Used in hero sections.

Layout:

2 columns desktop 1 column mobile

------------------------------------------------------------------------

## history-grid

Used for dashboard card layout.

Layout:

2 columns desktop 1 column mobile

------------------------------------------------------------------------

## kpi-grid

Metric card layout.

Typical usage:

4 cards in one row

------------------------------------------------------------------------

# 9. Color Semantics

Risk levels:

risk-low risk-guarded risk-elevated risk-high risk-critical

Meaning:

Low risk Guarded risk Elevated tension High instability Critical
situation

------------------------------------------------------------------------

# 10. Design Principles

GenesisPrediction UI should follow:

Clarity over decoration Consistent card structure Predictable layouts
Readable typography Dark dashboard aesthetic

------------------------------------------------------------------------

# 11. Component Reuse Rule

New UI pages must reuse existing components.

Avoid creating new structures when one of these exists:

panel card status-shell hero timeline list-stack sparkline

------------------------------------------------------------------------

# End
