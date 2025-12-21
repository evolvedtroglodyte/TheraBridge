# Metaprompt: Vast.ai GPU Auto-Connection for Developer Testing UI

**Date:** 2025-12-20 23:00:49 CST
**Researcher:** NewdlDewdl
**Git Commit:** f4e70f368fb0e6e913c2389311bf037a0af46fc6
**Branch:** main
**Repository:** peerbridge proj

---

## Context

**This UI is for DEVELOPER TESTING ONLY** - not for end users. The goal is to make your development workflow faster by automatically connecting to Vast.ai GPU when you open `localhost:8000` to test the audio transcription pipeline. This will later be integrated into the main TherapyBridge UI.

**Key Insight:** Since this is just for you, we can skip ALL the "user-friendly" features (consent modals, cost warnings, preference management) and go straight for **maximum convenience**.

---

## Goal

**One simple requirement:**

When you run `python ui/server_gpu.py` and open `http://localhost:8000`, the server should **automatically** boot/connect to a Vast.ai GPU instance in the background so you can immediately test audio uploads without clicking anything.

---

## Current State

### ✅ What Already Exists

**Backend:** `ui/server_gpu.py`
- Complete Vast.ai integration
- GPU status endpoint: `/api/gpu-status`
- Instance search: `/api/vast/search`
- Instance boot: `/api/vast/boot`
- Auto-setup via remote script

**Frontend:** `ui/js/gpu-manager.js`
- Manual boot button and modal
- 30-second status polling
- Progress tracking

**Environment:** `.env`
- `VAST_API_KEY` - Your API key
- `VAST_INSTANCE_ID` - Optional instance ID

### 🎯 Current Developer Workflow (Manual)

```
1. python ui/server_gpu.py
2. Open http://localhost:8000
3. Click "Boot Vast.ai GPU" button
4. Wait for modal, select instance
5. Wait 3-5 minutes for boot
6. Finally test audio upload
```

### ❌ What You Want

```
1. python ui/server_gpu.py
2. Open http://localhost:8000
3. GPU auto-boots in background (see progress in header)
4. Continue browsing/working
5. Test audio upload when ready (2-3 minutes)
```

---

## Recommended Implementation: Auto-Boot on Server Startup

**Simplest approach for dev testing:**

### Option 1: Server-Side Auto-Boot (Recommended)

**When to boot:**
- On server startup, if `VAST_INSTANCE_ID` in .env → verify it's running
- If no instance or instance not running → auto-create new one
- Store new instance ID in .env for next restart

**Advantages:**
- Zero frontend changes needed
- GPU ready before you even open browser
- Can track progress via server logs

**Implementation:**

**File:** `ui/server_gpu.py`

