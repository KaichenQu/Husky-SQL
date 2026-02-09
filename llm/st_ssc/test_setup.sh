#!/bin/bash
# Test ST-SSC Setup
# Validates that all Phase 1 components are working correctly

echo "======================================"
echo "ST-SSC Setup Validation"
echo "======================================"
echo ""

cd "$(dirname "$0")"

# Test 1: Verify directory structure
echo "[1/5] Verifying directory structure..."
if [ -d "prompts" ] && [ -d "scripts" ] && [ -d "data" ] && [ -d "outputs" ]; then
    echo "✅ Directory structure OK"
else
    echo "❌ Directory structure incomplete"
    exit 1
fi
echo ""

# Test 2: Verify configuration file
echo "[2/5] Verifying config.yaml..."
if [ -f "config.yaml" ]; then
    python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ config.yaml is valid YAML"
    else
        echo "❌ config.yaml is invalid"
        exit 1
    fi
else
    echo "❌ config.yaml not found"
    exit 1
fi
echo ""

# Test 3: Verify prompt templates
echo "[3/5] Verifying prompt templates..."
if [ -f "prompts/step1_generate_sql.txt" ] && \
   [ -f "prompts/step2_classify_error.txt" ] && \
   [ -f "prompts/step3_fix_one_type.txt" ]; then
    echo "✅ All 3 prompt templates exist"
else
    echo "❌ Prompt templates missing"
    exit 1
fi
echo ""

# Test 4: Test I/O utilities
echo "[4/5] Testing I/O utilities..."
cd scripts
python3 io_utils.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ io_utils.py tests passed"
else
    echo "❌ io_utils.py tests failed"
    exit 1
fi
cd ..
echo ""

# Test 5: Check API key configuration
echo "[5/5] Checking API key configuration..."
API_KEY=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['llm']['api_key'])" 2>/dev/null)
if [ "$API_KEY" = "YOUR_AIML_API_KEY_HERE" ]; then
    echo "⚠️  WARNING: API key not configured yet"
    echo "   Please edit config.yaml and add your AIML API key"
else
    echo "✅ API key is configured"
fi
echo ""

echo "======================================"
echo "Setup validation complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml to add your AIML API key (if not done)"
echo "2. Test API connection: cd scripts && python3 llm_client.py YOUR_KEY"
echo "3. Convert data: python3 scripts/data_converter.py --bird_json ../data/dev.json --db_root ../data/dev_databases/ --output data/bird_dev_test.jsonl --limit 10"
echo "4. Continue with Phase 2: Implement pipeline scripts"
echo ""
