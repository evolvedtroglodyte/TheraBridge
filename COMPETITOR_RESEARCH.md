# TherapyBridge - Competitor & Open Source Research

Research conducted: December 2024

---

## Executive Summary

TherapyBridge operates in the **AI-powered therapy documentation** space. The market is projected to grow from $88B (2024) to $132B (2032). Your key differentiators should focus on:
- **Open source** (most competitors are closed)
- **Self-hosted/privacy-first** option
- **Full pipeline** (transcription + diarization + extraction in one tool)

---

## Part 1: Open Source Projects (Best for Inspiration)

### Healthcare-Specific

| Project | Description | Tech Stack | GitHub |
|---------|-------------|------------|--------|
| **AI-Scribe** | Medical scribe for SOAP notes from patient conversations | Whisper + Kobold (local LLM) | [1984Doc/AI-Scribe](https://github.com/1984Doc/AI-Scribe) |
| **MemoMed** | Medical transcription + clinical notes + EHR suggestions | Speech-to-text + AI | [aisemble/MemoMed](https://github.com/aisemble/MemoMed) |
| **ai-transcribe** | Intel's psychotherapy transcription kit | PyTorch + Whisper | [oneapi-src/ai-transcribe](https://github.com/oneapi-src/ai-transcribe) |
| **Notetaker** | SOAP/HL7 notes with speaker diarization | Ollama/OpenAI + WhisperX | [Momentum Notetaker](https://www.themomentum.ai/open-source/notetaker-medical-ai) |

### General Meeting/Transcription (Privacy-Focused)

| Project | Description | Tech Stack | GitHub |
|---------|-------------|------------|--------|
| **Meetily** | 100% local AI meeting assistant | Rust + Whisper + Ollama | [Zackriya-Solutions/meeting-minutes](https://github.com/Zackriya-Solutions/meeting-minutes) |
| **Hyprnote** | Local-first transcription, used by psychiatrists | Whisper (local) | [hyprnote.com](https://hyprnote.com/) |
| **Scriberr** | Self-hosted transcription + diarization | Go + React + WhisperX + pyannote | [rishikanthc/Scriberr](https://github.com/rishikanthc/Scriberr) |
| **noScribe** | Desktop GUI for Whisper + pyannote | Python + GUI | [kaixxx/noScribe](https://github.com/kaixxx/noScribe) |

### Whisper + Pyannote Building Blocks

| Project | Description | Stars | GitHub |
|---------|-------------|-------|--------|
| **WhisperX** | Word-level timestamps + diarization | 13k+ | [m-bain/whisperX](https://github.com/m-bain/whisperX) |
| **ScrAIbe** | Transcription + diarization tool | - | [JSchmie/ScrAIbe](https://github.com/JSchmie/ScrAIbe) |
| **whisper-pyannote-api** | Production-ready containerized microservice | - | [vbrazo/whisper-pyannote-transcription-api](https://github.com/vbrazo/whisper-pyannote-transcription-api) |
| **pyannote-whisper-chatgpt** | Transcribe + summarize with GPT | - | [monodera/pyannote-whisper-chatgpt](https://github.com/monodera/pyannote-whisper-chatgpt) |

---

## Part 2: Commercial Competitors

### Direct Competitors (Mental Health Focus)

| Company | Target | Key Features | Pricing | Notes |
|---------|--------|--------------|---------|-------|
| **[Mentalyc](https://www.mentalyc.com/)** | Private practice | 92% clinical accuracy, EHR integration, HIPAA/PIPEDA | $19-70/mo | Market leader for accuracy |
| **[Upheal](https://www.upheal.io/)** | Private practice | Analytics, technique feedback, AI supervisor | $59/mo | Focus on insights, not just notes |
| **[Eleos Health](https://eleos.health/)** | Health systems | 80% note automation, HITRUST/SOC2 | Enterprise | Not for small practices |
| **[Supanote](https://www.supanote.ai/)** | Private practice | Native EHR autofill, therapy-specific templates | ~$30/mo | New entrant (2024) |
| **[AutoNotes](https://www.autonotes.ai/)** | Private practice | SOAP/BIRP/Treatment plans in 10 seconds | - | Speed-focused |
| **[Blueprint](https://blueprint.ai/)** | Private practice | Measurement-based care + notes | $39/mo | Strong analytics |

### Adjacent Competitors (General Healthcare)

| Company | Focus | Notes |
|---------|-------|-------|
| **[Abridge](https://www.abridge.com/)** | General clinical | Heavy VC funding, hospital focus |
| **[Nabla Copilot](https://www.nabla.com/)** | General medical | $24M Series B (2024) |
| **[Deepgram Nova-3 Medical](https://deepgram.com/solutions/medical-transcription)** | API provider | Speech-to-text API with medical vocabulary |

---

## Part 3: Market Insights

### Pricing Landscape
- **Free tier**: Upheal offers limited free plan
- **Entry**: $19-40/month (Mentalyc Mini, Blueprint Standard)
- **Pro**: $40-70/month (unlimited notes)
- **Enterprise**: Custom pricing (Eleos, Abridge)

### Key Differentiators in Market
1. **Clinical accuracy** (Mentalyc leads at 92%)
2. **EHR integration** (one-click export)
3. **HIPAA compliance** (table stakes)
4. **Session insights** (Upheal's differentiator)
5. **Template variety** (SOAP, DAP, BIRP, GIRP, EMDR, etc.)

### Gaps in Market (Opportunities)
1. **Open source option** - No major open source mental health documentation tool
2. **Self-hosted** - Privacy-conscious therapists want local processing
3. **Affordable** - Many solo practitioners find $40-70/mo expensive
4. **End-to-end** - Most tools are note-only, not full transcription + analysis

---

## Part 4: Technical Inspiration

### From AI-Scribe (Most Similar)
- Uses Whisper + local LLM for SOAP generation
- Includes PHI scrubbing before cloud API calls
- Doctor consent workflow before recording

### From Meetily/Hyprnote
- 100% local processing option
- Desktop application approach
- Meeting-style UI adaptable for sessions

### From Scriberr
- pyannote for local speaker diarization
- Go + React architecture
- Docker-ready deployment

### From whisper-pyannote-api
- Production containerized service
- Webhook support for async processing
- Admin dashboard for monitoring

---

## Part 5: Recommended Actions

### For Competitive Positioning
1. **Lead with privacy** - "Your sessions never leave your computer"
2. **Open source trust** - Full code transparency
3. **Full pipeline** - Transcription + diarization + notes in one tool
4. **Affordable** - Undercut $60/mo competitors

### For Feature Inspiration
1. Study **Upheal's analytics** - session insights, technique tracking
2. Study **Mentalyc's templates** - modality-specific (CBT, DBT, EMDR)
3. Study **AI-Scribe's privacy** - PHI scrubbing workflow
4. Study **Scriberr's architecture** - self-hosted deployment

### For Technical Reference
1. **WhisperX** for word-level timestamps
2. **pyannote-whisper-chatgpt** for the full pipeline pattern
3. **noScribe** for desktop GUI inspiration
4. **whisper-pyannote-api** for production deployment patterns

---

## Sources

### Open Source
- [AI-Scribe GitHub](https://github.com/1984Doc/AI-Scribe)
- [MemoMed GitHub](https://github.com/aisemble/MemoMed)
- [Meetily GitHub](https://github.com/Zackriya-Solutions/meeting-minutes)
- [Scriberr GitHub](https://github.com/rishikanthc/Scriberr)
- [WhisperX GitHub](https://github.com/m-bain/whisperX)
- [noScribe GitHub](https://github.com/kaixxx/noScribe)
- [Hyprnote](https://hyprnote.com/)

### Commercial
- [Mentalyc](https://www.mentalyc.com/)
- [Upheal](https://www.upheal.io/)
- [Eleos Health](https://eleos.health/)
- [Supanote](https://www.supanote.ai/)
- [Abridge](https://www.abridge.com/)

### Market Analysis
- [Best AI Tools for Mental Health Professionals 2025](https://www.supanote.ai/blog/best-ai-tools-for-mental-health-professionals)
- [Mentalyc vs Upheal Comparison](https://www.mentalyc.com/blog/upheal-vs-mentalyc)
- [AI Therapy Notes Guide 2025](https://yung-sidekick.com/blog/the-2025-guide-which-ai-therapy-notes-tools-are-worth-your-time)