**Prompt:**
```
Add auto-boot functionality to server startup for developer testing:

1. Add startup event handler:
   @app.on_event("startup")
   async def startup_auto_boot():
       """Auto-boot Vast.ai instance on server start for dev testing"""

       # Check if we have a cached instance ID
       instance_id = os.getenv("VAST_INSTANCE_ID")

       if instance_id:
           # Check if instance is running
           print(f"[Auto-Boot] Checking cached instance {instance_id}...")
           status = check_vast_connection()

           if status.get("available"):
               print(f"✓ [Auto-Boot] Instance {instance_id} is running")
               return
           else:
               print(f"[Auto-Boot] Cached instance not available, creating new one...")
       else:
           print("[Auto-Boot] No cached instance, creating new one...")

       # Auto-create instance
       try:
           # Search for cheapest available GPU
           search_result = await vast_search_instances(gpu_ram_min=16, max_price=0.5)
           offers = search_result.get("offers", [])

           if not offers:
               print("✗ [Auto-Boot] No GPU instances available")
               return

           # Pick cheapest
           best_offer = min(offers, key=lambda x: x.get("dph_total", 999))
           print(f"[Auto-Boot] Selected {best_offer['gpu_name']} @ ${best_offer['dph_total']}/hr")

           # Boot instance in background
           background_tasks = BackgroundTasks()
           result = await boot_vast_instance(best_offer["id"], background_tasks)

           if result.get("success"):
               new_instance_id = result["instance_id"]
               print(f"✓ [Auto-Boot] Created instance {new_instance_id}")
               print(f"[Auto-Boot] Setup running in background...")

               # Update .env file
               update_env_file("VAST_INSTANCE_ID", new_instance_id)

       except Exception as e:
           print(f"✗ [Auto-Boot] Failed: {e}")
           print("[Auto-Boot] You can manually boot from UI")

2. Add helper to update .env:
   def update_env_file(key: str, value: str):
       """Update or add key=value in .env file"""
       env_path = Path(__file__).parent.parent / ".env"

       if env_path.exists():
           with open(env_path, 'r') as f:
               lines = f.readlines()
       else:
           lines = []

       # Update or append
       updated = False
       for i, line in enumerate(lines):
           if line.startswith(f"{key}="):
               lines[i] = f"{key}={value}\n"
               updated = True
               break

       if not updated:
           lines.append(f"{key}={value}\n")

       with open(env_path, 'w') as f:
           f.writelines(lines)

3. Make startup non-blocking:
   - Wrap auto-boot in try/except (don't crash server if Vast.ai down)
   - Use BackgroundTasks for instance setup
   - Server starts immediately, GPU boots in background

Add this to ui/server_gpu.py
```

**Usage:**
```bash
# Start server
python ui/server_gpu.py

# Output:
# [Auto-Boot] No cached instance, creating new one...
# [Auto-Boot] Selected RTX 3090 @ $0.29/hr
# ✓ [Auto-Boot] Created instance 29040483
# [Auto-Boot] Setup running in background...
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Testing:**
```bash
# First run - creates instance
python ui/server_gpu.py
# Wait 2-3 minutes, instance ready

# Stop server (Ctrl+C)

# Second run - reuses instance
python ui/server_gpu.py
# Instance already running, ready immediately
```

---

### Option 2: Frontend Auto-Boot (Alternative)

**If you prefer frontend control:**

**File:** `ui/js/gpu-manager.js`

**Prompt:**
```
Add auto-boot on page load for developer testing:

1. Modify GPUManager.init() to auto-boot:
   async init() {
       const status = await this.checkGPUStatus();

       // Auto-boot if no GPU available (dev mode)
       if (!status.available) {
           console.log('[Dev] Auto-booting GPU instance...');
           await this.autoBootGPU();
       }

       this.startStatusMonitoring();
       this.setupUI();
   }

2. Add autoBootGPU() method:
   async autoBootGPU() {
       try {
           // Search for instances
           const searchResp = await fetch('/api/vast/search', {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({ gpu_ram_min: 16, max_price: 0.5 })
           });
           const searchData = await searchResp.json();
           const offers = searchData.offers || [];

           if (offers.length === 0) {
               console.warn('[Dev] No GPU instances available');
               return;
           }

           // Pick cheapest
           const bestOffer = offers.reduce((best, offer) =>
               offer.dph_total < best.dph_total ? offer : best
           );

           console.log(`[Dev] Auto-booting ${bestOffer.gpu_name} @ $${bestOffer.dph_total}/hr`);

           // Boot silently
           await this.bootGPUInstance(bestOffer.id);

       } catch (error) {
           console.error('[Dev] Auto-boot failed:', error);
           console.log('[Dev] You can manually boot from UI');
       }
   }

3. Update updateGPUIndicator() to show auto-boot status:
   - Add state for 'auto-booting'
   - Show "Auto-booting GPU..." with spinner
   - Show progress percentage in tooltip

