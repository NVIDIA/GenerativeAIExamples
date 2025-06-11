# NVIDIA vGPU Documentation

This directory contains PDF documentation that powers the enhanced vGPU RAG system.

## How to Use

1. **Download NVIDIA vGPU PDFs** from:
   - NVIDIA Developer Documentation
   - NVIDIA Enterprise Support Portal  
   - NVIDIA vGPU Software Documentation

2. **Place PDFs in appropriate folders**:
   - `baseline/` - Core vGPU user guides, installation manuals
   - `hypervisor/` - ESXi, VMware, Citrix deployment guides
   - `cost_efficiency/` - Cost optimization and sizing guides
   - `performance/` - Performance benchmarks and testing
   - `gpu_specific/a40/` - NVIDIA A40 specific documentation
   - `gpu_specific/l40s/` - NVIDIA L40S specific documentation
   - `gpu_specific/l4/` - NVIDIA L4 specific documentation
   - `sizing/` - VM sizing and capacity planning guides

3. **Restart the system** - The bootstrap process will automatically:
   - Create collections in Milvus
   - Ingest all PDFs 
   - Enable enhanced vGPU recommendations

## Example PDFs to Add

- `baseline/nvidia_vgpu_software_user_guide.pdf`
- `hypervisor/vgpu_vmware_deployment_guide.pdf`
- `gpu_specific/a40/a40_vgpu_profile_specifications.pdf`
- `cost_efficiency/vgpu_sizing_best_practices.pdf`

The more official NVIDIA documentation you add, the better your vGPU recommendations will be! 