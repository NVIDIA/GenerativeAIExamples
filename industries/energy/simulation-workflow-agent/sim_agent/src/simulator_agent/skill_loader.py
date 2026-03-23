# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Skill Loader for AI Planner / NAT Integration
Implements skill discovery, tool auto-discovery, and resource access tools

Based on the OpenSkills directory structure with AI Planner enhancements:
- SKILL.md: Skill instructions and metadata
- config.yaml: Configuration, access control, and agent settings
- scripts/: Implementation with @skill_tool decorated functions
- references/: Documentation and knowledge base files
- assets/: Templates, data files, and resources
"""

import functools
import importlib.util
import inspect
import sys
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
import yaml

try:
    from pydantic import BaseModel, create_model, Field
    from langchain.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseModel = None
    StructuredTool = None


# ============================================================================
# Decorator for Tool Auto-Discovery
# ============================================================================

def skill_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False
):
    """
    Decorator to mark functions for auto-discovery as agent tools
    
    Usage:
        @skill_tool(
            name="create_calendar_event",
            description="Create an iCalendar event from structured data"
        )
        def create_event(summary: str, start_date: str, duration_hours: float = 1.0) -> bytes:
            '''Create a calendar event'''
            # Implementation
            pass
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        return_direct: Whether the tool result should be returned directly to user
    
    The decorator:
    1. Marks the function with metadata for discovery
    2. Preserves the original function signature
    3. Enables automatic Pydantic model generation from type hints
    4. Integrates with LangChain StructuredTool for NAT compatibility
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        func._is_skill_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or (func.__doc__ or "").strip()
        func._tool_return_direct = return_direct
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Copy metadata to wrapper
        wrapper._is_skill_tool = True
        wrapper._tool_name = func._tool_name
        wrapper._tool_description = func._tool_description
        wrapper._tool_return_direct = func._tool_return_direct
        
        return wrapper
    
    return decorator


# ============================================================================
# Skill Discovery and Loading
# ============================================================================

