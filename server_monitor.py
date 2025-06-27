import asyncssh
import logging
from typing import Dict, Optional, Tuple
import os
import re
import asyncio

logger = logging.getLogger(__name__)

# For testing purposes
TEST_MODE = os.getenv('TEST_MODE', '').lower() == 'true'
TEST_CPU = float(os.getenv('TEST_CPU', '0'))
TEST_RAM = float(os.getenv('TEST_RAM', '0'))
TEST_DISK = float(os.getenv('TEST_DISK', '0'))

async def get_server_metrics(
    host: str,
    username: str,
    password: Optional[str] = None,
    ssh_key_path: Optional[str] = None
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Get CPU, RAM, and Disk usage from a remote server using SSH.
    Returns a tuple of (cpu_usage, ram_usage, disk_usage) as percentages.
    """
    # For testing purposes
    if TEST_MODE:
        logger.info(f"Test mode: CPU={TEST_CPU}%, RAM={TEST_RAM}%, Disk={TEST_DISK}%")
        return TEST_CPU, TEST_RAM, TEST_DISK

    try:
        # Prepare SSH connection options
        if ssh_key_path:
            client_keys = [ssh_key_path]
        else:
            client_keys = None

        async with asyncssh.connect(
            host,
            username=username,
            password=password,
            client_keys=client_keys,
            known_hosts=None  # In production, you should handle known_hosts properly
        ) as conn:
            # Get CPU usage using a combination of methods
            try:
                # Method 1: Try mpstat first (most accurate)
                try:
                    # Check if mpstat is available and install if needed
                    install_cmd = "command -v mpstat || (apt-get update && apt-get install -y sysstat) || (yum install -y sysstat) || (apk add --no-cache sysstat)"
                    await conn.run(install_cmd)
                    
                    # Use mpstat to get CPU usage
                    cpu_cmd = "mpstat 1 1 | tail -1 | awk '{print 100-$NF}'"
                    cpu_result = await conn.run(cpu_cmd)
                    cpu_str = cpu_result.stdout.strip()
                    logger.debug(f"Raw CPU usage from mpstat: {cpu_str}")
                    cpu_usage = float(cpu_str)
                except (ValueError, asyncssh.Error) as e:
                    logger.debug(f"mpstat method failed: {str(e)}")
                    # Method 2: Try using /proc/stat
                    try:
                        cpu_cmd = "cat /proc/stat | grep '^cpu '"
                        first_result = await conn.run(cpu_cmd)
                        first_cpu = first_result.stdout.strip().split()[1:]
                        first_idle = float(first_cpu[3]) + float(first_cpu[4])
                        first_total = sum(float(x) for x in first_cpu)
                        
                        # Wait a second and measure again
                        await asyncio.sleep(1)
                        
                        second_result = await conn.run(cpu_cmd)
                        second_cpu = second_result.stdout.strip().split()[1:]
                        second_idle = float(second_cpu[3]) + float(second_cpu[4])
                        second_total = sum(float(x) for x in second_cpu)
                        
                        # Calculate CPU usage
                        idle_diff = second_idle - first_idle
                        total_diff = second_total - first_total
                        cpu_usage = 100 * (1 - idle_diff / total_diff)
                        logger.debug(f"CPU usage from /proc/stat: {cpu_usage}%")
                    except (ValueError, asyncssh.Error) as e:
                        logger.debug(f"/proc/stat method failed: {str(e)}")
                        # Method 3: Try using top as last resort
                        cpu_cmd = "top -bn2 -d 0.1 | grep '^%Cpu' | tail -1 | awk '{print $2+$4+$6}'"
                        cpu_result = await conn.run(cpu_cmd)
                        cpu_str = cpu_result.stdout.strip()
                        logger.debug(f"Raw CPU usage from top: {cpu_str}")
                        cpu_usage = float(cpu_str)

                if cpu_usage is not None:
                    # Ensure CPU usage is between 0 and 100
                    cpu_usage = max(0.0, min(100.0, cpu_usage))
                    logger.debug(f"Final CPU usage: {cpu_usage}%")
            except Exception as e:
                logger.error(f"Error getting CPU metrics: {str(e)}")
                cpu_usage = None

            # Get RAM usage
            try:
                ram_cmd = """free | grep Mem | awk '{print $3/$2 * 100.0}'"""
                ram_result = await conn.run(ram_cmd)
                ram_usage = float(ram_result.stdout.strip())
                logger.debug(f"RAM usage: {ram_usage}%")
            except (ValueError, asyncssh.Error) as e:
                logger.error(f"Error getting RAM metrics: {str(e)}")
                ram_usage = None

            # Get Disk usage
            try:
                disk_cmd = """df -h / | tail -1 | awk '{print $5}' | sed 's/%//'"""
                disk_result = await conn.run(disk_cmd)
                disk_usage = float(disk_result.stdout.strip())
                logger.debug(f"Disk usage: {disk_usage}%")
            except (ValueError, asyncssh.Error) as e:
                logger.error(f"Error getting disk metrics: {str(e)}")
                disk_usage = None

            return cpu_usage, ram_usage, disk_usage

    except asyncssh.Error as e:
        logger.error(f"Error getting metrics from {host}: {str(e)}")
        return None, None, None 