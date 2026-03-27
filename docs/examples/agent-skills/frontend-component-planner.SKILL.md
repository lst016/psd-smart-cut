---
name: frontend-component-planner
description: Plan frontend-facing UI components, reusable states, and shared art resources from screenshot-first page understanding. Use when a subagent must decide how to split a design into frontend components, state assets, text specs, and reusable resources instead of exporting raw PSD groups or repeated layer instances.
---

# Frontend Component Planner

Use this skill after page-level understanding already exists.

Start from:
- the full-page screenshot
- the page or module summary
- the region tree

Use PSD structure only to support alignment, not as the main source of truth.

## Mandatory Workflow

1. Identify the frontend module.
2. Identify the reusable components inside that module.
3. Identify component states.
4. Separate shared resources from component instances.
5. Decide which text stays editable.
6. Produce a component plan before any export plan.
7. Produce implementation decisions before any resource task list.

## Required Output Shape
For each component, produce:

- `component_type`
- `component_role`
- `subparts`
- `states`
- `text_specs`
- `resource_refs`
- `instance_rules`
- `implementation_decision`
- `export_candidates`

## Required Deliverables

Before handing work to export-focused agents, produce:

- `frontend-analysis.md`
- `frontend-analysis.json`
- `implementation-decision.json`

These outputs must explain:

- which parts should remain editable text
- which parts should become shared image resources
- which parts are better implemented with CSS
- which parts should stay vector when possible

## Default Rules

### Buttons
Do not export one image per button instance by default.

Prefer:
- shared `normal`
- shared `selected` or `active`
- optional shared icon resources
- button instances only differ by text and placement

Implementation defaults:
- background skin: usually `image`
- label: usually `text`
- simple radius or shadow: prefer `css` when reproducible

### Switch Rows
Treat a switch row as a component, not a single screenshot crop.

Prefer:
- `label_text`
- `state_text`
- `toggle_control`

Prefer shared resources:
- `switch_track_active`
- `switch_track_inactive`
- `switch_thumb`

Implementation defaults:
- `label_text`: `text`
- `state_text`: `text`
- `switch_track_*`: `image` or `css` depending on fidelity
- `switch_thumb`: prefer `image` if styled, otherwise `css`

Do not export the entire row as a single image unless the row has unique baked artwork.

### Tabs
Treat a tab control as a reusable stateful component.

Prefer:
- shared tab background states
- editable labels
- per-page instances referencing the same tab resources

Implementation defaults:
- tab label: `text`
- tab background state: `image` or `css`

### Modal Or Panel Containers
Recognize structural containers explicitly.

Typical subparts:
- frame
- header
- close icon
- body background

Do not skip container structure just because the PSD does not name it cleanly.

Implementation defaults:
- close icon: `image` or `svg`
- header/body skin: `image`
- plain fill background: prefer `css` when practical

### Instructional Pages
For tutorial-style pages, prefer semantic blocks over anonymous rectangles.

Typical subparts:
- page header
- tab control
- instruction text block
- preview frame top
- preview frame bottom

Do not leave them as `content_block_1` and `content_block_2` if their roles can be inferred.

## Text Rules

Keep text editable by default.

Only bake text into image resources when:
- the typography is heavily stylized
- the text is visually inseparable from artwork
- the font effect is not realistically reproducible by frontend

## Example Judgments

### Floating Chat Entry

Prefer:
- `chat_button_base`
- `unread_badge`
- `unread_count_text`

Implementation defaults:
- `chat_button_base`: `image`
- `unread_badge`: `css`
- `unread_count_text`: `text`

### Chat Panel Bubble

Do not assume the whole bubble should be exported as one image.

Prefer:
- `bubble_background`
- `icon`
- `text_slot`
- `badge_slot`

Implementation defaults:
- `bubble_background`: prefer `css`
- `icon`: `image` or `svg`
- `text_slot`: `text`
- `badge_slot`: prefer `css`

## Anti-Patterns
Do not:
- map one PSD group directly to one final component by default
- export repeated instances as separate resources
- use raw layer names as final component names
- treat screenshot cropping as component modeling
- skip state modeling for switches, tabs, and buttons

## Review Questions
Before handing off, verify:

1. Is the result component-driven rather than layer-driven?
2. Are repeated visuals reused?
3. Are states explicit?
4. Is editable text preserved where possible?
5. Would a frontend engineer understand how to implement the component from this plan?
6. Does the plan explicitly say `image / css / text / svg` for each important part?
