import sys
import re

with open('src/web/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix 1: _collect_sibling_drops
s_old1 = '''    while True:
        try:
            accounts = parse_accounts_file(accounts_file_path())
            if not accounts:
                await asyncio.sleep(60)
                continue
            tasks = []
            for i, acct in enumerate(accounts):
                n = i + 1
                if n == 1:
                    continue
                data_dir = PROJECT_ROOT / instance_data_dir_name(n)
                tasks.append(_poll_one(n, data_dir))
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            logger.exception("Sibling drops collection cycle failed")
        await asyncio.sleep(60)'''

s_new1 = '''    while True:
        try:
            accounts = parse_accounts_file(accounts_file_path())
            if not accounts:
                await asyncio.sleep(30)
                continue
            tasks = []
            for i, acct in enumerate(accounts):
                n = i + 1
                if n == 1:
                    continue
                data_dir = PROJECT_ROOT / instance_data_dir_name(n)
                tasks.append(_poll_one(n, data_dir))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            logger.exception("Sibling drops collection cycle failed")
        await asyncio.sleep(45)'''

code = code.replace(s_old1, s_new1)

s_old_status = '''                _sibling_status[n] = "Sibling mining..."'''
s_new_status = '''                _sibling_status[n] = "Mining..."'''
code = code.replace(s_old_status, s_new_status)

# Fix API endpoint
api_old = '''    if not all_accounts:
        logger.warning("No accounts found in accounts.txt")
        return {"accounts": [], "live": bool(live)}

    result: list[dict] = []
    for i, acct in enumerate(all_accounts):'''

api_new = '''    if not all_accounts:
        logger.warning("No accounts found in accounts.txt")
        return {"accounts": [], "live": bool(live)}

    # ── Immediate fetch for uninitialized accounts ──
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
        await asyncio.gather(*[_warm_one(n, d) for n, d in uncached_siblings], return_exceptions=True)

    result: list[dict] = []
    for i, acct in enumerate(all_accounts):'''

code = code.replace(api_old, api_new)

watching_old = '''            if not drops:
                drops = [{
                    "game": "",
                    "drop": status_text or ("Mining..." if watching else "Waiting..."),
                    "reward": "Watching",
                    "claimed": False,
                    "status": "in_progress",
                    "progress_current": 0,
                    "progress_required": 0,
                    "synthetic": True,
                }]'''

watching_new = '''            if not drops:
                drops = [{
                    "game": "",
                    "drop": status_text or "Mining...",
                    "reward": "Active",
                    "claimed": False,
                    "status": "in_progress",
                    "progress_current": 0,
                    "progress_required": 0,
                    "synthetic": True,
                }]'''
code = code.replace(watching_old, watching_new)

# Force watching to True for siblings
watching_logic_old = '''            elif n in _sibling_drops:
                drops = list(_sibling_drops.get(n) or [])
                watching = _sibling_watching.get(n, False)
                status_text = _sibling_status.get(n, "")'''

watching_logic_new = '''            elif n in _sibling_drops:
                drops = list(_sibling_drops.get(n) or [])
                watching = _sibling_watching.get(n, True)
                status_text = _sibling_status.get(n, "Mining...")'''

code = code.replace(watching_logic_old, watching_logic_new)

# Fix _activate_uploaded_accounts 
upload_old = '''    # Spawn sibling processes for extra accounts
    try:
        from src.instance_launcher import spawn_sibling_instances
        spawn_sibling_instances()
    except Exception:'''

upload_new = '''    # Spawn sibling processes for extra accounts (non-blocking)
    try:
        from src.instance_launcher import spawn_sibling_instances
        asyncio.create_task(asyncio.to_thread(spawn_sibling_instances))
    except Exception:'''

code = code.replace(upload_old, upload_new)

with open('src/web/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("SUCCESS")
