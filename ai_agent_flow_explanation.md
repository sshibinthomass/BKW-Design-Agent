# AI Agent Flow Explanation

## Overview

The AI agent system is a sophisticated beam design assistant that guides users through a structured conversation flow to design, analyze, and optimize structural beams. It uses a state machine approach with strict linear progression through different phases.

## Core Components

### 1. **LLMOrchestrator** (Main Controller)

- **File**: `llm_orchestrator.py`
- **Purpose**: Central coordinator that manages the entire conversation flow
- **Key Features**:
  - Manages conversation states per session
  - Routes user input to appropriate phase handlers
  - Handles error recovery and session resets
  - Coordinates between all other components

### 2. **ConversationState** (State Management)

- **File**: `conversation_state.py`
- **Purpose**: Tracks conversation progress and beam specifications
- **Key Features**:
  - Maintains beam specifications (material, length, load, dimensions)
  - Tracks conversation phase progression
  - Enforces strict linear phase transitions
  - Manages missing field tracking

### 3. **IntentDetector** (User Intent Recognition)

- **File**: `intent_detector.py`
- **Purpose**: Uses LLM to detect user intentions
- **Key Features**:
  - Detects reset/restart requests
  - Identifies history comparison requests
  - Recognizes optimization requests
  - Supports multiple languages (English/German)

### 4. **PhaseHandlers** (Phase-Specific Logic)

- **File**: `phase_handlers.py`
- **Purpose**: Handles specific conversation phases
- **Key Features**:
  - Information gathering
  - Beam analysis
  - Historical comparison
  - Optimization execution

### 5. **BeamProcessor** (Data Extraction)

- **File**: `beam_processor.py`
- **Purpose**: Extracts beam specifications from user input
- **Key Features**:
  - LLM-based information extraction
  - JSON file processing
  - Unit conversion (mm, N, etc.)
  - Multi-language support

### 6. **HistoricalAnalyzer** (Data Comparison)

- **File**: `historical_analyzer.py`
- **Purpose**: Compares current design with historical data
- **Key Features**:
  - CSV data loading and analysis
  - Best alternative finding
  - Efficiency calculations
  - Volume savings analysis

### 7. **VisualizationHandler** (Visual Output)

- **File**: `visualization_handler.py`
- **Purpose**: Generates beam visualizations
- **Key Features**:
  - Plotly-based visualizations
  - Custom title generation
  - JSON output format

## Conversation Flow

### Phase 1: GATHERING_INFO

```
User Input → Intent Detection → Information Extraction → Missing Fields Check
```

- **Purpose**: Collect all required beam specifications
- **Required Fields**: material, length_mm, load_n, width_mm, height_mm
- **Actions**:
  - Extract information from user message and/or JSON files
  - Ask for missing parameters
  - Validate and convert units
- **Transition**: → ANALYZING (when all fields complete)

### Phase 2: ANALYZING

```
Complete Specs → Beam Analysis → Status Check → History Question
```

- **Purpose**: Analyze current beam design
- **Actions**:
  - Run structural analysis (PASS/FAIL status)
  - Generate visualization
  - Present analysis results
  - Ask if user wants historical comparison
- **Transition**: → HISTORY_RESULTS (if history requested)

### Phase 3: HISTORY_RESULTS

```
Historical Data → Best Alternative → Comparison → Optimization Question
```

- **Purpose**: Show historical alternatives and efficiency comparisons
- **Actions**:
  - Find best historical design for same material/length
  - Calculate volume savings potential
  - Present comparison with current design
  - Ask if user wants optimization
- **Transition**: → OPTIMIZING (if optimization requested)

### Phase 4: OPTIMIZING

```
Optimization Request → ML Model → Results → Final Recommendation
```

- **Purpose**: Optimize beam design for efficiency
- **Actions**:
  - Run optimization algorithm
  - Generate optimized dimensions
  - Calculate volume savings
  - Present before/after comparison
- **Transition**: → COMPLETED

### Phase 5: COMPLETED

```
Optimization Complete → Restart Option
```

- **Purpose**: Session completion with restart option
- **Actions**:
  - Present final results
  - Offer to start new beam design
- **Transition**: → GATHERING (for new beam)

## Key Features

### 1. **Strict Linear Progression**

- No jumping between phases
- Each phase has specific entry/exit conditions
- Clear state transitions

### 2. **Multi-Language Support**

- English and German support
- Automatic language detection
- Consistent responses in user's language

### 3. **Error Recovery**

- Automatic session reset on errors
- Fallback mechanisms for LLM failures
- Graceful degradation

### 4. **Intent Detection**

- LLM-based intent recognition
- Pattern matching fallbacks
- Context-aware decision making

### 5. **Data Integration**

- JSON file upload support
- Historical data comparison
- Real-time analysis integration

## State Machine Diagram

```
START
  ↓
GATHERING_INFO ←─────────────────┐
  ↓ (complete specs)              │
ANALYZING                         │
  ↓ (history requested)            │
HISTORY_RESULTS                   │
  ↓ (optimization requested)       │
OPTIMIZING                        │
  ↓                               │
COMPLETED                         │
  ↓ (new beam)                    │
  └───────────────────────────────┘
```

## Error Handling

### 1. **LLM Failures**

- Fallback to pattern matching
- Graceful error messages
- Session reset on critical failures

### 2. **Data Processing Errors**

- JSON parsing fallbacks
- Unit conversion error handling
- Missing data validation

### 3. **System Errors**

- Automatic session cleanup
- Error logging
- User-friendly error messages

## Integration Points

### 1. **ML Models**

- Structural analysis models
- Optimization algorithms
- Status prediction models

### 2. **External Data**

- Historical CSV data
- JSON file uploads
- Real-time calculations

### 3. **Visualization**

- Plotly integration
- Custom beam visualizations
- Interactive charts

## Session Management

### 1. **State Persistence**

- Per-session conversation states
- Beam specification tracking
- Phase progression history

### 2. **Reset Capabilities**

- Complete session reset
- Phase-specific resets
- Error recovery resets

### 3. **Multi-User Support**

- Session isolation
- Concurrent user handling
- State cleanup

This AI agent system provides a comprehensive, user-friendly interface for structural beam design with intelligent conversation flow, robust error handling, and advanced optimization capabilities.
