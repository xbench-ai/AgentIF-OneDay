# AgentIF-OneDay
[🌐 Website](https://xbench.org/agi/agentif) [🤗 Dataset](https://huggingface.co/datasets/xbench/AgentIF-OneDay) [**📄 Paper**](paper/AgentIF_OneDay.pdf) 

**AgentIF-OneDay** is the inaugural benchmark in the AgentIF series by xbench. It evaluates AI Agents on their ability to autonomously complete tasks that represent a full day of human workload.


## Overview

As AI agents evolve from handling minute-level tasks to complex real-world scenarios, AgentIF-OneDay focuses on two key dimensions of scaling:
- **Scaling Context**: Maintaining state, tracking goals, and ensuring consistency over longer execution cycles (from minutes to hours/days).
- **Scaling Domain**: Handling diverse, unstructured tasks across different fields rather than just coding or math.

The benchmark tests whether an agent can deliver stable, high-quality results without human intervention in scenarios involving **Work**, **Life**, and **Study**.

## Categories

Based on analysis of real-world user logs, tasks are categorized into three core types:

### 1. Workflow Execution
*   **Definition**: The user knows the process but the execution is tedious. The agent must precisely follow explicit steps.
*   **Example**: Planning a conference itinerary (e.g., NeurIPS) by verifying venue details, collecting schedules, and generating travel plans.

### 2. Latent Instruction Inference 
*   **Definition**: The user provides examples instead of clear rules. The agent must infer latent intent and constraints from reference files.
*   **Example**: Optimizing a phone plan purchase by analyzing provided carrier schemes and usage history files.

### 3. Iterative Refinement
*   **Definition**: Dynamic requirements that evolve during execution. The agent must handle multi-turn interactions and changing constraints.
*   **Example**: Updating a venue layout (SVG) based on a constraint table (Excel) while maintaining design feasibility.

## Dataset Statistics

- **Total Tasks**: 104 tasks.
- **Formats**: Supports 15+ file formats including PDF, PPT, Excel, Images, and Code.
- **Evaluation**: 767 granular scoring points (positive and negative indicators).
- **Methodology**: LLM-based judging (utilizing models like Gemini 3-pro) combined with automated verification (web retrieval, rendering, multimodal checks).

## Agent Performance

Evaluations of top-tier agents (Manus, Genspark, ChatGPT-Agent) show that leading agents achieve ~62-65% overall success rates on OneDay tasks.

### Domain-Specific Performance

| Rank | Work (Productivity) | Score | Life (Assistant) | Score | Study (Learning) | Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1st** | **ChatGPT-Agent** | **72.18** | **Manus** | **73.40** | **Genspark** | **71.19** |
| **2nd** | Genspark | 71.86 | ChatGPT-Agent | 69.67 | Manus | 64.41 |
| **3rd** | Manus | 70.27 | Genspark | 67.85 | ChatGPT-Agent | 59.29 |

*   **ChatGPT-Agent**: Excels in **Work** scenarios.
*   **Manus**: Excels in **Life** scenarios and Workflow Execution.
*   **Genspark**: Excels in **Study** scenarios and Latent Instruction Inference.

## Reproduction

We provide a comprehensive LLM-as-a-Judge evaluation script to reproduce the results.

👉 **[Go to Evaluation Script](llm_as_judge_script/README.md)**

## Citation

If you find this benchmark useful for your research, please cite our paper:

```bibtex
@misc{chen2026agentifoneday, 
       title={AgentIF-OneDay: A Task-level Instruction-Following Benchmark for General AI Agents in Daily Scenarios}, 
       author={Kaiyuan Chen and Qimin Wu and Taiyu Hou and Tianhao Tang and Xueyu Hu and Yuchen Hou and Bikun Li and Chengming Qian and Guoyin Wang and Haolin Chen and Haotong Tian and Haoye Zhang and Haoyu Bian and Hongbing Pan and Hongkang Zhang and Hongyi Zhou and Jiaqi Cai and Jiewu Rao and Jiyuan Ren and Keduan Huang and Lucia Zhu Huang and Mingyu Yuan and Naixu Guo and Qicheng Tang and Qinyan Zhang and Shuai Chen and Siheng Chen and Ting Ting Li and Xiaoxing Guo and Yaocheng Zuo and Yaoqi Guo and Yinan Wang and Yinzhou Yu and Yize Wang and Yuan Jiang and Yuan Tian and Yuanshuo Zhang and Yuxuan Liu and Yvette Yan Zeng and Zenyu Shan and Zihan Yin and Xiaobo Hu and Yang Liu and Yixin Ren and Yuan Gong}, 
       year={2026}, 
       eprint={2601.20613}, 
       archivePrefix={arXiv}, 
       primaryClass={cs.CL}, 
       url={https://arxiv.org/abs/2601.20613}, 
 }
```
