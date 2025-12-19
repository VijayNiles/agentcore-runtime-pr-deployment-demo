#!/usr/bin/env python3
"""Shared utilities for AgentCore Runtime deployment"""

import os
import shutil
import subprocess


def create_deployment_package(prompt_file=None):
    """Create zip file with agent code AND ARM64 dependencies.
    
    Follows AWS's exact recommended approach:
    1. Install ARM64 dependencies to deployment_package/
    2. Set proper POSIX permissions (644 for files, 755 for dirs)
    3. Zip dependencies using native zip command (preserves permissions)
    4. Add agent.py to the zip root
    
    Returns:
        str: Path to the created deployment package zip file
    """
    deployment_dir = "/tmp/deployment_package"
    zip_path = "/tmp/deployment_package.zip"
    
    # Clean up old package and zip
    if os.path.exists(deployment_dir):
        shutil.rmtree(deployment_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    os.makedirs(deployment_dir)
    
    print("📦 Installing dependencies with uv for ARM64...")
    print(f"   Platform: aarch64-manylinux2014")
    print(f"   Python: 3.11")
    print(f"   Target: {deployment_dir}")
    
    # Use uv to install ARM64-compatible dependencies
    result = subprocess.run(
        [
            "uv", "pip", "install",
            "--python-platform", "aarch64-manylinux2014",
            "--python-version", "3.11",
            "--target", deployment_dir,
            "--only-binary=:all:",
            "-r", "agent/requirements.txt"
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": f"{os.environ['HOME']}/.local/bin:{os.environ.get('PATH', '')}"}
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies:")
        print(result.stderr)
        raise Exception(f"Dependency installation failed: {result.stderr}")
    
    print("✓ Dependencies installed")
    
    # Set POSIX permissions as required by AgentCore Runtime
    # 644 (rw-r--r--) for non-executable files
    # 755 (rwxr-xr-x) for directories
    print("🔒 Setting POSIX permissions (644 for files, 755 for directories)...")
    
    for root, dirs, files in os.walk(deployment_dir):
        # Set directory permissions to 755
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.chmod(dir_path, 0o755)
        
        # Set file permissions to 644
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.chmod(file_path, 0o644)
    
    print("✓ Permissions set")
    
    # Create zip from deployment directory using native zip command
    # This preserves POSIX permissions better than Python's zipfile
    print("📦 Creating zip archive with native zip command...")
    
    original_dir = os.getcwd()
    os.chdir(deployment_dir)
    
    # First, zip all the dependencies
    result = subprocess.run(
        ["zip", "-r", zip_path, ".", "-x", "*.pyc", "*__pycache__*"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        os.chdir(original_dir)
        raise Exception(f"Failed to create zip: {result.stderr}")
    
    os.chdir(original_dir)
    print("✓ Dependencies zipped")
    
    # Now add agent.py to the root of the zip
    print("📦 Adding agent.py to zip root...")
    
    # Set permissions on agent.py before adding
    agent_src = "agent/agent.py"
    agent_temp = "/tmp/agent.py"
    shutil.copy(agent_src, agent_temp)
    os.chmod(agent_temp, 0o644)
    
    result = subprocess.run(
        ["zip", zip_path, "agent.py"],
        cwd="/tmp",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to add agent.py to zip: {result.stderr}")
    
    print("✓ agent.py added")
    
    # Add prompt file if provided
    if prompt_file:
        print(f"📦 Adding prompt file to zip root...")
        
        if not os.path.exists(prompt_file):
            raise Exception(f"Prompt file not found: {prompt_file}")
        
        # Copy and rename prompt to system_prompt.txt
        prompt_temp = "/tmp/system_prompt.txt"
        shutil.copy(prompt_file, prompt_temp)
        os.chmod(prompt_temp, 0o644)
        
        result = subprocess.run(
            ["zip", zip_path, "system_prompt.txt"],
            cwd="/tmp",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to add prompt file to zip: {result.stderr}")
        
        print(f"✓ Prompt file added: {os.path.basename(prompt_file)}")
    else:
        print("ℹ️  No prompt file specified, agent will use default prompt")
    
    # Verify size
    size_mb = os.path.getsize(zip_path) / 1024 / 1024
    print(f"✅ Deployment package created: {zip_path}")
    print(f"   Size: {size_mb:.2f} MB")
    
    if size_mb > 250:
        raise Exception(f"Package too large! {size_mb:.2f} MB > 250 MB limit")
    
    return zip_path