Update ui/js/gpu-manager.js
```

**Advantages:**
- See visual progress in browser
- Can still manually intervene if needed

**Disadvantages:**
- Only boots when you open browser
- Slightly slower than server-side

---

## Recommended Approach: Server-Side Auto-Boot

**For developer testing, go with Option 1 (Server-Side)** because:

1. **Fastest workflow:** GPU starts booting when you run the server, before you even open browser
2. **Simpler code:** Single startup handler, no frontend changes
3. **Better logs:** See progress in terminal where you're watching anyway
4. **Persistent instance:** Stores ID in .env, reuses instance on next run

### Enhanced Server Logging

Add verbose logging for development:

**Prompt:**
```
Add detailed logging to auto-boot process for developer visibility:

1. Log each step with timestamps:
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Checking for existing instance...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Searching for GPUs...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Found 5 offers, selecting cheapest...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Creating instance...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Waiting for SSH...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] Installing dependencies...")
   print(f"[{datetime.now().strftime('%H:%M:%S')}] [Auto-Boot] ✓ GPU ready!")

2. Add progress tracking in background task:
   - Update global status variable
   - Expose via /api/gpu-status
   - Frontend can poll for progress

3. Color-code terminal output (optional):
   from colorama import Fore, Style
   print(f"{Fore.GREEN}✓ [Auto-Boot] GPU ready!{Style.RESET_ALL}")
   print(f"{Fore.YELLOW}⚠ [Auto-Boot] No cached instance{Style.RESET_ALL}")
   print(f"{Fore.RED}✗ [Auto-Boot] Failed{Style.RESET_ALL}")

Add to ui/server_gpu.py
```

### Instance Cleanup on Shutdown

**Prompt:**
```
Add optional instance cleanup on server shutdown:

1. Add shutdown event handler:
   @app.on_event("shutdown")
   async def shutdown_cleanup():
       """Optional: Destroy instance on server shutdown to save costs"""

       # Read config - default to keep instance running
       auto_destroy = os.getenv("AUTO_DESTROY_ON_SHUTDOWN", "false").lower() == "true"

       if not auto_destroy:
           print("[Shutdown] Keeping instance running (set AUTO_DESTROY_ON_SHUTDOWN=true to auto-destroy)")
           return

       instance_id = os.getenv("VAST_INSTANCE_ID")
       if instance_id:
           print(f"[Shutdown] Destroying instance {instance_id}...")
           try:
               subprocess.run(
                   ["vastai", "destroy", "instance", instance_id],
                   check=True,
                   env={**os.environ, "VAST_API_KEY": VAST_API_KEY}
               )
               print(f"✓ [Shutdown] Instance destroyed")
           except Exception as e:
               print(f"✗ [Shutdown] Failed to destroy: {e}")

2. Add to .env.example:
   # Auto-destroy instance when server stops (saves costs, but slower next startup)
   AUTO_DESTROY_ON_SHUTDOWN=false

Add to ui/server_gpu.py
```

---

## Quick Start: Minimal Implementation

**If you just want it working ASAP:**

**Single prompt to add auto-boot:**

```
Add automatic Vast.ai GPU boot on server startup for developer testing:

File: ui/server_gpu.py

Add this startup handler:

