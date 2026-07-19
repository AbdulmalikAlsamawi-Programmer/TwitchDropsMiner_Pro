with open('src/web/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define prefix for warming tracking
target_line = "_sibling_status: dict[int, str] = {}"
replacement = """_sibling_status: dict[int, str] = {}
_sibling_warming_in_progress: set[int] = set()"""

if replacement not in code:
    code = code.replace(target_line, replacement)

# Replace the blocking gather block
blocking_block = """    # ── Immediate fetch for uninitialized accounts ──
    uncached_siblings = []
    if live:
        for i, _ in enumerate(all_accounts):
            n = i + 1
            if n > 1 and n not in _sibling_drops:
                data_dir = PROJECT_ROOT / instance_data_dir_name(n)
                uncached_siblings.append((n, data_dir))

    if uncached_siblings:
        from src.services.owned_drops_service import fetch_owned_drops_live
        sem = asyncio.Semaphore(5)
        async def _warm_one(n, data_dir):
            async with sem:
                try:
                    live_drops = await asyncio.wait_for(fetch_owned_drops_live(data_dir, n), timeout=12)
                    _sibling_drops[n] = live_drops if live_drops else load_drops_history(data_dir)
                except Exception:
                    _sibling_drops[n] = load_drops_history(data_dir)
                _sibling_watching[n] = True
                _sibling_status[n] = "Mining..."
        await asyncio.gather(*[_warm_one(n, d) for n, d in uncached_siblings], return_exceptions=True)"""

non_blocking_block = """    # ── Immediate background fetch for uninitialized accounts ──
    if live:
        from src.services.owned_drops_service import fetch_owned_drops_live
        sem = asyncio.Semaphore(5)

        async def _warm_one(n, data_dir):
            async with sem:
                try:
                    live_drops = await asyncio.wait_for(fetch_owned_drops_live(data_dir, n), timeout=12)
                    _sibling_drops[n] = live_drops if live_drops else load_drops_history(data_dir)
                except Exception:
                    if n not in _sibling_drops:
                        _sibling_drops[n] = load_drops_history(data_dir)
                finally:
                    _sibling_watching[n] = True
                    _sibling_status[n] = "Mining..."
                    _sibling_warming_in_progress.discard(n)

        for i, _ in enumerate(all_accounts):
            n = i + 1
            if n > 1 and n not in _sibling_drops and n not in _sibling_warming_in_progress:
                data_dir = PROJECT_ROOT / instance_data_dir_name(n)
                _sibling_warming_in_progress.add(n)
                asyncio.create_task(_warm_one(n, data_dir))"""

if blocking_block in code:
    code = code.replace(blocking_block, non_blocking_block)
    print("Found and replaced blocking block!")
else:
    print("Warning: Blocking block not found exactly in file!")

with open('src/web/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Finished app.py modifications")
