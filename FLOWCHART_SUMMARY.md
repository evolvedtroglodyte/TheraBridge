# TherapyBridge Flowchart Documentation

## 📊 Available Flowcharts

### 1. **ULTRA_DETAILED_FLOWCHART.md** (RECOMMENDED)
**Single ultra-granular Mermaid diagram - 400+ nodes**

✅ **Maximum detail** - Every validation, retry, error path
✅ **Copy-paste ready** - One massive flowchart
✅ **Color-coded** - 6 colors by operation type
✅ **Production-ready** - Shows actual implementation

**Best for:**
- Understanding complete algorithm
- Debugging specific issues
- Technical deep-dives
- Presentations with zoom capability

**View at:** https://mermaid.live (paste entire code block)

**Features:**
- 400+ nodes total
- 80+ decision points
- 35+ error handling paths
- 8 retry mechanisms with backoff
- 50+ validation steps
- 25+ database operations
- All file paths included
- API response codes (200, 429, 5xx)
- Confidence thresholds documented

---

### 2. **COMPLETE_PIPELINE_FLOWCHART.md**
**11 separate Mermaid diagrams - Multi-view documentation**

✅ **Comprehensive** - Different diagram types
✅ **Multi-angle** - Sequence, Graph, Gantt, ERD
✅ **Well-organized** - Each phase has dedicated diagram

**Includes:**
1. High-level pipeline (Graph TB)
2. Processing timeline (Gantt)
3. Audio upload flow (Sequence)
4. Transcription pipeline (Sequence)
5. Wave 1 orchestration (Graph TB)
6. Mood analysis logic (Flowchart TD)
7. Wave 2 analysis (Sequence)
8. AI chat context (Sequence)
9. End-to-end data flow (Graph TD)
10. Complete timeline (Gantt)
11. Database schema (ERD)

**Best for:**
- Different perspectives on same system
- Documentation sites
- Progressive learning (phase by phase)
- GitHub/GitLab display

---

### 3. **SINGLE_GIANT_FLOWCHART.md**
**Simplified version - 90+ nodes**

✅ **Less overwhelming** - Key steps only
✅ **Good overview** - Major phases clear
✅ **Database schema** - Included in diagram

**Best for:**
- Quick overview
- Non-technical stakeholders
- Presentations (no zoom needed)
- README documentation

---

## 🚀 Quick Start

**Want maximum detail?**
```bash
# Copy ULTRA_DETAILED_FLOWCHART.md
# Paste into https://mermaid.live
# Zoom out to see full diagram
```

**Want multiple views?**
```bash
# Open COMPLETE_PIPELINE_FLOWCHART.md in GitHub
# All 11 diagrams render automatically
```

**Want quick overview?**
```bash
# Copy SINGLE_GIANT_FLOWCHART.md
# Paste into mermaid.live or GitHub
```

---

## 📈 Comparison

| Feature | ULTRA_DETAILED | COMPLETE_PIPELINE | SINGLE_GIANT |
|---------|----------------|-------------------|--------------|
| **Total Diagrams** | 1 massive | 11 separate | 1 simplified |
| **Nodes** | 400+ | Varies per diagram | 90+ |
| **Detail Level** | Maximum | High | Medium |
| **Error Paths** | 35+ | Some shown | Few shown |
| **Retry Logic** | All 8 mechanisms | Mentioned | Not shown |
| **File Paths** | All included | Key files only | Not shown |
| **Best Viewer** | mermaid.live | GitHub/GitLab | Any |
| **Load Time** | 2-3 seconds | Instant | Instant |

---

## 🎯 Recommendation by Use Case

### For Developers
→ **ULTRA_DETAILED_FLOWCHART.md**
- Shows every validation check
- All retry mechanisms
- Complete error handling
- Actual file paths

### For Documentation
→ **COMPLETE_PIPELINE_FLOWCHART.md**
- Multiple diagram types
- ERD for database
- Gantt for timeline
- Sequence for interactions

### For Presentations
→ **SINGLE_GIANT_FLOWCHART.md**
- Clear overview
- Not overwhelming
- Fits on screen
- Good for slides

### For Debugging
→ **ULTRA_DETAILED_FLOWCHART.md**
- Trace exact error path
- See all retry attempts
- Find specific validation
- Check confidence thresholds

---

## 🔧 Viewing Tips

**mermaid.live (Best for large diagrams):**
1. Go to https://mermaid.live
2. Copy entire ` ```mermaid ... ``` ` block
3. Paste into editor
4. Zoom out (Ctrl/Cmd -)
5. Export as SVG for vector graphics

**GitHub/GitLab:**
- Push .md files
- Diagrams render automatically
- May need horizontal scroll for ULTRA_DETAILED

**VS Code:**
- Install extension: `bierner.markdown-mermaid`
- Open .md file
- Press Cmd+Shift+V (Mac) or Ctrl+Shift+V (Win)

**CLI (Generate images):**
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i ULTRA_DETAILED_FLOWCHART.md -o diagram.png
```

---

## 📊 Statistics

**ULTRA_DETAILED_FLOWCHART.md:**
- Lines: 800+
- Nodes: 400+
- Decision Points: 80+
- Error Paths: 35+
- Colors: 6 types
- File Size: ~65KB

**COMPLETE_PIPELINE_FLOWCHART.md:**
- Lines: 1,716
- Diagrams: 11
- Diagram Types: 5 (Graph, Sequence, Flowchart, Gantt, ERD)
- File Size: ~83KB

**SINGLE_GIANT_FLOWCHART.md:**
- Lines: 300+
- Nodes: 90+
- Subgraphs: 6 phases
- File Size: ~25KB

---

## 💡 Pro Tips

1. **Start with SINGLE_GIANT** to understand overall flow
2. **Read COMPLETE_PIPELINE** for detailed explanations
3. **Use ULTRA_DETAILED** when debugging specific issues
4. **Export to SVG** for presentations (vector, scalable)
5. **Zoom in/out** freely with mermaid.live
6. **Use find (Ctrl+F)** to search for specific nodes

---

**All flowcharts show the CURRENT working implementation - no planned features!**
