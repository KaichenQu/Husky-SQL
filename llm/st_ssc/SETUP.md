# Setup Instructions for GitHub

## Before Pushing to GitHub

### 1. Check Sensitive Files

Make sure `config.yaml` (with your real API key) is NOT committed:

```bash
git status
# Should NOT see config.yaml in the list
```

If you see `config.yaml`, it means `.gitignore` isn't working. Run:

```bash
git rm --cached config.yaml
git add .gitignore
git commit -m "Remove config.yaml from tracking"
```

### 2. Verify .gitignore

```bash
cat .gitignore
# Should contain:
# config.yaml
# outputs/
# data/*.jsonl
```

### 3. Create Your Local Config

```bash
cp config.example.yaml config.yaml
# Edit config.yaml and add your AIML API key
```

### 4. Test Before Pushing

```bash
# Check what will be committed
git status
git diff --staged

# Make sure no sensitive data
grep -r "0d5e7f9ef7774f1d98931e5d6a145981" . --exclude-dir=.git
# Should only find it in config.yaml (which is ignored)
```

## First Time Setup (After Clone)

1. Copy config template:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml` and add your AIML API key

3. Install dependencies (if any):
   ```bash
   pip install requests pyyaml tqdm
   ```

4. Test connection:
   ```bash
   python3 scripts/llm_client.py YOUR_API_KEY
   ```

5. Run pipeline:
   ```bash
   python3 scripts/run_pipeline.py
   ```

## What's Included in Git

✅ Included:
- All `.py` scripts
- Prompt templates (`prompts/`)
- `config.example.yaml` (template)
- `.gitignore`
- Documentation (README.md, etc.)

❌ Excluded (in .gitignore):
- `config.yaml` (has your API key)
- `outputs/` (intermediate results)
- `data/*.jsonl` (processed data)
- `__pycache__/` (Python cache)

## Security Checklist

Before every push:

- [ ] `config.yaml` is in `.gitignore`
- [ ] No API keys in any committed files
- [ ] `git status` doesn't show `config.yaml`
- [ ] `config.example.yaml` has placeholder API key
- [ ] No large output files being committed

## Quick Commands

```bash
# Check for sensitive data
grep -r "api_key.*:" . --include="*.py" --include="*.md" --include="*.txt"

# See what will be committed
git status

# Safe first commit
git add .gitignore config.example.yaml README.md SETUP.md
git commit -m "Initial commit: ST-SSC framework structure"
git push origin main
```
