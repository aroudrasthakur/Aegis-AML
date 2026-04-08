# SAR Download Dialog Component

## Overview

Custom confirmation dialog that appears when a Suspicious Activity Report (SAR) PDF is successfully generated. Matches the app's dark, terminal-inspired theme with green accent colors.

## Component: `SarDownloadDialog`

### Location

`frontend/src/components/SarDownloadDialog.tsx`

### Features

- **Theme-matched design**: Uses the app's color palette (dark backgrounds, green accents)
- **Success indicator**: Green checkmark icon and success message
- **SAR ID display**: Shows the generated SAR ID in monospace font
- **Security notice**: Reminds users about compliance and security policies
- **Loading states**: Shows spinner during download
- **Accessible**: Proper ARIA labels and keyboard navigation

### Props

```typescript
interface Props {
  open: boolean; // Controls dialog visibility
  onClose: () => void; // Called when user closes dialog
  onDownload: () => void; // Called when user clicks download
  sarId: string; // The generated SAR ID to display
  isDownloading?: boolean; // Shows loading state on download button
}
```

### Usage Example

```tsx
import SarDownloadDialog from "@/components/SarDownloadDialog";

function MyComponent() {
  const [showDialog, setShowDialog] = useState(false);
  const [sarId, setSarId] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadSar(sarId);
    } finally {
      setDownloading(false);
      setShowDialog(false);
    }
  };

  return (
    <SarDownloadDialog
      open={showDialog}
      onClose={() => setShowDialog(false)}
      onDownload={handleDownload}
      sarId={sarId}
      isDownloading={downloading}
    />
  );
}
```

## Integration in ReportsPage

### Flow

1. User clicks "Generate SAR PDF" button
2. Toast notification shows "Generating SAR..."
3. API call to generate SAR PDF
4. On success:
   - Toast notification shows "SAR Generated"
   - Custom dialog appears with SAR ID and download button
5. User can:
   - Download immediately via dialog
   - Close dialog and download later via "Download SAR PDF" button

### Key Changes

- Added `showSarDialog` state to control dialog visibility
- Modified `handleGenerateSar` to show dialog instead of browser confirm
- Updated "Download SAR PDF" button to reopen dialog
- Dialog automatically closes after successful download

## Design Tokens Used

### Colors

- Background: `#0d1117` (surface)
- Border: `var(--color-aegis-border)` (rgba(255, 255, 255, 0.08))
- Success: `#34d399` (aegis-green)
- Text primary: `#e6edf3`
- Text muted: `#9aa7b8`, `#6b7c90`

### Typography

- Display font: `font-display` (Syne)
- Data font: `font-data` (DM Mono)
- Mono font: `font-mono` (DM Mono)

### Components

- Rounded corners: `rounded-xl`, `rounded-lg`
- Backdrop blur: `backdrop-blur-[2px]`
- Transitions: `transition-colors`
- Icons: Lucide React (CheckCircle2, FileWarning, Download, X, Loader2)

## Accessibility

- Proper ARIA labels (`aria-modal`, `aria-labelledby`, `aria-label`)
- Keyboard navigation support
- Focus management
- Screen reader friendly
- Loading states announced

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires CSS Grid and Flexbox support
- Backdrop blur may degrade gracefully on older browsers
