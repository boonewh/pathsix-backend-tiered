"""
One-time script to add lead_source column to leads table
Run this script: python add_lead_source_column.py
"""
from sqlalchemy import text
from app.database import engine

def add_lead_source_column():
    """Add lead_source column to leads table"""
    with engine.connect() as conn:
        try:
            # Add the column
            conn.execute(text(
                "ALTER TABLE leads ADD COLUMN lead_source VARCHAR(50)"
            ))
            print("✓ Added lead_source column to leads table")
            
            # Create index
            conn.execute(text(
                "CREATE INDEX ix_leads_lead_source ON leads (lead_source)"
            ))
            print("✓ Created index on lead_source column")
            
            conn.commit()
            print("✓ Migration completed successfully!")
            
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ Column already exists - no action needed")
            else:
                print(f"✗ Error: {e}")
                raise

if __name__ == "__main__":
    add_lead_source_column()
