# Jupiter Java — Segmentation Survey Analysis Agent

An AI agent built with [Google ADK](https://google.github.io/adk-docs/) that integrates with Alteryx services (Agentyx and Auto Insights) to perform data analytics tasks. The agent, named **Marveryx**, answers data analytics questions by analyzing datasets within Alteryx Auto Insights using MCP toolsets.

---

## Overview

- **Framework:** Google Agent Development Kit (ADK)
- **Model:** Gemini 2.5 Flash (configurable via `MODEL_NAME` env var)
- **Integrations:** Alteryx Agentyx (workflow MCP), Alteryx Auto Insights (analytics MCP)
- **Planner:** PlanReAct

---

## Prerequisites

- Python 3.11+
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and up to date
- [Google ADK CLI (`adk`)](https://google.github.io/adk-docs/) installed
- A GCP project with billing enabled

---

## Local Setup

### 1. Clone the repository

```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_DIR>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the template and fill in your values:

```bash
cp .env.template .env
```

Key variables (see `.env.template` for the full list and inline examples):

| Variable | Description | Example |
| --- | --- | --- |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `my-gcp-project-****` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-west1` |
| `GOOGLE_CLOUD_STORAGE_BUCKET` | GCS bucket URI for staging | `gs://my-bucket-****` |
| `GOOGLE_API_KEY` | Google API key for Gemini | `AIzaSyXXXXXX****` |
| `AGENTYX_ENABLED` | Enable Agentyx MCP tool | `TRUE` / `FALSE` |
| `AGENTYX_URL` | Agentyx MCP endpoint URL | `https://us1.alteryxcloud.com/agentyx/mcp/v1/` |
| `AGENTYX_TOKEN` | Agentyx bearer token | `eyJ0b2tlbiI6...****` |
| `INSIGHTS_ENABLED` | Enable Auto Insights MCP tool | `TRUE` / `FALSE` |
| `INSIGHTS_URL` | Auto Insights MCP endpoint URL | `https://us1.alteryxcloud.com/auto-insights/mcp` |
| `INSIGHTS_ACCESS_KEY` | Auto Insights access key | `aKPVEacZRw40****` |
| `INSIGHTS_SECRET` | Auto Insights secret | `jrJFNNMElirU****` |
| `AUTO_INSIGHTS_WORKSPACE_URL` | Deep link to Auto Insights workspace | `https://us1.alteryxcloud.com/auto-insights/missions/edit/****` |

> Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Run the agent locally

```bash
adk run agentyx
```

Or launch the ADK web UI:

```bash
adk web
```

---

## Deployment to GCP Agent Engine

### Step 1 — Authenticate and configure gcloud

```bash
gcloud auth login
gcloud components update
gcloud config set project my-gcp-project-****
gcloud auth application-default login
```

### Step 2 — Enable required GCP services

```bash
gcloud services enable container.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com storage.googleapis.com storage-component.googleapis.com storage-api.googleapis.com
```

### Step 3 — Create the staging Cloud Storage bucket

The bucket is used by ADK as a staging area during deployment. Use the same region as your agent.

```bash
gcloud storage buckets create gs://my-agent-staging-**** --project=my-gcp-project-**** --location=us-west1 --uniform-bucket-level-access
```

### Step 4 — Deploy the agent

#### Option A — Create a new agent

```bash
adk deploy agent_engine --project=my-gcp-project-**** --region=us-west1 --staging_bucket=gs://my-agent-staging-**** --display_name="My Agent Display Name" agentyx
```

#### Option B — Update an existing agent

```bash
adk deploy agent_engine --agent_engine_id projects/12345678****/locations/us-west1/reasoningEngines/503236466477262**** --project=my-gcp-project-**** --region=us-west1 --staging_bucket=gs://my-agent-staging-**** --display_name="My Agent Display Name" agentyx
```

> All values shown are examples with masked endings (`****`). Replace them with your actual project, bucket, region, and agent engine ID.

---

## Project Structure

```text
.
├── agentyx/
│   ├── agent.py        # Agent definition and MCP toolset wiring
│   └── prompts.py      # System instructions
├── main.py             # Entry point
├── requirements.txt    # Python dependencies
├── .env.template       # Environment variable template
└── Deployment.txt      # Deployment command reference
```
