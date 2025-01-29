# Study on LLMs for FL and APR

## Introduction
This project explores the effectiveness of closed-source large language models (LLMs) in **Fault Localization (FL)** and **Automated Program Repair (APR)** tasks. It investigates how LLMs can assist in software debugging and repair.

## Dependencies
Ensure your environment meets the following requirements:
- **Java 8** (required for `Defects4J`)
- **Java 11** (required for `ConDefects`)

## Datasets
The study utilizes the following datasets:
- [**Defects4J 2.1.0**](https://github.com/rjust/defects4j/tree/v2.1.0)
- [**ConDefects**](https://github.com/appmlk/ConDefects)

Make sure the datasets are correctly set up and configured in the respective scripts (`main-d4j.py` and `main-cond.py`).

## Usage
1. **Configure Datasets**  
   - Set up the dataset paths and parameters in `main-d4j.py` and `main-cond.py`.

2. **Set Up LLM API**  
   - Configure the LLM API information in `util/llm/LLMManager.py`.

3. **Verify Java Version and Run the Scripts**  
   - Run `main-d4j.py` (requires Java 8):
     ```bash
     python main-d4j.py
     ```
   - Run `main-cond.py` (requires Java 11):
     ```bash
     python main-cond.py
     ```

## Experimental Results
The experiment results are stored in the `output` directory. For each bug, the following files are generated:
- `bug_id.bug_info.json`: Stores bug information
- `bug_id.prompts.json`: Logs prompts used for querying the LLM
- `bug_id.prompts.txt`: Contains the human-readable format of the prompts
- `bug_id.query_results.json`: Stores the LLM's response results
- `bug_id.check_results_fl.json`: Stores the FL task execution results
- `bug_id.check_results_apr.json`: Stores the APR task execution results
