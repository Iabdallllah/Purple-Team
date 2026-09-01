#!/usr/bin/env python3
"""
Sandbox Escape Test Runner
Runs security tests against sandbox containers.
"""

import argparse
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class SecurityTestRunner:
    """Runs sandbox escape prevention tests"""
    
    def __init__(self, verbose: bool = False, output_file: str = None):
        self.verbose = verbose
        self.output_file = output_file
        self.results: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            }
        }
    
    def run_tests(self, test_file: str = None, test_class: str = None, test_method: str = None) -> Dict[str, Any]:
        """Run pytest with specified filters"""
        test_path = test_file or "packages/sandbox/tests/security/test_sandbox_escape.py"
        
        cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short", "--json-report", "--json-report-file=/tmp/test_results.json"]
        
        if test_class:
            cmd.extend(["-k", test_class])
        if test_method:
            cmd.extend(["-k", test_method])
        
        if self.verbose:
            cmd.append("-s")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return self._parse_results(result)
        except subprocess.TimeoutExpired:
            return {"error": "Tests timed out after 5 minutes"}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_results(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse pytest results"""
        parsed = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        
        # Try to read JSON report
        try:
            with open("/tmp/test_results.json", "r") as f:
                report = json.load(f)
                parsed["report"] = report
        except:
            pass
        
        return parsed
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("SANDBOX ESCAPE TEST SUMMARY")
        print("="*60)
        
        if "report" in results:
            report = results["report"]
            summary = report.get("summary", {})
            print(f"Total tests: {summary.get('total', 0)}")
            print(f"Passed: {summary.get('passed', 0)}")
            print(f"Failed: {summary.get('failed', 0)}")
            print(f"Skipped: {summary.get('skipped', 0)}")
            print(f"Errors: {summary.get('error', 0)}")
            print(f"Duration: {summary.get('duration', 0):.2f}s")
            
            if summary.get('failed', 0) > 0:
                print("\nFAILED TESTS:")
                for test in report.get("tests", []):
                    if test.get("outcome") == "failed":
                        print(f"  - {test.get('name', 'Unknown')}")
                        if "call" in test and "longrepr" in test["call"]:
                            print(f"    {test['call']['longrepr'][:200]}")
        else:
            print("No detailed report available")
            if results.get("stdout"):
                print(results["stdout"][-2000:])
        
        print("="*60)
    
    def save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        if self.output_file:
            with open(self.output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {self.output_file}")


def run_manual_tests() -> Dict[str, bool]:
    """Run manual security checks without pytest"""
    import docker
    import tempfile
    
    results = {}
    client = docker.from_env()
    
    print("Running manual sandbox escape tests...")
    
    # Test 1: Basic container with security options
    print("\n1. Testing container with security options...")
    try:
        container = client.containers.run(
            "alpine:latest",
            command="sleep 60",
            detach=True,
            network_mode="none",
            read_only=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            mem_limit="128m",
            cpu_quota=50000,
            pids_limit=50,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=10m"},
        )
        
        time.sleep(1)
        
        # Test 1a: No network
        result = container.exec_run("ping -c 1 8.8.8.8")
        results["no_network"] = result.exit_code != 0
        print(f"  No network access: {'PASS' if results['no_network'] else 'FAIL'}")
        
        # Test 1b: Read-only filesystem
        result = container.exec_run("touch /test")
        results["readonly_fs"] = result.exit_code != 0
        print(f"  Read-only filesystem: {'PASS' if results['readonly_fs'] else 'FAIL'}")
        
        # Test 1c: No capabilities
        result = container.exec_run("capsh --print")
        output = result.output.decode()
        results["no_caps"] = "Current: =" in output
        print(f"  No capabilities: {'PASS' if results['no_caps'] else 'FAIL'}")
        
        # Test 1d: No new privileges
        result = container.exec_run("cat /proc/self/status | grep NoNewPrivs")
        output = result.output.decode()
        results["no_new_privs"] = "NoNewPrivs:\t1" in output
        print(f"  No new privileges: {'PASS' if results['no_new_privs'] else 'FAIL'}")
        
        # Test 1e: No SUID binaries
        result = container.exec_run("find / -perm -4000 -type f 2>/dev/null")
        results["no_suid"] = result.output.decode().strip() == ""
        print(f"  No SUID binaries: {'PASS' if results['no_suid'] else 'FAIL'}")
        
        # Test 1f: Cannot mount
        result = container.exec_run("mount -t tmpfs tmpfs /mnt")
        results["no_mount"] = result.exit_code != 0
        print(f"  Cannot mount: {'PASS' if results['no_mount'] else 'FAIL'}")
        
        # Test 1g: Cannot access Docker socket
        result = container.exec_run("ls /var/run/docker.sock 2>&1")
        results["no_docker_socket"] = "No such file" in result.output.decode() or result.exit_code != 0
        print(f"  No Docker socket: {'PASS' if results['no_docker_socket'] else 'FAIL'}")
        
        # Test 1h: Memory limit
        result = container.exec_run("cat /sys/fs/cgroup/memory.max")
        output = result.output.decode().strip()
        memory_ok = output != "max" and int(output) <= 134217728
        results["memory_limit"] = memory_ok
        print(f"  Memory limit (128MB): {'PASS' if memory_ok else 'FAIL'} ({output})")
        
        container.remove(force=True)
        print("  Container cleaned up")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results["error"] = str(e)
    
    # Test 2: Negative test - privileged container should have access
    print("\n2. Testing privileged container (control test)...")
    try:
        container = client.containers.run(
            "alpine:latest",
            command="sleep 60",
            detach=True,
            privileged=True,
        )
        time.sleep(1)
        
        # Should be able to mount
        result = container.exec_run("mount -t tmpfs tmpfs /mnt 2>&1")
        privileged_mount = result.exit_code == 0
        print(f"  Privileged can mount: {'PASS' if privileged_mount else 'FAIL'}")
        
        # Should access devices
        result = container.exec_run("ls /dev/sda")
        privileged_dev = result.exit_code == 0
        print(f"  Privileged can access devices: {'PASS' if privileged_dev else 'FAIL'}")
        
        container.remove(force=True)
        
    except Exception as e:
        print(f"  ERROR: {e}")
    
    return results


def print_final_report(results: Dict[str, Any]):
    """Print final test report"""
    print("\n" + "="*60)
    print("SANDBOX ESCAPE TEST REPORT")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    total = len([k for k in results if k != "error"])
    
    print(f"\nTotal checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFAILED CHECKS:")
        for k, v in results.items():
            if v is False:
                print(f"  - {k}")
    
    if "error" in results:
        print(f"\nError: {results['error']}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n✓ ALL SANDBOX ESCAPE PREVENTION TESTS PASSED")
    else:
        print(f"\n✗ {failed} SECURITY CHECKS FAILED - REVIEW REQUIRED")
    
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sandbox Escape Prevention Tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--test-file", help="Test file to run")
    parser.add_argument("--test-class", help="Test class to run")
    parser.add_argument("--test-method", help="Test method to run")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--manual", action="store_true", help="Run manual tests only")
    
    args = parser.parse_args()
    
    if args.manual:
        results = run_manual_tests()
        print_final_report(results)
    else:
        runner = SecurityTestRunner(verbose=args.verbose, output_file=args.output)
        results = runner.run_tests(
            test_file=args.test_file,
            test_class=args.test_class,
            test_method=args.test_method
        )
        runner.print_summary(results)
        runner.save_results(results)