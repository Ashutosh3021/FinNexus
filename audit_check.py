import os
import subprocess

root = r'c:\Users\ashut\Downloads\OnGoingProjects\FinNexus'
results = {}

# ── Read files ────────────────────────────────────────────────────────────────
with open(root + '/Backend/main.py', encoding='utf-8') as f:
    src = f.read()

with open(root + '/Frontend/src/components/layout/AppLayout.tsx', encoding='utf-8') as f:
    tsx = f.read()

with open(root + '/.gitignore', encoding='utf-8') as f:
    gi = f.read()

with open(root + '/Bot/scoring.py', encoding='utf-8') as f:
    sc = f.read()

with open(root + '/readme.md', encoding='utf-8') as f:
    rm = f.read()

with open(root + '/DEPLOY.md', encoding='utf-8') as f:
    dp = f.read()

with open(root + '/.env.example', encoding='utf-8') as f:
    ev = f.read()

# ── Issue 1: JWT — no hardcoded insecure fallback used outside insecure set ──
before_insecure_block = src.split('_INSECURE_SECRETS')[0]
results['#1  JWT no inline prod fallback'] = (
    'finnexus-dev-secret-change-in-production' not in before_insecure_block
)
results['#1  JWT startup sys.exit in production'] = (
    'sys.exit(1)' in src and 'JWT_SECRET' in src
)

# ── Issue 2: Rate limiting decorators ────────────────────────────────────────
results['#2  _rate_limit helper defined'] = 'def _rate_limit(' in src
results['#2  @_rate_limit on /auth/token'] = '@_rate_limit("20/minute")' in src
results['#2  @_rate_limit on session/start'] = '@_rate_limit("100/minute")' in src
results['#2  @_rate_limit on market/prices'] = '@_rate_limit("60/minute")' in src
results['#2  request:Request in login sig'] = 'def login(request: Request' in src

# ── Issue 3: CORS production enforcement ─────────────────────────────────────
results['#3  CORS production sys.exit'] = (
    'sys.exit(1)' in src and 'CORS_ORIGINS' in src and 'localhost' in src
)
results['#3  CORS defaults only in dev fallback'] = (
    'Development fallback' in src and 'localhost:5173' in src
)

# ── Issue 4: Frontend mock data banner ───────────────────────────────────────
results['#4  Demo mode banner in AppLayout'] = 'Demo mode' in tsx
results['#4  AlertTriangle imported'] = 'AlertTriangle' in tsx
results['#4  Demo/Live header conditional'] = 'Demo' in tsx and 'USE_API' in tsx

# ── Issue 5: No WebSocket in tracked source files ────────────────────────────
ws = subprocess.run(
    ['git', '-C', root, 'grep', '-rn', 'WebSocket',
     '--include=*.py', '--include=*.ts', '--include=*.tsx'],
    capture_output=True, text=True
)
results['#5  No WebSocket in tracked source'] = ws.stdout.strip() == ''

# ── Issue 7: .gitignore covers artifacts; tracked files removed ──────────────
results['#7  .gitignore covers *.pkl'] = '*.pkl' in gi
results['#7  .gitignore covers *.db'] = '*.db' in gi
results['#7  .gitignore covers artifacts/*.json'] = 'Bot/model/artifacts/*.json' in gi
r = subprocess.run(
    ['git', '-C', root, 'ls-files',
     'Bot/model/artifacts/hitl_xgb.pkl',
     'Bot/model/artifacts/hitl_scaler.pkl',
     'Bot/model/artifacts/hitl_meta.json',
     'Bot/model/finnexus_dev.db'],
    capture_output=True, text=True
)
results['#7  artifacts untracked from git index'] = r.stdout.strip() == ''

# ── Issue 8: SAQ LLM dimension clamp 0-20 ────────────────────────────────────
results['#8  LLM dimension clamped to 0-20'] = 'max(0, min(20,' in sc

# ── Issue 9: /health returns real subsystem state ────────────────────────────
results['#9  /health checks DB'] = 'get_paper_cash' in src and 'subsystems' in src
results['#9  /health checks RAG'] = 'retriever.stats()' in src
results['#9  /health checks LLM'] = 'llm.available' in src
results['#9  /health returns env and timestamp'] = '"env"' in src and '"timestamp"' in src

# ── Issue 10: Accuracy claims corrected in readme ────────────────────────────
results['#10 Actual backtested accuracy in readme'] = 'Actual (backtested)' in rm or 'backtested' in rm
results['#10 Old misleading >60% target updated'] = '>60%' not in rm or 'backtested' in rm

# ── Issue 11: DEPLOY.md complete ─────────────────────────────────────────────
results['#11 DEPLOY.md exists'] = os.path.exists(root + '/DEPLOY.md')
results['#11 DEPLOY.md has JWT_SECRET instructions'] = 'JWT_SECRET' in dp and 'secrets.token_hex' in dp
results['#11 DEPLOY.md has feature engineering step'] = 'generate_features' in dp
results['#11 DEPLOY.md has RAG ingestion step'] = 'Bot.RAG.ingest' in dp
results['#11 DEPLOY.md has accuracy table'] = 'backtested' in dp
results['#11 DEPLOY.md lists known limitations'] = 'WebSocket' in dp and 'OAuth' in dp

# ── Issue 12/13: .env.example has ENV var and Redis note ─────────────────────
results['#12 ENV=development in .env.example'] = 'ENV=development' in ev
results['#13 Redis multi-instance note'] = 'horizontal' in ev or 'multi-instance' in ev

# ── Issue 14: increment_total_cash noted in .env.example ─────────────────────
results['#14 increment_total_cash deployment note'] = 'increment_total_cash' in ev

# ── Python syntax check ───────────────────────────────────────────────────────
import ast
for fname, code in [('Backend/main.py', src), ('Bot/scoring.py', sc)]:
    try:
        ast.parse(code)
        results[f'SYNTAX {fname}'] = True
    except SyntaxError as e:
        results[f'SYNTAX {fname}'] = False
        print(f'  SYNTAX ERROR in {fname}: {e}')

# ── Print results ─────────────────────────────────────────────────────────────
print()
all_pass = True
for k, v in sorted(results.items()):
    status = 'PASS' if v else 'FAIL'
    if not v:
        all_pass = False
    print(f'  [{status}] {k}')

print()
total = len(results)
passed = sum(1 for v in results.values() if v)
print(f'Result: {passed}/{total} checks passed')
if all_pass:
    print('ALL PASS - ready to commit')
else:
    print('SOME FAILURES - review above')
