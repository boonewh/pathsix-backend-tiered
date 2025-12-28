#!/usr/bin/env python
"""
Quick development setup script for PathSix CRM Backend.

This script will:
1. Check Python version
2. Initialize the database
3. Optionally create an admin user
4. Provide next steps

Usage:
    python setup_dev.py
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Ensure Python 3.10+ is being used."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required!")
        print("   Please upgrade your Python installation.")
        sys.exit(1)

    print("✅ Python version is compatible")


def check_env_file():
    """Check if .env file exists."""
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("   Please copy .env.example to .env:")
        print("   Windows: copy .env.example .env")
        print("   macOS/Linux: cp .env.example .env")
        sys.exit(1)

    print("✅ .env file exists")


def initialize_database():
    """Initialize the database tables."""
    print("\n🔧 Initializing database...")

    try:
        # Set up path to find app module
        sys.path.insert(0, os.path.dirname(__file__))

        from app.database import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        print("   Check your DATABASE_URL in .env")
        return False


def create_storage_directory():
    """Create storage directory for local file uploads."""
    from app.config import STORAGE_VENDOR, STORAGE_ROOT

    if STORAGE_VENDOR == "local":
        storage_path = Path(STORAGE_ROOT)
        if not storage_path.exists():
            storage_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created storage directory: {STORAGE_ROOT}")
        else:
            print(f"✅ Storage directory exists: {STORAGE_ROOT}")


def offer_admin_creation():
    """Ask user if they want to create an admin user."""
    print("\n👤 Admin User Setup")
    response = input("Would you like to create an admin user now? (y/n): ").strip().lower()

    if response == 'y':
        print("\nRunning admin creation script...")
        print("(You can also run 'python create_tenant_admin.py' later)")
        print("\n" + "="*60)

        try:
            # Import and run the admin creation script
            import subprocess
            result = subprocess.run([sys.executable, "create_tenant_admin.py"])
            if result.returncode == 0:
                print("="*60)
                print("✅ Admin user created successfully")
            else:
                print("="*60)
                print("⚠️  Admin user creation was cancelled or failed")
        except Exception as e:
            print(f"❌ Failed to run admin creation script: {str(e)}")
            print("   You can run it manually: python create_tenant_admin.py")
    else:
        print("⏭️  Skipped admin user creation")
        print("   You can create one later: python create_tenant_admin.py")


def print_next_steps():
    """Print instructions for running the server."""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("\n1. Activate your virtual environment (if not already active):")
    print("   Windows: .\\venv\\Scripts\\activate")
    print("   macOS/Linux: source venv/bin/activate")

    print("\n2. Start the development server:")
    print("   hypercorn asgi:app --bind 0.0.0.0:8000 --reload")

    print("\n3. Test the API:")
    print("   Open http://localhost:8000/health in your browser")
    print("   Or run: curl http://localhost:8000/health")

    print("\n4. Connect your frontend:")
    print("   Make sure FRONTEND_URL in .env matches your frontend dev server")
    print("   Default: http://localhost:5173")

    print("\n📚 For more information, see SETUP_DEV.md")
    print("="*60 + "\n")


def main():
    """Run the setup process."""
    print("="*60)
    print("PathSix CRM Backend - Development Setup")
    print("="*60 + "\n")

    # Step 1: Check Python version
    check_python_version()

    # Step 2: Check for .env file
    check_env_file()

    # Step 3: Initialize database
    db_success = initialize_database()

    if not db_success:
        print("\n⚠️  Setup incomplete due to database error")
        print("   Fix the error above and run this script again")
        sys.exit(1)

    # Step 4: Create storage directory
    create_storage_directory()

    # Step 5: Offer to create admin user
    offer_admin_creation()

    # Step 6: Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
