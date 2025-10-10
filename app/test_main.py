# D:\localPyhton\ProgectITBase\ITBase-\main.py (ВРЕМЕННЫЙ КОД ДЛЯ ДИАГНОСТИКИ, ВЕРСИЯ 2)

import sys
import traceback

print("--- STARTING DIAGNOSTIC IMPORT ---")

try:
    print("[STEP 1/5] Importing basic libraries...")
    from fastapi import FastAPI
    print("   [SUCCESS] FastAPI imported.")

    print("[STEP 2/5] Importing router: assets")
    from app.api.endpoints import assets as assets_router
    print("   [SUCCESS] Router 'assets' imported.")

    print("[STEP 3/5] Importing router: tags")
    from app.api.endpoints import tags as tags_router
    print("   [SUCCESS] Router 'tags' imported.")
    
    print("[STEP 4/5] Importing router: dictionaries")
    from app.api.endpoints import dictionaries as dictionaries_router
    print("   [SUCCESS] Router 'dictionaries' imported.")

    print("[STEP 5/5] Creating FastAPI app instance...")
    app = FastAPI()
    print("   [SUCCESS] FastAPI app instance created.")
    
    print("\n--- DIAGNOSTIC IMPORT FINISHED SUCCESSFULLY ---")
    print("--- The problem is likely NOT an import error. ---")

except Exception as e:
    print(f"\n--- !!! IMPORT FAILED AT STEP [ {sys.exc_info()[2].tb_lineno} ] !!! ---")
    print(f"ERROR TYPE: {type(e).__name__}")
    print(f"ERROR DETAILS: {e}")
    print("\n--- TRACEBACK ---")
    traceback.print_exc()
    print("-----------------\n")
    sys.exit(1)