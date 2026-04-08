# SAR Download Dialog - Visual Reference

## Dialog Structure

```
┌─────────────────────────────────────────────────────────┐
│  ┌───┐                                                   │
│  │ ✓ │  SAR Report Ready                          ✕     │  ← Header
│  └───┘                                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ⚠  Suspicious Activity Report Generated         │  │  ← Success Message
│  │     Your SAR PDF has been successfully generated │  │
│  │     and is ready for download.                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  SAR ID                                           │  │  ← SAR ID Card
│  │  f0236c6d-8fea-4844-a873-b26381aef0f2            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  This report contains sensitive information.      │  │  ← Security Notice
│  │  Ensure it is handled in accordance with your    │  │
│  │  organization's compliance and security policies.│  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                    [ Close ]  [↓ Download PDF] │  ← Footer
└─────────────────────────────────────────────────────────┘
```

## Color Scheme

### Background Colors

```
Dialog Background:    #0d1117  ████████
Card Background:      #060810  ████████
Success Background:   #34d399/5 (5% opacity)
```

### Border Colors

```
Default Border:       rgba(255, 255, 255, 0.08)  ────────
Success Border:       #34d399/30 (30% opacity)   ────────
```

### Text Colors

```
Primary Text:         #e6edf3  ████████
Secondary Text:       #9aa7b8  ████████
Muted Text:          #6b7c90  ████████
Success Text:        #34d399  ████████
```

### Accent Colors

```
Success Green:       #34d399  ████████
Button Hover:        #34d399/15 (15% opacity)
```

## Component Breakdown

### Header Section

```tsx
<div className="flex items-center justify-between border-b px-5 py-4">
  <div className="flex items-center gap-2">
    <div className="rounded-lg bg-[#34d399]/10 p-2">
      <CheckCircle2 className="h-5 w-5 text-[#34d399]" />
    </div>
    <h2 className="font-display text-lg font-semibold text-[#e6edf3]">
      SAR Report Ready
    </h2>
  </div>
  <button className="rounded-lg p-1 text-[#9aa7b8] hover:text-[#e6edf3]">
    <X className="h-5 w-5" />
  </button>
</div>
```

### Success Message Card

```tsx
<div className="flex items-start gap-3 rounded-lg border border-[#34d399]/30 bg-[#34d399]/5 px-4 py-3">
  <FileWarning className="mt-0.5 h-5 w-5 shrink-0 text-[#34d399]" />
  <div className="flex-1">
    <p className="font-display text-sm font-medium text-[#e6edf3]">
      Suspicious Activity Report Generated
    </p>
    <p className="mt-1 font-data text-xs text-[#9aa7b8]">
      Your SAR PDF has been successfully generated and is ready for download.
    </p>
  </div>
</div>
```

### SAR ID Card

```tsx
<div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-3">
  <p className="font-data text-[11px] uppercase tracking-wide text-[#6b7c90]">
    SAR ID
  </p>
  <p className="mt-1 font-mono text-sm text-[#e6edf3] break-all">{sarId}</p>
</div>
```

### Security Notice Card

```tsx
<div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-3">
  <p className="font-data text-xs text-[#9aa7b8] leading-relaxed">
    This report contains sensitive information. Ensure it is handled in
    accordance with your organization's compliance and security policies.
  </p>
</div>
```

### Footer Buttons

```tsx
<div className="flex justify-end gap-2 border-t px-5 py-4">
  {/* Close Button */}
  <button className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-2 font-data text-sm text-[#e6edf3] hover:border-[#34d399]/35">
    Close
  </button>

  {/* Download Button */}
  <button className="inline-flex items-center gap-2 rounded-lg border border-[#34d399]/40 bg-[#34d399]/10 px-4 py-2 font-data text-sm font-medium text-[#6ee7b7] hover:bg-[#34d399]/15">
    <Download className="h-4 w-4" />
    Download PDF
  </button>
</div>
```

## States

### Normal State

- All elements visible
- Download button enabled
- Green accent colors

### Downloading State

```tsx
<button disabled className="... disabled:opacity-40">
  <Loader2 className="h-4 w-4 animate-spin" />
  Downloading…
</button>
```

### Hover States

- Close button: text color changes from `#9aa7b8` to `#e6edf3`
- Close button (footer): border changes to `#34d399/35`
- Download button: background changes to `#34d399/15`

## Responsive Behavior

- Max width: `max-w-md` (28rem / 448px)
- Padding: `px-4` on mobile for safe margins
- Text wrapping: SAR ID uses `break-all` for long UUIDs
- Flexible layout: All cards stack vertically

## Animation

- Backdrop: `backdrop-blur-[2px]` for depth
- Transitions: `transition-colors` on interactive elements
- Smooth hover effects

## Accessibility Features

- `role="dialog"` and `aria-modal="true"`
- `aria-labelledby` pointing to title
- `aria-label` on close button
- Keyboard navigation support
- Focus trap within dialog
- ESC key to close (handled by onClick on backdrop)
