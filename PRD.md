# Voice Journaling Web App - Product Requirements Document

Enable users to privately capture voice journals and receive structured reflection through transcripts, summaries, and emotional insights with minimal friction and high trust.

**Experience Qualities**:
1. **Intimate** - The app should feel like a safe, private space where users can express themselves freely without judgment
2. **Effortless** - Recording and accessing journals should require minimal cognitive load, with the focus on speaking, not navigating
3. **Reflective** - The interface should encourage thoughtful review of past entries while providing gentle insights into emotional patterns

**Complexity Level**: Light Application (multiple features with basic state)
  - This app features voice recording, playback, AI processing, and entry management but maintains a focused, single-purpose nature without complex workflows or multiple interconnected views

## Essential Features

### Voice Recording
- **Functionality**: Capture audio directly in the browser using Web Audio API, with visual feedback during recording
- **Purpose**: Enable frictionless thought capture without requiring external devices or apps
- **Trigger**: User clicks/taps record button on main interface
- **Progression**: Click record → Visual waveform appears → Speak thoughts → Click stop → Audio uploads automatically → Entry appears in list with "processing" state → AI summary appears when ready
- **Success criteria**: Recording starts within 500ms, audio quality is clear enough for transcription, upload completes reliably

### AI-Powered Transcription & Analysis
- **Functionality**: Automatically transcribe audio to text, generate summaries, and detect emotional tone using the Spark LLM API
- **Purpose**: Help users understand patterns in their thoughts and emotions without manual effort
- **Trigger**: Automatically begins after audio upload completes
- **Progression**: Audio uploaded → Transcription begins → Text processed for summary → Emotional tone analyzed → All results saved and displayed
- **Success criteria**: Processing completes within reasonable time, failures don't block UI, results feel accurate and helpful

### Journal Entry Management
- **Functionality**: View chronological list of entries, play back audio, read transcripts, edit summaries, and permanently delete entries
- **Purpose**: Provide full control over personal journal data with easy access to past reflections
- **Trigger**: Entries automatically appear after recording; user can click to expand details
- **Progression**: View list → Click entry → Expanded view shows audio player + transcript + summary + emotion → Can play audio, edit text, or delete entry
- **Success criteria**: All entries visible only to owner, deletions are permanent, playback works reliably

### Privacy & Data Control
- **Functionality**: All entries are private to the user, with explicit controls to regenerate AI analysis or permanently delete data
- **Purpose**: Build trust through transparency and user control over their personal reflections
- **Trigger**: User actions in settings or per-entry controls
- **Progression**: Access settings → View privacy options → Delete account or individual entries → Confirmation → Permanent removal
- **Success criteria**: Zero data leakage between users, deletion is irreversible, AI labeling uses soft suggestive language

## Edge Case Handling
- **Recording failures** - Handle microphone permissions denial with clear instructions, show error if recording fails mid-session
- **Upload interruptions** - Save partial uploads and allow retry, show clear status indicators
- **AI processing failures** - Display entry without AI features, allow manual retry of processing
- **Empty recordings** - Detect silence or very short recordings and prompt user to try again
- **Long recordings** - Show recording duration, optionally limit to reasonable length (e.g., 10 minutes)
- **No microphone** - Detect missing audio input and show helpful error with troubleshooting steps

## Design Direction
The design should evoke a sense of calm introspection and emotional safety, like opening a private journal in a quiet, comfortable space. It should feel modern and approachable, not clinical or overly technical, while conveying trust through subtle sophistication.

## Color Selection
A warm, introspective palette that feels personal and safe, avoiding sterile medical aesthetics while maintaining professional credibility.

- **Primary Color**: Deep Indigo `oklch(0.35 0.12 270)` - Communicates depth, introspection, and trust; used for primary actions and key UI elements
- **Secondary Colors**: 
  - Warm Amber `oklch(0.70 0.15 75)` - Adds warmth and approachability for recording states and active elements
  - Soft Lavender `oklch(0.80 0.08 290)` - Supporting color for subtle backgrounds and secondary information
- **Accent Color**: Vibrant Coral `oklch(0.68 0.18 25)` - Draws attention to recording button and important interactive moments
- **Foreground/Background Pairings**:
  - Primary (Deep Indigo): White text `oklch(0.98 0 0)` - Ratio 8.2:1 ✓
  - Accent (Coral): White text `oklch(0.98 0 0)` - Ratio 4.9:1 ✓
  - Background `oklch(0.97 0.01 280)`: Foreground `oklch(0.20 0.02 270)` - Ratio 13.1:1 ✓
  - Muted `oklch(0.88 0.02 285)`: Muted-foreground `oklch(0.45 0.03 275)` - Ratio 6.8:1 ✓

## Font Selection
Typography should feel personal yet polished, like handwritten notes that have been elegantly typeset—warm but legible, expressive but not distracting.

- **Typographic Hierarchy**:
  - H1 (App Title): Newsreader Semibold/32px/tight leading/-0.02em tracking
  - H2 (Section Headers): Newsreader Medium/24px/tight leading
  - H3 (Entry Titles): Space Grotesk Medium/18px/normal leading
  - Body (Transcripts): Space Grotesk Regular/16px/relaxed leading (1.6)
  - UI Labels: Space Grotesk Medium/14px/normal leading
  - Timestamps: Space Grotesk Regular/13px/normal leading/muted color

## Animations
Animations should feel organic and responsive, mirroring the natural rhythm of breath and speech—subtle pulsing during recording, smooth expansions when revealing content, gentle fades for state changes. No jarring transitions that might disrupt the contemplative mood.

## Component Selection
- **Components**: 
  - Button (shadcn) - Primary actions with custom accent color, recording button gets special coral treatment with pulse animation
  - Card (shadcn) - Journal entries with hover states, expandable for full transcript view
  - ScrollArea (shadcn) - For entry lists and long transcripts
  - Dialog (shadcn) - Confirmation for deletions and settings
  - Badge (shadcn) - Emotion labels with soft colors and rounded appearance
  - Progress (shadcn) - AI processing status indicator
  - Separator (shadcn) - Dividing sections without harsh lines
  - Tooltip (shadcn) - Helpful hints for controls without cluttering UI
- **Customizations**: 
  - Custom audio waveform visualizer during recording using canvas or SVG
  - Custom audio player with scrubbing timeline
  - Animated recording button with ripple/pulse effect
- **States**: 
  - Recording button: rest (coral), hover (brighter coral), active (pulsing animation), disabled (muted)
  - Entry cards: collapsed, expanded, processing, error
  - All buttons show subtle elevation changes on hover
- **Icon Selection**: 
  - Microphone (recording), Stop, Play/Pause (playback), Trash (delete), Sparkles (AI features), Lock (privacy), Download (export)
  - Use Phosphor Icons regular weight throughout
- **Spacing**: 
  - Page padding: p-6 md:p-8
  - Card gap in lists: gap-4
  - Internal card padding: p-4 md:p-6
  - Button spacing: px-6 py-3 for primary, px-4 py-2 for secondary
- **Mobile**: 
  - Single column layout stacks naturally
  - Recording button remains prominently accessible at bottom on mobile (sticky footer)
  - Entry cards full width on mobile, grid on larger screens
  - Transcript text remains readable at base size
  - Touch targets minimum 44px for all interactive elements
