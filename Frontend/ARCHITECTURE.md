# CryptoSense Frontend Architecture

This project is a mobile-first React application built with Vite, TailwindCSS, and Recharts. It mirrors the design patterns from the original HTML files while adding interactivity and modern component structure.

## Component Architecture

The application follows an Atomic Design-inspired structure:

### 1. UI Components (`src/components/ui/`)
Reusable, low-level components that form the building blocks of the UI.
- **Button**: Handles primary, secondary, and outline styles with gradient support.
- **Card**: Versatile container with dark surface styling and backdrop blur.
- **SignalCard**: Specialized card for displaying market signals with confidence ratings.
- **ConfidenceRing**: Visual indicator of signal confidence using SVG.
- **Header**: Responsive navigation with sticky behavior and backdrop blur.
- **PortfolioTable**: Styled data table for portfolio items.
- **PriceChart**: Data visualization using Recharts.

### 2. Pages (`src/pages/`)
Higher-level components that represent full screens.
- **LandingPage**: Hero section, features, and call to action.
- **Dashboard**: The main terminal view with signals and performance tracking.

### 3. Lib & Utils (`src/lib/`)
Helper functions and shared logic.
- **utils.ts**: Contains `cn` for merging Tailwind classes safely.

## Design System

### Colors
- **Background**: `#0A0F1E` (Dark Navy)
- **Primary**: `#10b981` (Emerald Green)
- **Surface**: `#111827` (Dark Slate)
- **Accents**: Tertiary (Amber), Error (Red/Coral)

### Typography
- **Headlines**: `Space Grotesk` (700 weight for headers)
- **Body**: `Space Grotesk` (400 weight)
- **Data**: `IBM Plex Mono` (Used for prices and ticker symbols)

### Responsiveness
- **Mobile-First**: All layouts are designed for small screens first.
- **Breakpoints**: 
  - `md`: Desktop navigation and grid layouts (2-3 columns).
  - `lg`: Maximum width for content centering.

## Getting Started

1. `npm install`
2. `npm run dev` - Start development server
3. `npm run test` - Run unit tests
4. `npm run build` - Create production build

## Interactivity Features
- Gradient backgrounds and mesh grids for visual depth.
- Animated confidence rings and system status indicators.
- Hover states for all interactive elements.
- Responsive mobile menu support.
