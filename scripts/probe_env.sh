#!/bin/bash

# Environment probing script for the agentic system

echo "Probing system environment..."

# Network connectivity
echo "Checking network connectivity..."
ping -c 1 8.8.8.8 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Network: Connected"
else
    echo "Network: Disconnected"
fi

# DNS resolution
echo "Checking DNS resolution..."
nslookup google.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "DNS: Resolving"
else
    echo "DNS: Not resolving"
fi

# CPU load
echo "Checking CPU load..."
cpu_load=$(uptime | awk -F'load average:' '{ print $2 }' | awk '{ print $1 }' | sed 's/,//')
echo "CPU Load: $cpu_load"

# Memory usage
echo "Checking memory usage..."
mem_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2 }')
echo "Memory Usage: ${mem_usage}%"

# Disk space
echo "Checking disk space..."
disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
echo "Disk Usage: ${disk_usage}%"

# Browser availability
echo "Checking browser availability..."
if command -v chromium &> /dev/null; then
    echo "Browser: Chromium available"
elif command -v firefox &> /dev/null; then
    echo "Browser: Firefox available"
else
    echo "Browser: Not available"
fi

echo "Environment probing complete."