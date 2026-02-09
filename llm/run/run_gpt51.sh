#!/bin/bash
# Activate conda environment (if exists)
if [ -f "/opt/homebrew/anaconda3/bin/activate" ]; then
    source /opt/homebrew/anaconda3/bin/activate cv
fi

eval_path='./data/dev.json'
dev_path='./output/'
db_root_path='./data/dev_databases/'
use_knowledge='True'
not_use_knowledge='False'
mode='dev'
cot='True'
no_cot='False'  # Fixed typo: was 'Fales'

# AIML API Configuration
AIML_API_KEY='YOUR_AIML_API_KEY_HERE'  # Replace with your actual AIML API key
model='openai/gpt-5-1'  # IMPORTANT: Use forward slash, not dot!

# Output paths for GPT-5.1
data_output_path='./exp_result/gpt51_output/'
data_kg_output_path='./exp_result/gpt51_output_kg/'

# Reasoning effort level (low, medium, high)
reasoning_effort='medium'

# Set test data limit (set to 0 or comment out to process all data)
TEST_LIMIT=0  # Test first 50 entries, set to 0 to process all data

if [ "$TEST_LIMIT" -gt 0 ]; then
    echo "⚠️  Test mode: only processing first ${TEST_LIMIT} entries"
    # Note: aiml_request.py needs to implement --limit parameter support
    # For now, you can manually limit the data in the script by uncommenting the debug lines
    LIMIT_NOTE="(TEST_LIMIT not yet implemented in aiml_request.py)"
else
    LIMIT_NOTE=""
fi

echo '========================================='
echo 'Starting GPT-5.1 (AIML API) Batch Processing'
echo '========================================='
echo "Model: ${model}"
echo "Reasoning effort: ${reasoning_effort}"
echo "Test limit: ${TEST_LIMIT} ${LIMIT_NOTE}"
echo ''

echo 'Generate GPT-5.1 batch WITH knowledge'
python3 -u ./src/aiml_request.py \
    --db_root_path ${db_root_path} \
    --api_key ${AIML_API_KEY} \
    --mode ${mode} \
    --model ${model} \
    --eval_path ${eval_path} \
    --data_output_path ${data_kg_output_path} \
    --use_knowledge ${use_knowledge} \
    --chain_of_thought ${no_cot} \
    --reasoning_effort ${reasoning_effort}

echo ''
echo 'Generate GPT-5.1 batch WITHOUT knowledge'
python3 -u ./src/aiml_request.py \
    --db_root_path ${db_root_path} \
    --api_key ${AIML_API_KEY} \
    --mode ${mode} \
    --model ${model} \
    --eval_path ${eval_path} \
    --data_output_path ${data_output_path} \
    --use_knowledge ${not_use_knowledge} \
    --chain_of_thought ${no_cot} \
    --reasoning_effort ${reasoning_effort}

echo ''
echo '========================================='
echo '✅ GPT-5.1 batch processing complete'
echo '========================================='
echo "Results saved to:"
echo "  - With knowledge: ${data_kg_output_path}"
echo "  - Without knowledge: ${data_output_path}"
