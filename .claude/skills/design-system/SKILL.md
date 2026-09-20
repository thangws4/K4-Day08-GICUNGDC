---
name: design-system-new-chat
description: Creates implementation-ready design-system guidance with tokens, component behavior, and accessibility standards. Use when creating or updating UI rules, component specifications, or design-system documentation.
---

<!-- TYPEUI_SH_MANAGED_START -->

# New chat

## Mission
Deliver implementation-ready design-system guidance for New chat that can be applied consistently across marketing site interfaces.

## Brand
- Product/brand: New chat
- URL: https://claude.ai/new
- Audience: buyers, teams, and decision-makers
- Product surface: marketing site

## Style Foundations
- Visual style: structured, accessible, implementation-first
- Main font style: `font.family.primary=anthropic-sans`, `font.family.stack=anthropic-sans, system-ui, Segoe UI, Roboto, Helvetica, Arial, PingFang SC, PingFang TC, Hiragino Sans, Apple SD Gothic Neo, Kohinoor Devanagari, Kohinoor Bangla, Kohinoor Telugu, Tamil Sangam MN, Kohinoor Gujarati, Malayalam Sangam MN, Nirmala UI, Noto Sans Devanagari UI, Noto Sans Devanagari, Noto Sans Bengali UI, Noto Sans Bengali, Noto Sans Telugu UI, Noto Sans Telugu, Noto Sans Tamil UI, Noto Sans Tamil, Noto Sans Gujarati UI, Noto Sans Gujarati, Noto Sans Kannada UI, Noto Sans Kannada, Noto Sans Malayalam UI, Noto Sans Malayalam, Thonburi, Leelawadee UI, Noto Sans Thai UI, Noto Sans Thai, Kefa, Ebrima, Noto Sans Ethiopic, Abyssinica SIL, sans-serif, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, PingFang SC, PingFang TC, Hiragino Sans, Apple SD Gothic Neo, sans-serif`, `font.size.base=14px`, `font.weight.base=400`, `font.lineHeight.base=20px`
- Typography scale: `font.size.xs=13px`, `font.size.sm=14px`, `font.size.md=16px`
- Color palette: `color.text.primary=#0b0b0b`, `color.text.secondary=#52514e`, `color.text.tertiary=#898781`, `color.surface.base=#000000`, `color.surface.muted=#ffffff`, `color.surface.raised=#fcfcfb`, `color.surface.strong=color(srgb 0.982353 0.982353 0.976471)`, `color.border.default=color(srgb 0.0431373 0.0431373 0.0431373 / 0.1)`, `color.focus.ring=#256abf`
- Spacing scale: `space.1=0.5px`, `space.2=2px`, `space.3=4px`, `space.4=8px`, `space.5=10px`, `space.6=12px`
- Radius/shadow/motion tokens: `radius.xs=5px`, `radius.sm=6px`, `radius.md=7px`, `radius.lg=8px`, `radius.xl=14px` | `shadow.1=rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, color(srgb 0.0431373 0.0431373 0.0431373 / 0.1) 0px 0px 0px 1px inset, rgba(0, 0, 0, 0.05) 0px 1px 2px 0px`, `shadow.2=rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, color(srgb 0.0431373 0.0431373 0.0431373 / 0.1) 0px 0px 0px 0px inset, color(srgb 0.0431373 0.0431373 0.0431373 / 0.1) 0px 0px 0px 1px` | `motion.duration.instant=60ms`, `motion.duration.fast=450ms`

## Accessibility
- Target: WCAG 2.2 AA
- Keyboard-first interactions required.
- Focus-visible rules required.
- Contrast constraints required.

## Writing Tone
concise, confident, implementation-focused

## Rules: Do
- Use semantic tokens, not raw hex values in component guidance.
- Every component must define required states: default, hover, focus-visible, active, disabled, loading, error.
- Responsive behavior and edge-case handling should be specified for every component family.
- Accessibility acceptance criteria must be testable in implementation.

## Rules: Don't
- Do not allow low-contrast text or hidden focus indicators.
- Do not introduce one-off spacing or typography exceptions.
- Do not use ambiguous labels or non-descriptive actions.

## Guideline Authoring Workflow
1. Restate design intent in one sentence.
2. Define foundations and tokens.
3. Define component anatomy, variants, and interactions.
4. Add accessibility acceptance criteria.
5. Add anti-patterns and migration notes.
6. End with QA checklist.

## Required Output Structure
- Context and goals
- Design tokens and foundations
- Component-level rules (anatomy, variants, states, responsive behavior)
- Accessibility requirements and testable acceptance criteria
- Content and tone standards with examples
- Anti-patterns and prohibited implementations
- QA checklist

## Component Rule Expectations
- Include keyboard, pointer, and touch behavior.
- Include spacing and typography token requirements.
- Include long-content, overflow, and empty-state handling.

## Quality Gates
- Every non-negotiable rule must use "must".
- Every recommendation should use "should".
- Every accessibility rule must be testable in implementation.
- Prefer system consistency over local visual exceptions.

<!-- TYPEUI_SH_MANAGED_END -->
