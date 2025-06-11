# Simplified vGPU RAG System

## Overview

The vGPU RAG system has been simplified to provide a seamless experience:
- **NO collection selection** - just one pre-loaded knowledge base
- **NO manual uploads** - all PDFs are automatically ingested
- **NO configuration** - everything works out of the box

## How It Works

1. **Single Knowledge Base**: All vGPU documentation is loaded into one collection called `vgpu_knowledge_base`
2. **Automatic Loading**: When the system starts, it automatically ingests ALL PDFs from the `vgpu_docs` folder
3. **Enhanced Validation**: The system still validates vGPU profiles and provides accurate recommendations

## Setup Instructions

### 1. Add Your PDFs

Place ALL your NVIDIA vGPU documentation PDFs in the `vgpu_docs` folder:

```
vgpu_docs/
├── nvidia_vgpu_software_user_guide.pdf
├── vgpu_profile_specifications.pdf
├── a40_datasheet.pdf
├── l40s_specifications.pdf
├── esxi_vgpu_deployment_guide.pdf
└── [any other vGPU PDFs]
```

### 2. Start the System

```bash
# Set your NGC API key
export NGC_API_KEY="nvapi-your-key-here"

# Start everything (cloud mode)
./scripts/start_vgpu_rag.sh --skip-nims
```

### 3. Use the System

Open http://localhost:8090 and start asking questions!

Examples:
- "What vGPU profiles are available for A40 GPUs?"
- "I have 4x L40S GPUs, how many VMs can I run?"
- "Compare vGPU vs passthrough for AI workloads"

## What Changed?

### Before (Complex)
- Multiple collections to manage
- Manual collection selection in UI
- Complex document organization
- Users had to know which collection to search

### After (Simple)
- One collection with everything
- No UI clutter
- Drop PDFs in one folder
- System automatically finds relevant content

## Benefits

1. **Easier Setup**: Just drop PDFs and go
2. **Better User Experience**: No confusion about collections
3. **Same Intelligence**: Still validates profiles and provides enhanced recommendations
4. **Faster Onboarding**: New users can start immediately

## Technical Details

- Collection Name: `vgpu_knowledge_base`
- Bootstrap automatically creates collection and ingests all PDFs
- Enhanced validation still works (profile checking, capacity calculations)
- All PDFs are searched for every query

## Troubleshooting

### PDFs Not Loading?
```bash
# Check if PDFs exist
ls -la vgpu_docs/*.pdf

# Re-run bootstrap
docker compose -f deploy/compose/docker-compose-bootstrap.yaml up
```

### Want to Update PDFs?
1. Add/remove PDFs in `vgpu_docs`
2. Re-run bootstrap to update the knowledge base

### Need to Reset?
```bash
# Stop everything
./scripts/stop_vgpu_rag.sh

# Remove volumes (careful - this deletes all data!)
docker volume rm nvidia-rag_milvus-data

# Start fresh
./scripts/start_vgpu_rag.sh --skip-nims
``` 