class SkillMetadata:
    """Container for skill metadata from config.yaml and SKILL.md"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.config = self._load_config()
        self.skill_md_metadata, self.skill_md_content = self._load_skill_md()
        # Set name from config, SKILL.md, or fallback to directory name
        self.name = (
            self.config.get('name') or 
            self.skill_md_metadata.get('name') or 
            skill_path.name
        )
        
    def _load_config(self) -> Dict[str, Any]:
        """Load config.yaml"""
        config_path = self.skill_path / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_skill_md(self) -> tuple[Dict[str, Any], str]:
        """Load and parse SKILL.md frontmatter and content"""
        skill_md_path = self.skill_path / "SKILL.md"
        if not skill_md_path.exists():
            return {}, ""
        
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return metadata, body
                except yaml.YAMLError:
                    pass
        
        return {}, content
    
    @property
    def description(self) -> str:
        """Get skill description for LLM-based routing"""
        return (
            self.config.get("description") or 
            self.skill_md_metadata.get("description") or 
            ""
        )
    
    @property
    def skill_type(self) -> str:
        """Get skill type: 'generic' or 'custom'"""
        return self.config.get("skill_type", "generic")
    
    @property
    def user_groups(self) -> List[str]:
        """Get allowed user groups (empty = no restrictions)"""
        return self.config.get("user_group", [])
    
    @property
    def admin_groups(self) -> List[str]:
        """Get admin groups"""
        return self.config.get("admin_group", [])
    
    def check_access(self, user_groups: List[str]) -> bool:
        """
        Check if user has access to this skill
        
        Args:
            user_groups: List of groups the user belongs to
        
        Returns:
            True if user has access, False otherwise
        """
        # No restrictions = everyone has access
        if not self.user_groups and not self.admin_groups:
            return True
        
        # Check if user is in allowed groups
        user_group_set = set(user_groups)
        allowed_groups = set(self.user_groups + self.admin_groups)
        
        return bool(user_group_set & allowed_groups)


class SkillLoader:
    """
    Load and manage skills following OpenSkills + AI Planner architecture
    
    Features:
    - Skill discovery from directory structure
    - Tool auto-discovery with @skill_tool decorator
    - Access control via config.yaml
    - Resource access tools (read_reference, read_asset, list_resources)
    - Pydantic model generation from type hints
    - LangChain StructuredTool integration for NAT
    """
    
    def __init__(
        self, 
        skills_base_path: Path,
        exclude_skills: Optional[List[str]] = None
    ):
        """
        Initialize the skill loader
        
        Args:
            skills_base_path: Base path containing skill directories
            exclude_skills: Optional list of skill names to exclude from discovery
                           (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
        """
        self.skills_base_path = Path(skills_base_path)
        self.exclude_skills = set(exclude_skills if exclude_skills is not None else [])
        self.skills: Dict[str, SkillMetadata] = {}
        self.discover_skills()
    
    def discover_skills(self) -> List[SkillMetadata]:
        """
        Discover all skills in the base path (excluding skills in exclude_skills)
        
        Returns:
            List of discovered skill metadata
        """
        self.skills = {}
        
        if not self.skills_base_path.exists():
            return []
        
        # Find all directories with SKILL.md
        for skill_dir in self.skills_base_path.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                metadata = SkillMetadata(skill_dir)
                # Skip excluded skills - check both skill name and directory name
                skill_name = metadata.name
                dir_name = skill_dir.name
                if skill_name not in self.exclude_skills and dir_name not in self.exclude_skills:
                    self.skills[metadata.name] = metadata
        
        return list(self.skills.values())
    
    def get_skill(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get skill metadata by name"""
        return self.skills.get(skill_name)
    
    def list_skills(
        self, 
        user_groups: Optional[List[str]] = None
    ) -> List[SkillMetadata]:
        """
        List all available skills (with optional access control)
        
        Args:
            user_groups: User's group memberships for access control
        
        Returns:
            List of accessible skills
        """
        if user_groups is None:
            return list(self.skills.values())
        
        return [
            skill for skill in self.skills.values()
            if skill.check_access(user_groups)
        ]
    
    def generate_skills_xml(
        self, 
        user_groups: Optional[List[str]] = None
    ) -> str:
        """
        Generate XML for skill selection (for LLM prompt injection)
        
        This is used by the skill selector to match user queries against
        skill descriptions for routing.
        
        Args:
            user_groups: User's group memberships for access control
        
        Returns:
            XML string with available skills
        """
        skills = self.list_skills(user_groups)
        
        if not skills:
            return "<available_skills></available_skills>"
        
        xml_parts = ["<available_skills>"]
        for skill in sorted(skills, key=lambda s: s.name):
            xml_parts.append(f"""  <skill>
    <name>{skill.name}</name>
    <description>{skill.description}</description>
    <location>{skill.skill_path}</location>
  </skill>""")
        xml_parts.append("</available_skills>")
        
        return "\n".join(xml_parts)
    
    def discover_tools(self, skill_name: str) -> List[Callable]:
        """
        Auto-discover @skill_tool decorated functions from a skill's scripts/
        
        Args:
            skill_name: Name of the skill to discover tools from
        
        Returns:
            List of discovered tool functions
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        
        # Check if auto-discovery is enabled
        if not skill.config.get("generic_settings", {}).get("auto_discover_tools", True):
            return []
        
        scripts_dir = skill.skill_path / "scripts"
        if not scripts_dir.exists():
            return []
        
        tools = []
        
        # Scan all Python files in scripts/
        for py_file in scripts_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            # Import the module
            module_name = f"skill_{skill_name}_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Find all @skill_tool decorated functions
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(obj, '_is_skill_tool') and obj._is_skill_tool:
                        tools.append(obj)
        
        return tools
    
    def get_skill_entry_script(self, skill_name: str) -> Optional[Path]:
        """
        Get the main entry script for a skill
        
        Args:
            skill_name: Name of the skill
        
        Returns:
            Path to the main skill script or None
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        
        scripts_dir = skill.skill_path / "scripts"
        if not scripts_dir.exists():
            return None
        
        # Look for common entry point names
        for candidate in [
            f"{skill_name.replace('-', '_')}_skill.py",
            f"{skill.skill_path.name.replace('-', '_')}_skill.py",
            "skill.py",
            "main.py"
        ]:
            entry_path = scripts_dir / candidate
            if entry_path.exists():
                return entry_path
        
        # Fallback: Return first non-init python file
        for py_file in scripts_dir.glob("*.py"):
            if not py_file.name.startswith("__"):
                return py_file
        
        return None
    
    def execute_skill_subprocess(
        self,
        skill_name: str,
        command: str,
        parameters: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a skill via subprocess with JSON input/output
        
        This method offloads LLM context by executing skills directly
        instead of tool calling within the LLM.
        
        Args:
            skill_name: Name of the skill to execute
            command: Command/function to execute (e.g., 'create_event', 'generate_ideas')
            parameters: Dictionary of parameters to pass to the skill
            timeout: Maximum execution time in seconds
        
        Returns:
            Dict with execution results: success, output, error
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return {
                'success': False,
                'error': f"Skill '{skill_name}' not found"
            }
        
        entry_script = self.get_skill_entry_script(skill_name)
        if not entry_script:
            return {
                'success': False,
                'error': f"No entry script found for skill '{skill_name}'"
            }
        
        # Prepare input data
        input_data = {
            'command': command,
            'parameters': parameters
        }
        
        try:
            # Execute skill script via subprocess
            result = subprocess.run(
                [sys.executable, str(entry_script), '--json'],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(skill.skill_path)
            )
            
            # Parse output
            if result.returncode == 0:
                try:
                    output_data = json.loads(result.stdout)
                    return {
                        'success': True,
                        'output': output_data,
                        'skill_name': skill_name,
                        'command': command
                    }
                except json.JSONDecodeError:
                    # Non-JSON output, return as raw text
                    return {
                        'success': True,
                        'output': result.stdout,
                        'raw_output': True,
                        'skill_name': skill_name,
                        'command': command
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout,
                    'returncode': result.returncode
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Skill execution timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution failed: {str(e)}"
            }
    
    def generate_progressive_prompt(
        self,
        skill_name: str,
        include_tools: bool = True,
        include_resources: bool = True
    ) -> str:
        """
        Generate progressive prompt disclosure for a skill
        
        This method progressively injects more information into the LLM
        context as the skill is activated, following the 5-step process.
        
        Args:
            skill_name: Name of the skill to generate prompt for
            include_tools: Whether to include tool descriptions
            include_resources: Whether to include resource listings
        
        Returns:
            Progressive prompt string with skill details
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return ""
        
        prompt_parts = []
        
        # Add skill instructions (SKILL.md content)
        if skill.skill_md_content:
            prompt_parts.append(f"# {skill.name} - Full Instructions\n")
            prompt_parts.append(skill.skill_md_content)
            prompt_parts.append("\n")
        
        # Add tool descriptions (progressive disclosure)
        if include_tools:
            tools = self.discover_tools(skill_name)
            if tools:
                prompt_parts.append(f"\n## Available Tools ({len(tools)})\n")
                for tool in tools:
                    prompt_parts.append(f"\n### {tool._tool_name}\n")
                    prompt_parts.append(f"{tool._tool_description}\n")
                    
                    # Add function signature
                    sig = inspect.signature(tool)
                    prompt_parts.append(f"\n**Signature:** `{tool._tool_name}{sig}`\n")
                    
                    # Add parameter details
                    type_hints = get_type_hints(tool)
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        param_type = type_hints.get(param_name, Any)
                        param_info = f"- `{param_name}`: {param_type}"
                        if param.default != inspect.Parameter.empty:
                            param_info += f" (default: {param.default})"
                        params.append(param_info)
                    
                    if params:
                        prompt_parts.append("\n**Parameters:**\n")
                        prompt_parts.extend(p + "\n" for p in params)
        
        # Add resource information
        if include_resources:
            refs_dir = skill.skill_path / "references"
            assets_dir = skill.skill_path / "assets"
            
            if refs_dir.exists() or assets_dir.exists():
                prompt_parts.append("\n## Available Resources\n")
                
                if refs_dir.exists():
                    refs = list(refs_dir.glob("*"))
                    if refs:
                        prompt_parts.append(f"\n### References ({len(refs)} files)\n")
                        for ref in refs[:10]:  # Limit to first 10
                            prompt_parts.append(f"- {ref.name}\n")
                
                if assets_dir.exists():
                    assets = list(assets_dir.glob("*"))
                    if assets:
                        prompt_parts.append(f"\n### Assets ({len(assets)} files)\n")
                        for asset in assets[:10]:  # Limit to first 10
                            prompt_parts.append(f"- {asset.name}\n")
        
        return "".join(prompt_parts)
    
    def create_langchain_tools(
        self, 
        skill_name: str,
        skill_instance: Optional[Any] = None
    ) -> List:
        """
        Create LangChain StructuredTool objects from discovered tools
        
        This generates Pydantic models from function type hints and creates
        StructuredTool instances compatible with NAT agents.
        
        Args:
            skill_name: Name of the skill
            skill_instance: Optional skill instance for method binding
        
        Returns:
            List of LangChain StructuredTool objects
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain and pydantic are required for tool creation. "
                "Install with: pip install langchain pydantic"
            )
        
        discovered_tools = self.discover_tools(skill_name)
        langchain_tools = []
        
        for tool_func in discovered_tools:
            # Generate Pydantic model from type hints
            args_schema = self._create_pydantic_model_from_function(tool_func)
            
            # Bind method to instance if provided
            if skill_instance and not inspect.isfunction(tool_func):
                tool_func = getattr(skill_instance, tool_func.__name__, tool_func)
            
            # Create StructuredTool
            langchain_tool = StructuredTool(
                name=tool_func._tool_name,
                description=tool_func._tool_description,
                func=tool_func,
                args_schema=args_schema,
                return_direct=tool_func._tool_return_direct
            )
            
            langchain_tools.append(langchain_tool)
        
        # Add built-in resource access tools if enabled
        skill = self.get_skill(skill_name)
        if skill and skill.config.get("generic_settings", {}).get("enable_resource_tools", True):
            langchain_tools.extend(self._create_resource_tools(skill))
        
        return langchain_tools
    
    def _create_pydantic_model_from_function(self, func: Callable) -> Type[BaseModel]:
        """
        Generate a Pydantic model from function type hints
        
        Args:
            func: Function with type hints
        
        Returns:
            Pydantic BaseModel class for input validation
        """
        type_hints = get_type_hints(func)
        sig = inspect.signature(func)
        
        # Build field definitions
        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = type_hints.get(param_name, Any)
            default = param.default if param.default != inspect.Parameter.empty else ...
            
            # Extract description from docstring if available
            description = f"Parameter: {param_name}"
            
            fields[param_name] = (param_type, Field(default=default, description=description))
        
        # Create dynamic Pydantic model
        model_name = f"{func.__name__.title()}Input"
        return create_model(model_name, **fields)
    
    def _create_resource_tools(self, skill: SkillMetadata) -> List:
        """
        Create built-in resource access tools for a skill
        
        Tools:
        - read_reference: Read documentation from references/
        - read_asset: Read data files from assets/
        - list_resources: List available references and assets
        
        Args:
            skill: Skill metadata
        
        Returns:
            List of resource access StructuredTool objects
        """
        if not LANGCHAIN_AVAILABLE:
            return []
        
        skill_path = skill.skill_path
        
        # read_reference tool
        def read_reference(filename: str) -> str:
            """Read a reference document from the references/ directory"""
            ref_path = skill_path / "references" / filename
            if not ref_path.exists():
                return f"Reference file not found: {filename}"
            try:
                return ref_path.read_text(encoding='utf-8')
            except Exception as e:
                return f"Error reading reference: {str(e)}"
        
        # read_asset tool
        def read_asset(filename: str) -> str:
            """Read an asset file from the assets/ directory"""
            asset_path = skill_path / "assets" / filename
            if not asset_path.exists():
                return f"Asset file not found: {filename}"
            try:
                # For text files
                if asset_path.suffix in ['.txt', '.md', '.json', '.yaml', '.yml', '.csv']:
                    return asset_path.read_text(encoding='utf-8')
                else:
                    return f"Asset file (binary): {filename}, size: {asset_path.stat().st_size} bytes"
            except Exception as e:
                return f"Error reading asset: {str(e)}"
        
        # list_resources tool
        def list_resources() -> str:
            """List all available references and assets"""
            result = []
            
            # List references
            ref_dir = skill_path / "references"
            if ref_dir.exists():
                refs = [f.name for f in ref_dir.iterdir() if f.is_file()]
                if refs:
                    result.append("References:")
                    result.extend(f"  - {ref}" for ref in sorted(refs))
            
            # List assets
            asset_dir = skill_path / "assets"
            if asset_dir.exists():
                assets = [f.name for f in asset_dir.iterdir() if f.is_file()]
                if assets:
                    result.append("\nAssets:")
                    result.extend(f"  - {asset}" for asset in sorted(assets))
            
            return "\n".join(result) if result else "No resources available"
        
        # Create StructuredTools
        tools = []
        
        # read_reference tool
        ReadReferenceInput = create_model(
            "ReadReferenceInput",
            filename=(str, Field(description="Name of the reference file to read"))
        )
        tools.append(StructuredTool(
            name="read_reference",
            description="Read a reference document from the skill's references/ directory",
            func=read_reference,
            args_schema=ReadReferenceInput
        ))
        
        # read_asset tool
        ReadAssetInput = create_model(
            "ReadAssetInput",
            filename=(str, Field(description="Name of the asset file to read"))
        )
        tools.append(StructuredTool(
            name="read_asset",
            description="Read an asset file from the skill's assets/ directory",
            func=read_asset,
            args_schema=ReadAssetInput
        ))
        
        # list_resources tool
        ListResourcesInput = create_model("ListResourcesInput")
        tools.append(StructuredTool(
            name="list_resources",
            description="List all available reference documents and asset files",
            func=list_resources,
            args_schema=ListResourcesInput
        ))
        
        return tools


# ============================================================================
# Convenience Functions
# ============================================================================

def load_skills(
    skills_base_path: str | Path,
    exclude_skills: Optional[List[str]] = None
) -> SkillLoader:
    """
    Convenience function to create a SkillLoader
    
    Args:
        skills_base_path: Path to directory containing skill folders
        exclude_skills: Optional list of skill names to exclude from discovery
                       (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
    
    Returns:
        Initialized SkillLoader instance
    """
    return SkillLoader(Path(skills_base_path), exclude_skills=exclude_skills)


def discover_and_list_skills(
    skills_base_path: str | Path,
    user_groups: Optional[List[str]] = None,
    exclude_skills: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Discover skills and return as list of dictionaries
    
    Args:
        skills_base_path: Path to skills directory
        user_groups: Optional user groups for access control
        exclude_skills: Optional list of skill names to exclude from discovery
                       (e.g., ['nvidia_vlm_skill', 'image_generation_skill'])
    
    Returns:
        List of skill info dictionaries
    """
    loader = SkillLoader(Path(skills_base_path), exclude_skills=exclude_skills)
    skills = loader.list_skills(user_groups)
    print("discovered skills: ", skills)
    return [
        {
            "name": skill.name,
            "description": skill.description,
            "skill_type": skill.skill_type,
            "path": str(skill.skill_path),
            "has_access_control": bool(skill.user_groups or skill.admin_groups)
        }
        for skill in skills
    ]

