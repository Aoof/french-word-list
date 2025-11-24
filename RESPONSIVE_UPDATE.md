# French Word List - Responsive Design Update

## Summary of Changes

The application has been updated to improve mobile responsiveness and follow best practices by extracting HTML templates from the Python code.

## Changes Made

### 1. Template Extraction
- Created `templates/` directory
- Extracted HTML from inline strings to separate template files:
  - `templates/index.html` - Home page with word statistics and tables
  - `templates/cards.html` - Flashcard learning interface

### 2. Updated Python Code
- Changed from `render_template_string()` to `render_template()` in `viewer.py`
- Updated imports: `from flask import Flask, render_template, jsonify`

### 3. Mobile Responsive Enhancements

#### index.html
- Reduced font sizes on mobile devices (h1: 1.5rem → 1.25rem on small screens)
- Made stats cards stack vertically on mobile with proper spacing
- Optimized table display with smaller fonts and padding on mobile
- Made "Start Learning" button full-width with max-width on mobile
- Added responsive grid system with Bootstrap (col-12 col-md-6)
- Improved touch target sizes for better mobile usability

#### cards.html
- Reduced flashcard height on mobile (400px → 350px → 320px)
- Scaled word display font size appropriately (3rem → 2.5rem → 2rem)
- Made action buttons flexible and responsive with proper spacing
- Optimized for landscape orientation on mobile devices
- Improved touch interactions for card flipping
- Better spacing and padding on smaller screens
- Button group uses flexbox for proper wrapping on narrow screens

### 4. Key Responsive Breakpoints
- **Desktop (>768px)**: Full-size components, larger fonts
- **Tablet (≤768px)**: Medium-sized components, reduced spacing
- **Mobile (≤576px)**: Compact layout, smaller fonts, vertical stacking
- **Landscape Mobile (height ≤600px)**: Reduced vertical spacing for better fit

### 5. Mobile-Specific Features
- Touch-friendly tap targets (minimum 44px)
- Proper viewport meta tag for mobile scaling
- Optimized font sizes for readability on small screens
- Flexible button layouts that adapt to screen width
- Tables with horizontal scrolling when needed
- Card flip animations optimized for touch devices

## Testing
The application is now running at http://127.0.0.1:5000 and should work seamlessly on:
- Desktop browsers
- Tablets
- Mobile phones (portrait and landscape)
- Various screen sizes

## File Structure
```
french-word-list/
├── templates/
│   ├── index.html      # Home page template
│   └── cards.html      # Flashcard template
├── viewer.py           # Flask application (simplified)
└── [other files...]
```

## Next Steps
To test on mobile devices:
1. Connect your phone to the same network as your computer
2. Find your computer's local IP address (e.g., 192.168.1.x)
3. Access http://YOUR_IP:5000 from your phone's browser

Or use browser developer tools to test responsive design:
1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select different device presets to test various screen sizes