@app.on_event("startup")
async def dev_auto_boot():
    """Auto-boot GPU for dev testing - skip if instance already running"""
    instance_id = os.getenv("VAST_INSTANCE_ID")

    # Check existing instance
    if instance_id:
        status = check_vast_connection()
        if status.get("available"):
            print(f"✓ GPU instance {instance_id} already running")
            return

    print("⚡ Auto-booting Vast.ai GPU for testing...")

    try:
        # Search and boot cheapest instance
        result = subprocess.run(
            ["vastai", "search", "offers", "gpu_ram>=16", "-o", "dph+", "--limit", "1", "--raw"],
            capture_output=True, text=True, check=True,
            env={**os.environ, "VAST_API_KEY": VAST_API_KEY}
        )
        offers = json.loads(result.stdout)

        if not offers:
            print("✗ No GPU instances available")
            return

        offer_id = offers[0]["id"]
        gpu_name = offers[0].get("gpu_name", "Unknown")
        price = offers[0].get("dph_total", 0)

        print(f"  Booting {gpu_name} @ ${price}/hr...")

        # Create instance
        result = subprocess.run(
            ["vastai", "create", "instance", str(offer_id),
             "--image", "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
             "--disk", "64", "--ssh"],
            capture_output=True, text=True, check=True,
            env={**os.environ, "VAST_API_KEY": VAST_API_KEY}
        )

        # Extract instance ID
        import re
        match = re.search(r'(\d+)', result.stdout)
        if match:
            new_id = match.group(1)
            print(f"✓ Instance {new_id} created (setup running in background)")

            # Save to .env
            env_path = Path(__file__).parent.parent / ".env"
            with open(env_path, 'a') as f:
                f.write(f"\nVAST_INSTANCE_ID={new_id}\n")

    except Exception as e:
        print(f"✗ Auto-boot failed: {e}")
        print("  You can manually boot from UI")

Add this at the top level of ui/server_gpu.py (after app initialization).
Server will auto-boot GPU on startup. Set VAST_API_KEY in .env first.
```

**Test it:**
```bash
# Set API key if not already set
echo "VAST_API_KEY=your-key-here" >> .env

# Start server
python ui/server_gpu.py

# Expected output:
⚡ Auto-booting Vast.ai GPU for testing...
  Booting RTX 3090 @ $0.29/hr...
✓ Instance 29040483 created (setup running in background)
INFO:     Uvicorn running on http://0.0.0.0:8000

# Open browser after 2-3 minutes, GPU will be ready
```

---

## Additional Dev Helpers

### 1. Environment Variable for Auto-Boot

Add a flag to enable/disable auto-boot:

```bash
# .env
AUTO_BOOT_GPU=true  # Set to false to disable auto-boot
```

Update startup handler:
```python
if os.getenv("AUTO_BOOT_GPU", "true").lower() != "true":
    print("[Auto-Boot] Disabled via AUTO_BOOT_GPU=false")
    return
```

### 2. Quick Shutdown Command

Add a CLI command to destroy instance:

```bash
# scripts/destroy_instance.sh
#!/bin/bash
INSTANCE_ID=$(grep VAST_INSTANCE_ID .env | cut -d= -f2)
vastai destroy instance $INSTANCE_ID
echo "Instance $INSTANCE_ID destroyed"
```

Usage:
```bash
chmod +x scripts/destroy_instance.sh
./scripts/destroy_instance.sh
```

### 3. Status Check Command

Quick terminal command to check GPU status:

```bash
curl http://localhost:8000/api/gpu-status | jq
```

---

## Summary

**For your dev testing workflow, implement:**

1. ✅ **Server-side auto-boot on startup** (Option 1 - minimal prompt above)
2. ✅ **Store instance ID in .env** (auto-reuse on next run)
3. ✅ **Verbose terminal logging** (see progress in console)
4. ⚠️ **Manual shutdown** (don't auto-destroy - costs $0.29/hr, worth keeping for quick tests)

**Total implementation time:** 15-30 minutes

**Result:** Run `python ui/server_gpu.py` and GPU will be ready in 2-3 minutes. No clicking, no modals, no preferences. Just automatic GPU for testing.

---

## Future: Integration into Main UI

When you're ready to integrate into TherapyBridge frontend:

1. Remove auto-boot from test UI
2. Add user-friendly manual boot button to main frontend
3. Add cost warnings and consent
4. Integrate with TherapyBridge authentication
5. Add instance cost tracking for users

But for now, **keep it simple for dev testing** - just auto-boot and go.

---

**Document Version:** 3.0 (Developer Testing Edition)
**Last Updated:** 2025-12-20
**Next Review:** After implementation and testing
