# ClaimPilot Pro

**AI-Assisted Medical Coding & Claim Generation Platform**

A professional healthcare application for automating medical coding and insurance claim generation using AI. Built with React, TypeScript, Tailwind CSS, and shadcn/ui.

## 🎯 Features

- **Clinical Note Upload**: Support for PDF, JPG, PNG files or direct text paste
- **AI-Powered Code Suggestions**: Automatic ICD-10 diagnosis and CPT procedure code recommendations
- **Interactive Review**: Edit, add, or remove codes before claim generation
- **Blockchain Verification**: Claims recorded on Polygon testnet for audit trails
- **Professional UI**: Clean, accessible, healthcare-optimized interface
- **Full Type Safety**: Built with TypeScript for robust development

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm installed
- Backend API running (see API Configuration below)

### Installation

```bash
# Clone the repository
git clone <YOUR_GIT_URL>
cd claimpilot-pro

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env and set VITE_API_URL to your backend API

# Start development server
npm run dev
```

The app will be available at `http://localhost:8080`

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui base components
│   ├── AmountEditor.tsx
│   ├── ApprovedTable.tsx
│   ├── EntityChips.tsx
│   ├── FileDrop.tsx
│   ├── Header.tsx
│   ├── PageHeader.tsx
│   ├── PasteText.tsx
│   ├── SignatureBlock.tsx
│   ├── SuggestionCard.tsx
│   ├── SuggestionList.tsx
│   └── TxBadge.tsx
│
├── pages/              # Route pages
│   ├── Upload.tsx      # Step 1: Document/text upload
│   ├── Suggest.tsx     # Step 2: AI code suggestions
│   ├── Review.tsx      # Step 3: Review & sign
│   ├── Claims.tsx      # Claim history
│   └── NotFound.tsx
│
├── store/              # State management
│   └── claimStore.ts   # Zustand store with persistence
│
├── lib/                # Utilities and API
│   ├── api.ts          # Axios API client
│   ├── types.ts        # TypeScript type definitions
│   └── utils.ts        # Utility functions
│
├── App.tsx             # Main app with routing
└── index.css           # Global styles & design system
```

## 🎨 Design System

The app uses a healthcare-optimized design system with:

- **Primary Color**: Medical teal (#0891B2)
- **Typography**: Inter font family, 18px base size
- **Spacing**: Generous padding for readability
- **Animations**: Subtle fades and scales
- **Accessibility**: WCAG AA compliant contrast ratios

All design tokens are defined in `src/index.css` and `tailwind.config.ts`.

## 🔌 API Configuration

The app requires a FastAPI backend with these endpoints:

### POST `/upload`
Upload document or text for entity extraction.

**Request (multipart):**
```typescript
{ file: File }
```
or
```typescript
{ text: string }
```

**Response:**
```typescript
{
  text: string;
  entities: Array<{
    text: string;
    label: string;
    start: number;
    end: number;
  }>;
}
```

### POST `/suggest`
Get AI code suggestions.

**Request:**
```typescript
{
  text: string;
  top_k?: number;
}
```

**Response:**
```typescript
{
  entities: Entity[];
  suggestions: Array<{
    code: string;
    system: "ICD-10" | "CPT";
    description: string;
    score: number;
    reason: string;
  }>;
}
```

### POST `/generate_claim`
Generate final claim with blockchain verification.

**Request:**
```typescript
{
  approved: CodeSuggestion[];
  amount?: number;
  signed_by?: string;
}
```

**Response:**
```typescript
{
  claim_id: string;
  approved: CodeSuggestion[];
  metadata: {
    pdf_url?: string;
    tx_hash?: string;
    explorer?: string;
  };
}
```

## 🛠️ Tech Stack

- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand (with session persistence)
- **Data Fetching**: React Query
- **HTTP Client**: Axios
- **Routing**: React Router
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod

## 🧪 Development

```bash
# Run development server
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📦 Deployment

The app is ready to deploy to:

- **Vercel**: Automatic deployment via Git integration
- **Netlify**: Configure build command `npm run build` and publish directory `dist`
- **Any static host**: Build with `npm run build` and deploy `dist/` folder

### Environment Variables for Production

Set `VITE_API_URL` to your production API endpoint in your hosting platform's environment settings.

## 🔐 Security Notes

- Never commit `.env` files with real API keys
- All sensitive operations happen server-side
- Client validates input but server enforces security
- Claims are recorded on blockchain for immutability

## 🎯 User Flow

1. **Upload** → Drop file or paste clinical note text
2. **Extract** → AI identifies medical entities (diagnoses, procedures)
3. **Suggest** → AI recommends ICD-10 and CPT codes with confidence scores
4. **Select** → User reviews and selects relevant codes
5. **Review** → Edit descriptions, add manual codes, set claim amount
6. **Sign** → User certifies claim accuracy
7. **Generate** → System creates CMS-1500, records on blockchain
8. **Verify** → User gets claim ID and blockchain transaction link

## 📄 License

This project is for demonstration purposes. Adapt licensing as needed for production use.

## 🤝 Contributing

This is a demonstration project. For production deployment, ensure compliance with:
- HIPAA regulations for healthcare data
- Medical coding standards (ICD-10, CPT)
- Insurance industry requirements
- Blockchain compliance in your jurisdiction

---

**Built with ❤️ for healthcare professionals**
