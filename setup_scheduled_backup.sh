#!/bin/bash
# Setup Fly.io scheduled machine for daily database backups
# This creates a machine that runs once per day

# Disable Git Bash path conversion for this command
export MSYS_NO_PATHCONV=1

flyctl machine run \
  --app pathsixsolutions-backend \
  --name scheduled-backup \
  --schedule daily \
  --restart no \
  --region ord \
  --vm-memory 512 \
  --vm-cpus 1 \
  --vm-cpu-kind shared \
  registry.fly.io/pathsixsolutions-backend:deployment-01KDE3F3HBWWJP1Z7G5PC97T3S \
  /venv/bin/python scripts/run_scheduled_backup.py

echo ""
echo "✅ Scheduled backup machine created!"
echo "It will run daily at 2 AM UTC (9 PM EST / 6 PM PST)"
echo ""
echo "To check scheduled machines:"
echo "  flyctl machine list --app pathsixsolutions-backend"
echo ""
echo "To view backup logs:"
echo "  flyctl logs --app pathsixsolutions-backend"